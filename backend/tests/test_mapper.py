import pytest
from mappers.camt053_mapper import map_to_camt053
from lxml import etree
import json


def test_map_to_camt053_xml():
    """Test mapping transactions to ISO 20022 camt.053 XML format."""
    transactions = [
        {
            "date": "2025-11-01",
            "description": "Test Transaction 1",
            "debit": 1000.00,
            "credit": 0.00,
            "amount": -1000.00,
            "balance": 5000.00,
            "type": "debit",
            "currency": "NGN",
            "reference": "TXN001"
        },
        {
            "date": "2025-11-02",
            "description": "Test Transaction 2",
            "debit": 0.00,
            "credit": 2000.00,
            "amount": 2000.00,
            "balance": 7000.00,
            "type": "credit",
            "currency": "NGN",
            "reference": "TXN002"
        }
    ]
    
    account_info = {
        "account_number": "0123456789",
        "account_name": "TEST ACCOUNT",
        "opening_balance": 6000.00,
        "closing_balance": 7000.00
    }
    
    xml_output = map_to_camt053(transactions, account_info, output_format="xml")
    
    # Parse XML to verify structure
    root = etree.fromstring(xml_output.encode('utf-8'))
    
    # Verify namespace
    assert NAMESPACE in root.tag or "iso:std:iso:20022" in xml_output
    
    # Verify basic structure
    assert len(xml_output) > 0
    assert "BkToCstmrStmt" in xml_output
    assert "Stmt" in xml_output
    assert "Ntry" in xml_output
    
    # Verify transaction count (should have 2 entries)
    assert xml_output.count("<Ntry") == 2 or xml_output.count("Ntry>") >= 2


def test_map_to_camt053_json():
    """Test mapping transactions to ISO 20022 camt.053 JSON format."""
    transactions = [
        {
            "date": "2025-11-01",
            "description": "Test Transaction",
            "debit": 500.00,
            "credit": 0.00,
            "amount": -500.00,
            "balance": 4500.00,
            "type": "debit",
            "currency": "NGN"
        }
    ]
    
    account_info = {
        "account_number": "0123456789",
        "account_name": "TEST ACCOUNT"
    }
    
    json_output = map_to_camt053(transactions, account_info, output_format="json")
    
    # Parse JSON to verify structure
    data = json.loads(json_output)
    
    assert "Document" in data
    assert "BkToCstmrStmt" in data["Document"]
    assert "Stmt" in data["Document"]["BkToCstmrStmt"]
    
    stmt = data["Document"]["BkToCstmrStmt"]["Stmt"]
    assert "Acct" in stmt
    assert "Ntry" in stmt
    assert len(stmt["Ntry"]) == 1


def test_map_empty_transactions():
    """Test mapping with no transactions."""
    transactions = []
    account_info = {"account_number": "0123456789"}
    
    xml_output = map_to_camt053(transactions, account_info, output_format="xml")
    
    assert len(xml_output) > 0
    assert "BkToCstmrStmt" in xml_output
    # Should have no entries
    assert "<Ntry" not in xml_output or xml_output.count("<Ntry") == 0


def test_map_invalid_format():
    """Test mapping with invalid output format."""
    transactions = [{"date": "2025-11-01", "amount": 100}]
    
    with pytest.raises(Exception):  # Should raise MappingError
        map_to_camt053(transactions, output_format="invalid")


# Define namespace for test
NAMESPACE = "urn:iso:std:iso:20022:tech:xsd:camt.053.001.02"
