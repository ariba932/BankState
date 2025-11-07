import PyPDF2
import re
from typing import Dict, Any, List
from datetime import datetime
from models.transaction import Transaction
from utils.bank_format_detector import detect_bank_format, get_bank_config, BankFormat
from utils.exceptions import ExtractionError
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_pdf_statement(file_path: str) -> Dict[str, Any]:
    """
    Extract transaction data from PDF bank statements.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        Dictionary with transactions and metadata
    
    Raises:
        ExtractionError: If extraction fails
    """
    try:
        # Detect bank format
        format_info = detect_bank_format(file_path)
        logger.info(f"Detected bank: {format_info['bank']} (confidence: {format_info.get('confidence', 0):.2f})")
        
        # Extract text from PDF
        raw_text = _extract_text_from_pdf(file_path)
        
        # Extract account information
        account_info = _extract_account_info(raw_text, format_info['bank'])
        
        # Extract transactions based on bank format
        transactions = _extract_transactions(raw_text, format_info['bank'])
        
        logger.info(f"Extracted {len(transactions)} transactions from PDF")
        
        return {
            "transactions": transactions,
            "account_info": account_info,
            "format_info": format_info,
            "status": "success",
            "transaction_count": len(transactions),
        }
    
    except Exception as e:
        logger.error(f"PDF extraction failed: {str(e)}", exc_info=True)
        raise ExtractionError(
            f"Failed to extract data from PDF: {str(e)}",
            details={"file_path": file_path}
        )


def _extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from PDF."""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text_pages = []
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_pages.append(page_text)
                else:
                    logger.warning(f"Page {page_num + 1} has no extractable text")
            
            return "\n".join(text_pages)
    
    except Exception as e:
        raise ExtractionError(f"Failed to read PDF: {str(e)}")


def _extract_account_info(text: str, bank: str) -> Dict[str, Any]:
    """Extract account information from statement text."""
    account_info = {
        "account_number": None,
        "account_name": None,
        "bank_name": bank,
        "statement_period": None,
        "opening_balance": None,
        "closing_balance": None,
    }
    
    # Extract account number (various patterns)
    account_patterns = [
        r"account\s*(?:no|number)[:\s]+(\d{10})",
        r"acct\s*(?:no|number)[:\s]+(\d{10})",
        r"account[:\s]+(\d{10})",
    ]
    for pattern in account_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            account_info["account_number"] = match.group(1)
            break
    
    # Extract account name
    name_patterns = [
        r"account\s*name[:\s]+([A-Z][A-Z\s\.]+)",
        r"customer\s*name[:\s]+([A-Z][A-Z\s\.]+)",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            account_info["account_name"] = match.group(1).strip()
            break
    
    # Extract statement period
    period_patterns = [
        r"period[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*to\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        r"from[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*to\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
    ]
    for pattern in period_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            account_info["statement_period"] = {
                "from": match.group(1),
                "to": match.group(2)
            }
            break
    
    # Extract opening/closing balances
    balance_patterns = [
        r"opening\s*balance[:\s]+(?:NGN|₦)?\s*([\d,]+\.?\d*)",
        r"closing\s*balance[:\s]+(?:NGN|₦)?\s*([\d,]+\.?\d*)",
    ]
    
    opening_match = re.search(balance_patterns[0], text, re.IGNORECASE)
    if opening_match:
        account_info["opening_balance"] = _parse_amount(opening_match.group(1))
    
    closing_match = re.search(balance_patterns[1], text, re.IGNORECASE)
    if closing_match:
        account_info["closing_balance"] = _parse_amount(closing_match.group(1))
    
    return account_info


def _extract_transactions(text: str, bank: str) -> List[Dict[str, Any]]:
    """Extract transactions from statement text."""
    transactions = []
    bank_config = get_bank_config(bank)
    
    # Split text into lines
    lines = text.split('\n')
    
    # Transaction patterns for Nigerian banks
    # Pattern: Date | Description | Debit | Credit | Balance
    transaction_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(.+?)\s+([\d,]+\.?\d*)\s*([\d,]+\.?\d*)?\s+([\d,]+\.?\d*)'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Try to match transaction pattern
        match = re.search(transaction_pattern, line)
        if match:
            try:
                date_str = match.group(1)
                description = match.group(2).strip()
                amount1 = match.group(3)
                amount2 = match.group(4) if match.group(4) else None
                balance = match.group(5)
                
                # Determine debit/credit
                # If we have two amounts, first is debit, second is credit
                if amount2:
                    debit = _parse_amount(amount1)
                    credit = _parse_amount(amount2)
                else:
                    # Single amount - determine by keywords or balance change
                    amount = _parse_amount(amount1)
                    if any(keyword in description.lower() for keyword in ['credit', 'deposit', 'transfer in']):
                        debit = 0.0
                        credit = amount
                    else:
                        debit = amount
                        credit = 0.0
                
                # Parse date
                parsed_date = _parse_date(date_str, bank_config['date_formats'])
                
                transaction = {
                    "date": parsed_date.isoformat() if parsed_date else date_str,
                    "description": description,
                    "debit": debit,
                    "credit": credit,
                    "amount": credit if credit > 0 else -debit,
                    "balance": _parse_amount(balance),
                    "type": "credit" if credit > 0 else "debit",
                    "currency": bank_config['currency'],
                }
                
                transactions.append(transaction)
            
            except Exception as e:
                logger.warning(f"Failed to parse transaction line: {line[:50]}... Error: {str(e)}")
                continue
    
    return transactions


def _parse_amount(amount_str: str) -> float:
    """Parse amount string to float."""
    try:
        # Remove currency symbols and whitespace
        clean_str = re.sub(r'[₦NGN\s]', '', amount_str)
        # Remove thousand separators
        clean_str = clean_str.replace(',', '')
        return float(clean_str)
    except (ValueError, AttributeError):
        return 0.0


def _parse_date(date_str: str, date_formats: List[str]) -> datetime:
    """Parse date string using multiple formats."""
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # If no format matches, try common variations
    try:
        # Try replacing separators
        for separator in ['-', '/']:
            modified_date = date_str.replace(separator, '/')
            return datetime.strptime(modified_date, '%d/%m/%Y')
    except ValueError:
        pass
    
    logger.warning(f"Could not parse date: {date_str}")
    return None
