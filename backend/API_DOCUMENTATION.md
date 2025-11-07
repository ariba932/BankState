# API Documentation Guide

## Overview

This document provides comprehensive information about the BankState API, including endpoint descriptions, request/response formats, authentication, and integration examples.

## Base URL

```
Development: http://localhost:8000
Production: https://api.bankstate.example.com
```

## Interactive Documentation

The API provides interactive documentation via Swagger UI and ReDoc:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Authentication

### API Key (Optional)

For enhanced security, API key authentication can be enabled:

```bash
curl -X POST "http://localhost:8000/v1/upload-statement" \
  -H "X-API-Key: your-api-key-here" \
  -F "files=@statement.pdf"
```

### Rate Limiting

- **Default**: 100 requests per 60 seconds per IP
- **Header**: `X-RateLimit-Remaining` shows remaining requests
- **Error**: `429 Too Many Requests` when exceeded

## Endpoints

### 1. Upload Statement (`POST /v1/upload-statement`)

Upload and process bank statement files.

**Request:**

```bash
curl -X POST "http://localhost:8000/v1/upload-statement" \
  -F "files=@gtbank_statement.pdf" \
  -F "mode=local" \
  -F "output_format=xml"
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| files | file[] | Yes | Bank statement files (PDF/Excel) |
| mode | string | No | Processing mode: `local`, `docuclipper`, `ai` |
| api_key | string | Conditional | DocuClipper API key (required for `docuclipper` mode) |
| output_format | string | No | Output format: `xml` or `json` |

**Response (200 OK):**

```json
{
  "status": "completed",
  "mode": "local",
  "total_files": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "file_id": "abc123-def456",
      "filename": "gtbank_statement.pdf",
      "status": "success",
      "transaction_count": 45,
      "account_info": {
        "account_number": "0123456789",
        "account_name": "JOHN DOE",
        "bank_name": "gtbank",
        "opening_balance": 100000.00,
        "closing_balance": 125000.00
      },
      "format_info": {
        "bank": "gtbank",
        "format": "tabular",
        "confidence": 0.9,
        "file_type": "pdf"
      },
      "output_file": "abc123-def456_camt053.xml",
      "output_format": "xml"
    }
  ]
}
```

**Error Responses:**

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid parameters |
| 413 | Payload Too Large - File size exceeds limit |
| 422 | Unprocessable Entity - Processing error |
| 429 | Too Many Requests - Rate limit exceeded |

---

### 2. Get Statement (`GET /v1/statement/{file_id}`)

Retrieve a processed statement by file ID.

**Request:**

```bash
curl "http://localhost:8000/v1/statement/abc123-def456?format=xml" \
  -o statement.xml
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file_id | path | Yes | Unique file identifier from upload |
| format | query | No | Output format: `xml` (default) or `json` |

**Response (200 OK):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">
  <BkToCstmrStmt>
    <GrpHdr>
      <MsgId>STMT-20251107120000</MsgId>
      <CreDtTm>2025-11-07T12:00:00.000000</CreDtTm>
    </GrpHdr>
    <Stmt>
      <!-- Statement details -->
    </Stmt>
  </BkToCstmrStmt>
</Document>
```

**Error Responses:**

| Status Code | Description |
|-------------|-------------|
| 404 | Not Found - File ID does not exist |

---

### 3. List Statements (`GET /v1/statements`)

List all available processed statements.

**Request:**

```bash
curl "http://localhost:8000/v1/statements"
```

**Response (200 OK):**

```json
{
  "count": 2,
  "statements": [
    {
      "file_id": "abc123-def456",
      "filename": "abc123-def456_camt053.xml",
      "size": 15234,
      "created_at": "2025-11-07T10:30:00"
    },
    {
      "file_id": "xyz789-uvw012",
      "filename": "xyz789-uvw012_camt053.json",
      "size": 12456,
      "created_at": "2025-11-07T11:00:00"
    }
  ]
}
```

---

### 4. Webhook Notification (`POST /v1/webhook/erp-notification`)

Receive processing notifications (for ERP integration).

**Request:**

```bash
curl -X POST "http://localhost:8000/v1/webhook/erp-notification" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: a1b2c3d4..." \
  -d '{
    "event": "processing_complete",
    "file_id": "abc123-def456",
    "transaction_count": 45,
    "status": "success"
  }'
```

**Event Types:**

- `processing_complete` - File processed successfully
- `processing_failed` - Processing encountered error
- `reconciliation_request` - Reconciliation data requested

**Response (200 OK):**

```json
{
  "status": "success",
  "event": "processing_complete",
  "processed_at": "2025-11-07T12:00:00.000000",
  "result": {
    "action": "acknowledged",
    "file_id": "abc123-def456",
    "transactions": 45
  }
}
```

---

### 5. Register Webhook (`POST /v1/webhook/register`)

Register a webhook URL for notifications.

**Request:**

```bash
curl -X POST "http://localhost:8000/v1/webhook/register" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-erp.com/webhook",
    "events": ["processing_complete", "processing_failed"],
    "secret": "your-webhook-secret"
  }'
```

**Response (200 OK):**

```json
{
  "status": "registered",
  "url": "https://your-erp.com/webhook",
  "events": ["processing_complete", "processing_failed"],
  "registered_at": "2025-11-07T12:00:00.000000"
}
```

---

### 6. Health Check (`GET /health`)

Check API health status.

**Request:**

```bash
curl "http://localhost:8000/health"
```

**Response (200 OK):**

```json
{
  "status": "healthy",
  "version": "v1",
  "service": "bankstate-api"
}
```

---

## Request Examples

### Python

```python
import requests

# Upload statement
url = "http://localhost:8000/v1/upload-statement"
files = {"files": open("statement.pdf", "rb")}
data = {"mode": "local", "output_format": "xml"}

response = requests.post(url, files=files, data=data)
result = response.json()
file_id = result["results"][0]["file_id"]

# Retrieve processed statement
statement_url = f"http://localhost:8000/v1/statement/{file_id}"
statement = requests.get(statement_url, params={"format": "xml"})
print(statement.text)
```

### JavaScript/Node.js

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

// Upload statement
const form = new FormData();
form.append('files', fs.createReadStream('statement.pdf'));
form.append('mode', 'local');
form.append('output_format', 'xml');

axios.post('http://localhost:8000/v1/upload-statement', form, {
  headers: form.getHeaders()
})
.then(response => {
  const fileId = response.data.results[0].file_id;
  
  // Retrieve processed statement
  return axios.get(`http://localhost:8000/v1/statement/${fileId}`, {
    params: { format: 'xml' }
  });
})
.then(statement => {
  console.log(statement.data);
});
```

### cURL

```bash
# Upload and process
curl -X POST "http://localhost:8000/v1/upload-statement" \
  -F "files=@statement.pdf" \
  -F "mode=local" \
  -F "output_format=xml" \
  | jq -r '.results[0].file_id' > file_id.txt

# Retrieve result
FILE_ID=$(cat file_id.txt)
curl "http://localhost:8000/v1/statement/$FILE_ID?format=xml" \
  -o statement_camt053.xml
```

---

## Response Models

### UploadStatementResponse

```typescript
{
  status: string;           // "completed"
  mode: string;            // "local" | "docuclipper" | "ai"
  total_files: number;     // Total files submitted
  successful: number;      // Successfully processed
  failed: number;          // Failed processing
  results: UploadResult[]; // Array of results
  errors?: UploadError[];  // Array of errors (if any)
}
```

### UploadResult

```typescript
{
  file_id: string;              // Unique identifier
  filename: string;             // Original filename
  status: string;               // "success" | "failed"
  transaction_count: number;    // Number of transactions
  account_info: AccountInfo;    // Account details
  format_info: FormatInfo;      // Detection results
  output_file: string;          // Output filename
  output_format: string;        // "xml" | "json"
}
```

### AccountInfo

```typescript
{
  account_number?: string;      // Account number
  account_name?: string;        // Account holder name
  bank_name?: string;           // Bank identifier
  statement_period?: {          // Statement period
    from: string;
    to: string;
  };
  opening_balance?: number;     // Opening balance
  closing_balance?: number;     // Closing balance
}
```

### FormatInfo

```typescript
{
  bank: string;                 // Bank identifier
  format: string;               // Document format type
  confidence: number;           // Detection confidence (0-1)
  file_type: string;            // "pdf" | "excel"
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error message",
  "details": {
    "field": "value",
    "additional": "information"
  },
  "status_code": 400
}
```

### Common Error Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 400 | Bad Request | Invalid parameters, missing required fields |
| 401 | Unauthorized | Invalid or missing API key |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource does not exist |
| 413 | Payload Too Large | File size exceeds limit |
| 422 | Unprocessable Entity | File processing error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | External service error (DocuClipper) |

---

## Rate Limiting

### Default Limits

- **100 requests per 60 seconds** per IP address
- Applies to all endpoints

### Headers

Response includes rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699363200
```

### Handling Rate Limits

When rate limited (429 response):

```json
{
  "error": "Rate limit exceeded",
  "details": {
    "retry_after": 60
  },
  "status_code": 429
}
```

Implement exponential backoff:

```python
import time

def upload_with_retry(file_path, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, files=files)
        
        if response.status_code == 429:
            retry_after = response.json()["details"].get("retry_after", 60)
            time.sleep(retry_after)
            continue
            
        return response
```

---

## Webhook Security

### Signature Verification

Verify webhook authenticity using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)

# Usage
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Webhook-Signature')
    
    if not verify_webhook(payload, signature, WEBHOOK_SECRET):
        return {'error': 'Invalid signature'}, 401
    
    # Process webhook
    data = request.json
    # ...
```

---

## Best Practices

### 1. File Upload

- Validate file types before upload
- Check file size (max 50MB default)
- Use appropriate processing mode
- Handle errors gracefully

### 2. Batch Processing

- Group multiple files in single request (max 100)
- Process in parallel when possible
- Implement retry logic for failures

### 3. Error Handling

- Always check response status
- Parse error details for troubleshooting
- Implement exponential backoff for retries
- Log errors for debugging

### 4. Security

- Use HTTPS in production
- Implement API key authentication
- Verify webhook signatures
- Rotate secrets regularly

### 5. Performance

- Use connection pooling
- Implement caching where appropriate
- Monitor rate limits
- Consider async processing for large batches

---

## Testing

### Using Swagger UI

1. Navigate to `http://localhost:8000/docs`
2. Click "Try it out" on any endpoint
3. Fill in parameters
4. Click "Execute"
5. View response

### Sample Test Files

Create test statements in `tests/fixtures/`:

- `gtbank_sample.pdf`
- `access_sample.xlsx`
- `zenith_sample.pdf`

### Integration Tests

```python
def test_upload_and_retrieve():
    # Upload
    response = client.post(
        "/v1/upload-statement",
        files={"files": ("test.pdf", pdf_content, "application/pdf")},
        data={"mode": "local", "output_format": "xml"}
    )
    assert response.status_code == 200
    
    file_id = response.json()["results"][0]["file_id"]
    
    # Retrieve
    statement = client.get(f"/v1/statement/{file_id}")
    assert statement.status_code == 200
    assert "BkToCstmrStmt" in statement.text
```

---

## Support

For additional help:

- **Documentation**: See `DEPLOYMENT.md` and `QUICKSTART.md`
- **Issues**: GitHub Issues
- **API Status**: `/health` endpoint

---

**Version**: 1.0  
**Last Updated**: November 7, 2025  
**API Version**: v1
