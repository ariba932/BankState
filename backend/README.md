# BankState Backend

## Overview
AI-powered middleware for Nigerian bank statement reconciliation. Ingests PDF/Excel, extracts transactions, and outputs ISO 20022 camt.053 for ERP/open banking.

## Structure
- `main.py`: FastAPI entrypoint
- `api/`: API routes & webhooks
- `extractors/`: PDF/Excel extraction modules
- `mappers/`: ISO 20022 mapping
- `integrations/`: DocuClipper API integration
- `models/`: Data models (Pydantic)
- `utils/`: Shared utilities
- `tests/`: Unit/integration tests

## Key Endpoints
- `POST /upload-statement`: Upload and process bank statements
- `POST /webhook/erp-notification`: Receive ERP notifications

## Features
- Batch upload (up to 100 files)
- Local/DocuClipper extraction
- ISO 20022 camt.053 output
- Webhook for ERP integration
- Extensible for AI model training (future)

## Run
```bash
uvicorn main:app --reload
```

## Test
```bash
pytest
```
