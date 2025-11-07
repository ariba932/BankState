from lxml import etree
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.exceptions import MappingError
from utils.logger import get_logger

logger = get_logger(__name__)

# ISO 20022 namespace
NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"
NS_MAP = {None: NAMESPACE}


def map_to_camt053(
    transactions: List[Dict[str, Any]],
    account_info: Dict[str, Any] = None,
    output_format: str = "xml"
) -> str:
    """
    Map extracted transaction data to ISO 20022 camt.053 format.
    
    Args:
        transactions: List of transaction dictionaries
        account_info: Account information dictionary
        output_format: Output format ('xml' or 'json')
    
    Returns:
        ISO 20022 camt.053 formatted string (XML or JSON)
    
    Raises:
        MappingError: If mapping fails
    """
    try:
        if output_format == "xml":
            return _generate_camt053_xml(transactions, account_info)
        elif output_format == "json":
            return _generate_camt053_json(transactions, account_info)
        else:
            raise MappingError(f"Unsupported output format: {output_format}")
    
    except Exception as e:
        logger.error(f"Mapping to camt.053 failed: {str(e)}", exc_info=True)
        raise MappingError(
            f"Failed to map transactions to ISO 20022 format: {str(e)}",
            details={"transaction_count": len(transactions)}
        )


def _generate_camt053_xml(
    transactions: List[Dict[str, Any]],
    account_info: Dict[str, Any] = None
) -> str:
    """Generate ISO 20022 camt.053 XML."""
    
    # Root element: Document
    root = etree.Element(
        f"{{{NAMESPACE}}}Document",
        nsmap=NS_MAP
    )
    
    # BkToCstmrStmt (Bank To Customer Statement)
    bk_to_cstmr_stmt = etree.SubElement(root, f"{{{NAMESPACE}}}BkToCstmrStmt")
    
    # Group Header
    grp_hdr = etree.SubElement(bk_to_cstmr_stmt, f"{{{NAMESPACE}}}GrpHdr")
    
    msg_id = etree.SubElement(grp_hdr, f"{{{NAMESPACE}}}MsgId")
    msg_id.text = f"STMT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    cre_dt_tm = etree.SubElement(grp_hdr, f"{{{NAMESPACE}}}CreDtTm")
    cre_dt_tm.text = datetime.utcnow().isoformat()
    
    # Statement
    stmt = etree.SubElement(bk_to_cstmr_stmt, f"{{{NAMESPACE}}}Stmt")
    
    # Statement ID
    stmt_id = etree.SubElement(stmt, f"{{{NAMESPACE}}}Id")
    stmt_id.text = f"STMT-{datetime.utcnow().strftime('%Y%m%d')}"
    
    # Creation Date Time
    cre_dt_tm_stmt = etree.SubElement(stmt, f"{{{NAMESPACE}}}CreDtTm")
    cre_dt_tm_stmt.text = datetime.utcnow().isoformat()
    
    # Account
    if account_info:
        acct = etree.SubElement(stmt, f"{{{NAMESPACE}}}Acct")
        
        # Account ID
        acct_id = etree.SubElement(acct, f"{{{NAMESPACE}}}Id")
        
        if account_info.get('account_number'):
            othr = etree.SubElement(acct_id, f"{{{NAMESPACE}}}Othr")
            othr_id = etree.SubElement(othr, f"{{{NAMESPACE}}}Id")
            othr_id.text = account_info['account_number']
        
        # Account Currency
        ccy = etree.SubElement(acct, f"{{{NAMESPACE}}}Ccy")
        ccy.text = "NGN"  # Nigerian Naira
        
        # Account Owner Name
        if account_info.get('account_name'):
            ownr = etree.SubElement(acct, f"{{{NAMESPACE}}}Ownr")
            nm = etree.SubElement(ownr, f"{{{NAMESPACE}}}Nm")
            nm.text = account_info['account_name']
    
    # Balance - Opening
    if account_info and account_info.get('opening_balance') is not None:
        bal = etree.SubElement(stmt, f"{{{NAMESPACE}}}Bal")
        
        tp = etree.SubElement(bal, f"{{{NAMESPACE}}}Tp")
        cd_or_prtry = etree.SubElement(tp, f"{{{NAMESPACE}}}CdOrPrtry")
        cd = etree.SubElement(cd_or_prtry, f"{{{NAMESPACE}}}Cd")
        cd.text = "OPBD"  # Opening Booked
        
        amt = etree.SubElement(bal, f"{{{NAMESPACE}}}Amt")
        amt.set("Ccy", "NGN")
        amt.text = f"{account_info['opening_balance']:.2f}"
        
        cdt_dbt_ind = etree.SubElement(bal, f"{{{NAMESPACE}}}CdtDbtInd")
        cdt_dbt_ind.text = "CRDT" if account_info['opening_balance'] >= 0 else "DBIT"
        
        dt = etree.SubElement(bal, f"{{{NAMESPACE}}}Dt")
        dt_val = etree.SubElement(dt, f"{{{NAMESPACE}}}Dt")
        if account_info.get('statement_period') and account_info['statement_period'].get('from'):
            dt_val.text = account_info['statement_period']['from']
        else:
            dt_val.text = datetime.utcnow().date().isoformat()
    
    # Entries (Transactions)
    for idx, tx in enumerate(transactions, 1):
        ntry = etree.SubElement(stmt, f"{{{NAMESPACE}}}Ntry")
        
        # Amount
        amt = etree.SubElement(ntry, f"{{{NAMESPACE}}}Amt")
        amt.set("Ccy", tx.get('currency', 'NGN'))
        tx_amount = abs(tx.get('amount', 0))
        amt.text = f"{tx_amount:.2f}"
        
        # Credit/Debit Indicator
        cdt_dbt_ind = etree.SubElement(ntry, f"{{{NAMESPACE}}}CdtDbtInd")
        cdt_dbt_ind.text = "CRDT" if tx.get('type') == 'credit' else "DBIT"
        
        # Status (Booked)
        sts = etree.SubElement(ntry, f"{{{NAMESPACE}}}Sts")
        sts.text = "BOOK"
        
        # Booking Date
        book_dt = etree.SubElement(ntry, f"{{{NAMESPACE}}}BookgDt")
        dt = etree.SubElement(book_dt, f"{{{NAMESPACE}}}Dt")
        try:
            tx_date = datetime.fromisoformat(tx['date']).date().isoformat()
        except (ValueError, TypeError):
            tx_date = datetime.utcnow().date().isoformat()
        dt.text = tx_date
        
        # Value Date
        val_dt = etree.SubElement(ntry, f"{{{NAMESPACE}}}ValDt")
        dt_val = etree.SubElement(val_dt, f"{{{NAMESPACE}}}Dt")
        dt_val.text = tx_date
        
        # Bank Transaction Code (simplified)
        bank_tx_cd = etree.SubElement(ntry, f"{{{NAMESPACE}}}BkTxCd")
        domn = etree.SubElement(bank_tx_cd, f"{{{NAMESPACE}}}Domn")
        cd = etree.SubElement(domn, f"{{{NAMESPACE}}}Cd")
        cd.text = "PMNT"  # Payment
        
        # Entry Details
        ntry_dtls = etree.SubElement(ntry, f"{{{NAMESPACE}}}NtryDtls")
        tx_dtls = etree.SubElement(ntry_dtls, f"{{{NAMESPACE}}}TxDtls")
        
        # References
        refs = etree.SubElement(tx_dtls, f"{{{NAMESPACE}}}Refs")
        
        # Entry reference
        entry_ref = etree.SubElement(refs, f"{{{NAMESPACE}}}AcctSvcrRef")
        entry_ref.text = tx.get('reference', f"TXN-{idx}")
        
        # Additional Transaction Info (Description)
        addtl_tx_inf = etree.SubElement(tx_dtls, f"{{{NAMESPACE}}}AddtlTxInf")
        addtl_tx_inf.text = tx.get('description', 'No description')
    
    # Balance - Closing
    if account_info and account_info.get('closing_balance') is not None:
        bal = etree.SubElement(stmt, f"{{{NAMESPACE}}}Bal")
        
        tp = etree.SubElement(bal, f"{{{NAMESPACE}}}Tp")
        cd_or_prtry = etree.SubElement(tp, f"{{{NAMESPACE}}}CdOrPrtry")
        cd = etree.SubElement(cd_or_prtry, f"{{{NAMESPACE}}}Cd")
        cd.text = "CLBD"  # Closing Booked
        
        amt = etree.SubElement(bal, f"{{{NAMESPACE}}}Amt")
        amt.set("Ccy", "NGN")
        amt.text = f"{account_info['closing_balance']:.2f}"
        
        cdt_dbt_ind = etree.SubElement(bal, f"{{{NAMESPACE}}}CdtDbtInd")
        cdt_dbt_ind.text = "CRDT" if account_info['closing_balance'] >= 0 else "DBIT"
        
        dt = etree.SubElement(bal, f"{{{NAMESPACE}}}Dt")
        dt_val = etree.SubElement(dt, f"{{{NAMESPACE}}}Dt")
        if account_info.get('statement_period') and account_info['statement_period'].get('to'):
            dt_val.text = account_info['statement_period']['to']
        else:
            dt_val.text = datetime.utcnow().date().isoformat()
    
    return etree.tostring(root, pretty_print=True, encoding="unicode", xml_declaration=True)


def _generate_camt053_json(
    transactions: List[Dict[str, Any]],
    account_info: Dict[str, Any] = None
) -> str:
    """Generate ISO 20022 camt.053 JSON representation."""
    import json
    
    document = {
        "Document": {
            "BkToCstmrStmt": {
                "GrpHdr": {
                    "MsgId": f"STMT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "CreDtTm": datetime.utcnow().isoformat()
                },
                "Stmt": {
                    "Id": f"STMT-{datetime.utcnow().strftime('%Y%m%d')}",
                    "CreDtTm": datetime.utcnow().isoformat(),
                }
            }
        }
    }
    
    stmt = document["Document"]["BkToCstmrStmt"]["Stmt"]
    
    # Account
    if account_info:
        stmt["Acct"] = {
            "Id": {"Othr": {"Id": account_info.get('account_number', 'UNKNOWN')}},
            "Ccy": "NGN"
        }
        if account_info.get('account_name'):
            stmt["Acct"]["Ownr"] = {"Nm": account_info['account_name']}
    
    # Balances
    stmt["Bal"] = []
    
    if account_info and account_info.get('opening_balance') is not None:
        stmt["Bal"].append({
            "Tp": {"CdOrPrtry": {"Cd": "OPBD"}},
            "Amt": {"Ccy": "NGN", "Value": account_info['opening_balance']},
            "CdtDbtInd": "CRDT" if account_info['opening_balance'] >= 0 else "DBIT"
        })
    
    # Transactions
    stmt["Ntry"] = []
    for idx, tx in enumerate(transactions, 1):
        entry = {
            "Amt": {"Ccy": tx.get('currency', 'NGN'), "Value": abs(tx.get('amount', 0))},
            "CdtDbtInd": "CRDT" if tx.get('type') == 'credit' else "DBIT",
            "Sts": "BOOK",
            "BookgDt": {"Dt": tx.get('date', datetime.utcnow().date().isoformat())[:10]},
            "ValDt": {"Dt": tx.get('date', datetime.utcnow().date().isoformat())[:10]},
            "NtryDtls": {
                "TxDtls": {
                    "Refs": {"AcctSvcrRef": tx.get('reference', f"TXN-{idx}")},
                    "AddtlTxInf": tx.get('description', 'No description')
                }
            }
        }
        stmt["Ntry"].append(entry)
    
    if account_info and account_info.get('closing_balance') is not None:
        stmt["Bal"].append({
            "Tp": {"CdOrPrtry": {"Cd": "CLBD"}},
            "Amt": {"Ccy": "NGN", "Value": account_info['closing_balance']},
            "CdtDbtInd": "CRDT" if account_info['closing_balance'] >= 0 else "DBIT"
        })
    
    return json.dumps(document, indent=2)
