import re
from typing import Dict, Any, Optional
import PyPDF2
import pandas as pd
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class BankFormat:
    """Bank format identifiers and patterns."""
    
    # Nigerian Banks
    GTB = "gtbank"
    ACCESS = "access_bank"
    ZENITH = "zenith_bank"
    UBA = "uba"
    FIRST_BANK = "first_bank"
    STANBIC = "stanbic_ibtc"
    FIDELITY = "fidelity_bank"
    UNION = "union_bank"
    UNKNOWN = "unknown"


# Bank detection patterns
BANK_PATTERNS = {
    BankFormat.GTB: [
        r"guaranty\s*trust\s*bank",
        r"gtbank",
        r"gtb",
    ],
    BankFormat.ACCESS: [
        r"access\s*bank",
        r"accessbank",
    ],
    BankFormat.ZENITH: [
        r"zenith\s*bank",
        r"zenithbank",
    ],
    BankFormat.UBA: [
        r"united\s*bank\s*for\s*africa",
        r"uba",
    ],
    BankFormat.FIRST_BANK: [
        r"first\s*bank",
        r"firstbank",
    ],
    BankFormat.STANBIC: [
        r"stanbic\s*ibtc",
        r"stanbicibtc",
    ],
    BankFormat.FIDELITY: [
        r"fidelity\s*bank",
        r"fidelitybank",
    ],
    BankFormat.UNION: [
        r"union\s*bank",
        r"unionbank",
    ],
}


def detect_bank_format(file_path: str) -> Dict[str, Any]:
    """
    Detect bank and format from file content using heuristics.
    
    Args:
        file_path: Path to the statement file
    
    Returns:
        Dictionary with bank, format, confidence, and metadata
    """
    file_ext = Path(file_path).suffix.lower()
    
    try:
        if file_ext == '.pdf':
            return _detect_from_pdf(file_path)
        elif file_ext in ['.xls', '.xlsx']:
            return _detect_from_excel(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return {
                "bank": BankFormat.UNKNOWN,
                "format": "unknown",
                "confidence": 0.0,
                "file_type": file_ext
            }
    except Exception as e:
        logger.error(f"Error detecting bank format: {str(e)}", exc_info=True)
        return {
            "bank": BankFormat.UNKNOWN,
            "format": "unknown",
            "confidence": 0.0,
            "error": str(e)
        }


def _detect_from_pdf(file_path: str) -> Dict[str, Any]:
    """Detect bank format from PDF content."""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            
            # Extract text from first 2 pages
            text = ""
            for page_num in range(min(2, len(reader.pages))):
                page_text = reader.pages[page_num].extract_text() or ""
                text += page_text.lower()
            
            # Detect bank
            bank, confidence = _match_bank_patterns(text)
            
            # Detect format characteristics
            has_table = bool(re.search(r'date.*description.*amount', text, re.IGNORECASE))
            has_debit_credit = bool(re.search(r'debit.*credit', text, re.IGNORECASE))
            
            format_type = "tabular" if has_table else "narrative"
            
            return {
                "bank": bank,
                "format": format_type,
                "confidence": confidence,
                "file_type": "pdf",
                "pages": len(reader.pages),
                "has_table": has_table,
                "has_debit_credit": has_debit_credit,
            }
    except Exception as e:
        logger.error(f"Error reading PDF: {str(e)}")
        raise


def _detect_from_excel(file_path: str) -> Dict[str, Any]:
    """Detect bank format from Excel content."""
    try:
        # Read first few rows
        df = pd.read_excel(file_path, nrows=10)
        
        # Convert to text for pattern matching
        text = " ".join(df.astype(str).values.flatten()).lower()
        
        # Also check column names
        columns = " ".join(df.columns.astype(str)).lower()
        text += " " + columns
        
        # Detect bank
        bank, confidence = _match_bank_patterns(text)
        
        # Detect format characteristics
        has_date_column = any('date' in col.lower() for col in df.columns)
        has_amount_column = any('amount' in col.lower() or 'debit' in col.lower() or 'credit' in col.lower() for col in df.columns)
        
        return {
            "bank": bank,
            "format": "spreadsheet",
            "confidence": confidence,
            "file_type": "excel",
            "sheets": 1,  # Could be enhanced to count sheets
            "rows": len(df),
            "columns": len(df.columns),
            "has_date_column": has_date_column,
            "has_amount_column": has_amount_column,
        }
    except Exception as e:
        logger.error(f"Error reading Excel: {str(e)}")
        raise


def _match_bank_patterns(text: str) -> tuple[str, float]:
    """
    Match text against bank patterns.
    
    Returns:
        Tuple of (bank_name, confidence_score)
    """
    best_match = BankFormat.UNKNOWN
    best_score = 0.0
    
    for bank, patterns in BANK_PATTERNS.items():
        score = 0.0
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * 0.3  # Each match increases confidence
        
        if score > best_score:
            best_score = score
            best_match = bank
    
    # Normalize confidence to 0-1 range
    confidence = min(1.0, best_score)
    
    return best_match, confidence


def get_bank_config(bank: str) -> Dict[str, Any]:
    """
    Get configuration for specific bank format.
    
    Args:
        bank: Bank identifier
    
    Returns:
        Configuration dictionary with parsing rules
    """
    configs = {
        BankFormat.GTB: {
            "name": "GTBank (Guaranty Trust Bank)",
            "date_formats": ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"],
            "currency": "NGN",
            "decimal_separator": ".",
            "thousand_separator": ",",
        },
        BankFormat.ACCESS: {
            "name": "Access Bank",
            "date_formats": ["%d/%m/%Y", "%d-%b-%Y"],
            "currency": "NGN",
            "decimal_separator": ".",
            "thousand_separator": ",",
        },
        BankFormat.ZENITH: {
            "name": "Zenith Bank",
            "date_formats": ["%d/%m/%Y", "%d-%m-%Y"],
            "currency": "NGN",
            "decimal_separator": ".",
            "thousand_separator": ",",
        },
        BankFormat.UBA: {
            "name": "United Bank for Africa (UBA)",
            "date_formats": ["%d/%m/%Y", "%Y-%m-%d"],
            "currency": "NGN",
            "decimal_separator": ".",
            "thousand_separator": ",",
        },
    }
    
    return configs.get(bank, {
        "name": "Unknown Bank",
        "date_formats": ["%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y"],
        "currency": "NGN",
        "decimal_separator": ".",
        "thousand_separator": ",",
    })
