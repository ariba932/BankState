import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
import re
from models.transaction import Transaction
from utils.bank_format_detector import detect_bank_format, get_bank_config
from utils.exceptions import ExtractionError
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_excel_statement(file_path: str) -> Dict[str, Any]:
    """
    Extract transaction data from Excel bank statements.
    
    Args:
        file_path: Path to Excel file
    
    Returns:
        Dictionary with transactions and metadata
    
    Raises:
        ExtractionError: If extraction fails
    """
    try:
        # Detect bank format
        format_info = detect_bank_format(file_path)
        logger.info(f"Detected bank: {format_info['bank']} (confidence: {format_info.get('confidence', 0):.2f})")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Clean and normalize column names
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        # Extract account information from header rows or metadata
        account_info = _extract_account_info_from_df(df, format_info['bank'])
        
        # Find the transaction data starting row
        transaction_start_row = _find_transaction_start(df)
        
        # Extract transactions
        transactions = _extract_transactions_from_df(
            df.iloc[transaction_start_row:],
            format_info['bank']
        )
        
        logger.info(f"Extracted {len(transactions)} transactions from Excel")
        
        return {
            "transactions": transactions,
            "account_info": account_info,
            "format_info": format_info,
            "status": "success",
            "transaction_count": len(transactions),
        }
    
    except Exception as e:
        logger.error(f"Excel extraction failed: {str(e)}", exc_info=True)
        raise ExtractionError(
            f"Failed to extract data from Excel: {str(e)}",
            details={"file_path": file_path}
        )


def _find_transaction_start(df: pd.DataFrame) -> int:
    """Find the row where transaction data starts."""
    # Look for common header keywords
    header_keywords = ['date', 'transaction', 'description', 'amount', 'debit', 'credit', 'balance']
    
    for idx, row in df.iterrows():
        row_str = ' '.join(str(val).lower() for val in row.values if pd.notna(val))
        if any(keyword in row_str for keyword in header_keywords):
            return idx + 1  # Return next row (data starts after header)
    
    return 0  # If no header found, assume data starts at beginning


def _extract_account_info_from_df(df: pd.DataFrame, bank: str) -> Dict[str, Any]:
    """Extract account information from DataFrame."""
    account_info = {
        "account_number": None,
        "account_name": None,
        "bank_name": bank,
        "statement_period": None,
        "opening_balance": None,
        "closing_balance": None,
    }
    
    # Check first few rows for account info
    header_text = ""
    for idx in range(min(10, len(df))):
        row_text = ' '.join(str(val) for val in df.iloc[idx].values if pd.notna(val))
        header_text += row_text + " "
    
    # Extract account number
    account_match = re.search(r'account\s*(?:no|number)?[:\s]*(\d{10})', header_text, re.IGNORECASE)
    if account_match:
        account_info["account_number"] = account_match.group(1)
    
    # Extract account name
    name_match = re.search(r'account\s*name[:\s]+([A-Z][A-Z\s\.]+)', header_text, re.IGNORECASE)
    if name_match:
        account_info["account_name"] = name_match.group(1).strip()
    
    return account_info


def _extract_transactions_from_df(df: pd.DataFrame, bank: str) -> List[Dict[str, Any]]:
    """Extract transactions from DataFrame."""
    transactions = []
    bank_config = get_bank_config(bank)
    
    # Identify column mappings
    column_map = _map_columns(df.columns)
    
    if not column_map.get('date'):
        logger.warning("No date column found, attempting fuzzy extraction")
        return []
    
    # Process each row as a transaction
    for idx, row in df.iterrows():
        try:
            # Skip rows with no date
            date_val = row[column_map['date']]
            if pd.isna(date_val):
                continue
            
            # Parse date
            if isinstance(date_val, datetime):
                parsed_date = date_val
            elif isinstance(date_val, str):
                parsed_date = _parse_date(date_val, bank_config['date_formats'])
            else:
                continue
            
            # Extract description
            description = ""
            if column_map.get('description'):
                description = str(row[column_map['description']]) if pd.notna(row[column_map['description']]) else ""
            
            # Extract amounts
            debit = 0.0
            credit = 0.0
            balance = 0.0
            
            if column_map.get('debit'):
                debit_val = row[column_map['debit']]
                debit = float(debit_val) if pd.notna(debit_val) and debit_val != '' else 0.0
            
            if column_map.get('credit'):
                credit_val = row[column_map['credit']]
                credit = float(credit_val) if pd.notna(credit_val) and credit_val != '' else 0.0
            
            if column_map.get('balance'):
                balance_val = row[column_map['balance']]
                balance = float(balance_val) if pd.notna(balance_val) and balance_val != '' else 0.0
            
            # If no debit/credit columns, check for single amount column
            if debit == 0.0 and credit == 0.0 and column_map.get('amount'):
                amount_val = row[column_map['amount']]
                amount = float(amount_val) if pd.notna(amount_val) else 0.0
                
                # Determine type based on sign or keywords
                if amount < 0:
                    debit = abs(amount)
                elif amount > 0:
                    credit = amount
                else:
                    # Check description for hints
                    if any(kw in description.lower() for kw in ['credit', 'deposit', 'transfer in']):
                        credit = abs(amount)
                    else:
                        debit = abs(amount)
            
            # Build transaction
            transaction = {
                "date": parsed_date.isoformat() if parsed_date else str(date_val),
                "description": description,
                "debit": debit,
                "credit": credit,
                "amount": credit if credit > 0 else -debit,
                "balance": balance,
                "type": "credit" if credit > 0 else "debit",
                "currency": bank_config['currency'],
            }
            
            transactions.append(transaction)
        
        except Exception as e:
            logger.warning(f"Failed to parse row {idx}: {str(e)}")
            continue
    
    return transactions


def _map_columns(columns: List[str]) -> Dict[str, str]:
    """Map DataFrame columns to standard fields."""
    column_map = {}
    
    # Normalize column names
    columns_lower = [str(col).lower().strip() for col in columns]
    
    # Date column patterns
    date_patterns = ['date', 'trans date', 'transaction date', 'value date', 'posting date']
    for pattern in date_patterns:
        for col in columns_lower:
            if pattern in col:
                column_map['date'] = columns[columns_lower.index(col)]
                break
        if 'date' in column_map:
            break
    
    # Description column patterns
    desc_patterns = ['description', 'narration', 'details', 'particulars', 'remarks']
    for pattern in desc_patterns:
        for col in columns_lower:
            if pattern in col:
                column_map['description'] = columns[columns_lower.index(col)]
                break
        if 'description' in column_map:
            break
    
    # Amount columns
    for col in columns_lower:
        if 'debit' in col and 'debit' not in column_map:
            column_map['debit'] = columns[columns_lower.index(col)]
        if 'credit' in col and 'credit' not in column_map:
            column_map['credit'] = columns[columns_lower.index(col)]
        if 'balance' in col and 'balance' not in column_map:
            column_map['balance'] = columns[columns_lower.index(col)]
        if 'amount' in col and 'amount' not in column_map and 'debit' not in column_map and 'credit' not in column_map:
            column_map['amount'] = columns[columns_lower.index(col)]
    
    return column_map


def _parse_date(date_str: str, date_formats: List[str]) -> datetime:
    """Parse date string using multiple formats."""
    for fmt in date_formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except (ValueError, TypeError):
            continue
    
    # Try pandas date parser as fallback
    try:
        return pd.to_datetime(date_str)
    except Exception:
        logger.warning(f"Could not parse date: {date_str}")
        return None
