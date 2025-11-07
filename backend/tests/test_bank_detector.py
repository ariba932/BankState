import pytest
from utils.bank_format_detector import (
    detect_bank_format,
    get_bank_config,
    BankFormat,
    _match_bank_patterns
)
import tempfile
import os


def test_match_bank_patterns():
    """Test bank pattern matching."""
    text = "guaranty trust bank statement"
    bank, confidence = _match_bank_patterns(text)
    assert bank == BankFormat.GTB
    assert confidence > 0
    
    text2 = "access bank nigeria"
    bank2, confidence2 = _match_bank_patterns(text2)
    assert bank2 == BankFormat.ACCESS
    
    text3 = "unknown bank name"
    bank3, confidence3 = _match_bank_patterns(text3)
    assert bank3 == BankFormat.UNKNOWN


def test_get_bank_config():
    """Test getting bank configuration."""
    config = get_bank_config(BankFormat.GTB)
    assert "name" in config
    assert "date_formats" in config
    assert "currency" in config
    assert config["currency"] == "NGN"
    
    # Test unknown bank
    unknown_config = get_bank_config("unknown_bank")
    assert unknown_config["name"] == "Unknown Bank"


def test_detect_bank_format_unsupported():
    """Test detection with unsupported file type."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"Some text content")
        temp_file = f.name
    
    try:
        result = detect_bank_format(temp_file)
        assert result["bank"] == BankFormat.UNKNOWN
        assert result["format"] == "unknown"
    finally:
        os.unlink(temp_file)


def test_bank_format_constants():
    """Test BankFormat constants."""
    assert BankFormat.GTB == "gtbank"
    assert BankFormat.ACCESS == "access_bank"
    assert BankFormat.ZENITH == "zenith_bank"
    assert BankFormat.UBA == "uba"
    assert BankFormat.UNKNOWN == "unknown"
