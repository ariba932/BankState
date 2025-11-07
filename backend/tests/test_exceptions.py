import pytest
from utils.exceptions import (
    BankStateException,
    ValidationError,
    FileProcessingError,
    ExtractionError,
    MappingError,
    IntegrationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError
)


def test_base_exception():
    """Test base BankStateException."""
    exc = BankStateException("Test error", status_code=500, details={"key": "value"})
    assert str(exc) == "Test error"
    assert exc.status_code == 500
    assert exc.details == {"key": "value"}


def test_validation_error():
    """Test ValidationError."""
    exc = ValidationError("Invalid input", details={"field": "email"})
    assert exc.status_code == 400
    assert exc.message == "Invalid input"
    assert exc.details["field"] == "email"


def test_file_processing_error():
    """Test FileProcessingError."""
    exc = FileProcessingError("Failed to process file")
    assert exc.status_code == 422


def test_extraction_error():
    """Test ExtractionError."""
    exc = ExtractionError("Failed to extract data")
    assert exc.status_code == 422


def test_mapping_error():
    """Test MappingError."""
    exc = MappingError("Failed to map data")
    assert exc.status_code == 422


def test_integration_error():
    """Test IntegrationError."""
    exc = IntegrationError("External API failed")
    assert exc.status_code == 502


def test_authentication_error():
    """Test AuthenticationError."""
    exc = AuthenticationError()
    assert exc.status_code == 401
    assert exc.message == "Authentication failed"
    
    exc2 = AuthenticationError("Invalid token")
    assert exc2.message == "Invalid token"


def test_authorization_error():
    """Test AuthorizationError."""
    exc = AuthorizationError()
    assert exc.status_code == 403
    assert exc.message == "Access denied"


def test_not_found_error():
    """Test NotFoundError."""
    exc = NotFoundError("Resource not found")
    assert exc.status_code == 404


def test_rate_limit_error():
    """Test RateLimitError."""
    exc = RateLimitError()
    assert exc.status_code == 429
    assert exc.message == "Rate limit exceeded"
