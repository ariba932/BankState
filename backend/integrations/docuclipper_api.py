import requests
from typing import Dict, Any, List
from utils.exceptions import IntegrationError
from utils.logger import get_logger
from config import get_settings

logger = get_logger(__name__)
settings = get_settings()


def extract_with_docuclipper(file_path: str, api_key: str = None) -> Dict[str, Any]:
    """
    Extract bank statement data using DocuClipper API.
    
    Args:
        file_path: Path to the file to extract
        api_key: DocuClipper API key (optional, uses config if not provided)
    
    Returns:
        Dictionary with extracted transactions and metadata
    
    Raises:
        IntegrationError: If API call fails
    """
    api_key = api_key or settings.docuclipper_api_key
    
    if not api_key:
        raise IntegrationError(
            "DocuClipper API key not configured",
            details={"config_key": "DOCUCLIPPER_API_KEY"}
        )
    
    url = f"{settings.docuclipper_api_url}/bank-statements/extract"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    try:
        logger.info(f"Calling DocuClipper API for file: {file_path}")
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                url,
                headers=headers,
                files=files,
                timeout=settings.docuclipper_timeout
            )
        
        response.raise_for_status()
        result = response.json()
        
        logger.info(f"DocuClipper API call successful. Extracted {len(result.get('transactions', []))} transactions")
        
        # Map DocuClipper response to our format
        return _map_docuclipper_response(result)
    
    except requests.exceptions.Timeout:
        raise IntegrationError(
            "DocuClipper API request timed out",
            details={"timeout": settings.docuclipper_timeout}
        )
    
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_detail = e.response.text
        
        logger.error(f"DocuClipper API error: {status_code} - {error_detail}")
        
        raise IntegrationError(
            f"DocuClipper API returned error: {status_code}",
            details={
                "status_code": status_code,
                "error": error_detail
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error calling DocuClipper API: {str(e)}", exc_info=True)
        raise IntegrationError(
            f"Failed to call DocuClipper API: {str(e)}",
            details={"error_type": type(e).__name__}
        )


def _map_docuclipper_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map DocuClipper API response to our standard format.
    
    DocuClipper returns data in CSV/Excel/QBO format, which needs
    to be standardized to our transaction format.
    """
    transactions = []
    
    # DocuClipper typically returns transactions in a 'data' or 'transactions' field
    raw_transactions = response.get('transactions', response.get('data', []))
    
    for tx in raw_transactions:
        # Map DocuClipper fields to our standard format
        transaction = {
            "date": tx.get('date', tx.get('transaction_date', '')),
            "description": tx.get('description', tx.get('narration', tx.get('details', ''))),
            "debit": float(tx.get('debit', tx.get('withdrawal', 0))),
            "credit": float(tx.get('credit', tx.get('deposit', 0))),
            "balance": float(tx.get('balance', 0)),
            "reference": tx.get('reference', tx.get('ref', '')),
            "currency": tx.get('currency', 'NGN'),
        }
        
        # Calculate amount and type
        if transaction['credit'] > 0:
            transaction['amount'] = transaction['credit']
            transaction['type'] = 'credit'
        else:
            transaction['amount'] = -transaction['debit']
            transaction['type'] = 'debit'
        
        transactions.append(transaction)
    
    # Extract account information
    account_info = {
        "account_number": response.get('account_number', response.get('account', {}).get('number')),
        "account_name": response.get('account_name', response.get('account', {}).get('name')),
        "bank_name": response.get('bank_name', response.get('bank')),
        "statement_period": response.get('period', {
            "from": response.get('start_date'),
            "to": response.get('end_date')
        }),
        "opening_balance": float(response.get('opening_balance', 0)),
        "closing_balance": float(response.get('closing_balance', 0)),
    }
    
    return {
        "transactions": transactions,
        "account_info": account_info,
        "format_info": {
            "bank": account_info.get('bank_name', 'unknown'),
            "source": "docuclipper",
            "confidence": 0.99  # DocuClipper has 99.6% accuracy
        },
        "status": "success",
        "transaction_count": len(transactions),
    }
