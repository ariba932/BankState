import pytest
from fastapi.testclient import TestClient
from main import app
import os
import tempfile
from pathlib import Path

client = TestClient(app)


def test_read_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Bank Statement Reconciliation API"


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_upload_statement_no_files():
    """Test upload endpoint with no files."""
    response = client.post("/v1/upload-statement")
    assert response.status_code == 422  # Validation error


def test_upload_statement_invalid_mode():
    """Test upload with invalid processing mode."""
    # Create a dummy file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 dummy content")
        temp_file = f.name
    
    try:
        with open(temp_file, "rb") as f:
            response = client.post(
                "/v1/upload-statement",
                files={"files": ("test.pdf", f, "application/pdf")},
                data={"mode": "invalid_mode"}
            )
        
        # Should return error about invalid mode
        assert response.status_code in [400, 422]
    finally:
        os.unlink(temp_file)


def test_list_statements():
    """Test list statements endpoint."""
    response = client.get("/v1/statements")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "statements" in data


def test_get_statement_not_found():
    """Test retrieving non-existent statement."""
    response = client.get("/v1/statement/non-existent-id")
    assert response.status_code == 404


def test_webhook_no_payload():
    """Test webhook with no payload."""
    response = client.post("/v1/webhook/erp-notification")
    assert response.status_code == 422  # Missing body


def test_webhook_missing_event():
    """Test webhook with missing event field."""
    response = client.post(
        "/v1/webhook/erp-notification",
        json={"file_id": "test-123"}
    )
    assert response.status_code == 400


def test_webhook_valid_payload():
    """Test webhook with valid payload."""
    payload = {
        "event": "processing_complete",
        "file_id": "test-123",
        "transaction_count": 10,
        "status": "success"
    }
    response = client.post(
        "/v1/webhook/erp-notification",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "processing_complete"


def test_webhook_register():
    """Test webhook registration."""
    payload = {
        "url": "https://example.com/webhook",
        "events": ["processing_complete"],
        "secret": "test-secret"
    }
    response = client.post(
        "/v1/webhook/register",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "registered"
    assert data["url"] == payload["url"]
