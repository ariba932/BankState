# BankState Backend API

## Overview
AI-powered middleware for Nigerian bank statement reconciliation. Ingests PDF/Excel statements, extracts transactions using intelligent parsing or external APIs, and outputs ISO 20022 camt.053-compliant data for ERP integration and open banking.

## Features

### ✅ Production-Ready Components
- **Multi-format extraction**: PDF (PyPDF2) and Excel (pandas/openpyxl) support
- **Bank auto-detection**: Automatic identification of Nigerian banks (GTB, Access, Zenith, UBA, etc.)
- **ISO 20022 compliance**: Full camt.053 XML/JSON output generation
- **External integration**: DocuClipper API support for enhanced OCR
- **Robust error handling**: Structured exceptions with detailed logging
- **Security**: Rate limiting, API key auth, CORS, input validation
- **File management**: Automatic cleanup, retention policies
- **Monitoring**: Health checks, structured logging (JSON/text)
- **Webhooks**: ERP integration with signature verification
- **Comprehensive testing**: Unit and integration test suite

### 🚧 Future Enhancements
- Database integration (SQLite/PostgreSQL)
- Async background processing (Celery)
- Local AI models (LayoutLM/Donut)
- Advanced fraud detection

## Architecture

```
backend/
├── main.py                  # FastAPI application entry
├── config.py                # Configuration management
├── api/
│   ├── routes.py           # Statement processing endpoints
│   └── webhook.py          # Webhook handlers
├── extractors/
│   ├── pdf_extractor.py    # PDF statement parsing
│   └── excel_extractor.py  # Excel statement parsing
├── mappers/
│   └── camt053_mapper.py   # ISO 20022 XML/JSON generation
├── integrations/
│   └── docuclipper_api.py  # External API integration
├── middleware/
│   ├── error_handler.py    # Global exception handling
│   └── security.py         # Auth, rate limiting, validation
├── models/
│   └── transaction.py      # Pydantic data models
├── utils/
│   ├── logger.py           # Structured logging
│   ├── exceptions.py       # Custom exceptions
│   └── bank_format_detector.py  # Bank format detection
└── tests/                   # Comprehensive test suite
```

## Installation

### Prerequisites
- Python 3.10+
- pip or poetry

### Setup

1. **Clone and navigate to backend:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Create required directories:**
```bash
mkdir -p uploads processed temp logs models
```

## Configuration

### Environment Variables (.env)

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False

# Security
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# File Settings
MAX_UPLOAD_SIZE=52428800  # 50MB
MAX_BATCH_SIZE=100
RETENTION_DAYS=7

# DocuClipper Integration
DOCUCLIPPER_API_KEY=your-api-key-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Running the Application

### Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
```bash
docker build -t bankstate-backend .
docker run -p 8000:8000 --env-file .env bankstate-backend
```

## API Documentation

### Interactive API Docs
Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Key Endpoints

#### 1. Upload & Process Statements
```bash
POST /v1/upload-statement

# Local processing
curl -X POST "http://localhost:8000/v1/upload-statement" \
  -F "files=@statement.pdf" \
  -F "mode=local" \
  -F "output_format=xml"

# DocuClipper processing
curl -X POST "http://localhost:8000/v1/upload-statement" \
  -F "files=@statement.pdf" \
  -F "mode=docuclipper" \
  -F "api_key=your-api-key" \
  -F "output_format=json"
```

**Response:**
```json
{
  "status": "completed",
  "mode": "local",
  "total_files": 1,
  "successful": 1,
  "failed": 0,
  "results": [{
    "file_id": "uuid-here",
    "filename": "statement.pdf",
    "status": "success",
    "transaction_count": 45,
    "account_info": {
      "account_number": "0123456789",
      "account_name": "JOHN DOE",
      "bank_name": "gtbank"
    },
    "output_file": "uuid_camt053.xml"
  }]
}
```

#### 2. Retrieve Processed Statement
```bash
GET /v1/statement/{file_id}?format=xml

curl "http://localhost:8000/v1/statement/{file_id}?format=xml"
```

#### 3. List All Statements
```bash
GET /v1/statements

curl "http://localhost:8000/v1/statements"
```

#### 4. Webhook Endpoints
```bash
# ERP Notification
POST /v1/webhook/erp-notification

# Register Webhook
POST /v1/webhook/register
```

#### 5. Health Check
```bash
GET /health

curl "http://localhost:8000/health"
```

## Testing

### Run All Tests
```bash
pytest
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run Specific Tests
```bash
# Unit tests only
pytest tests/test_config.py

# Integration tests
pytest tests/test_basic.py
```

### View Coverage Report
```bash
# Generate HTML report
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Nigerian Bank Support

The system currently supports automatic detection and parsing for:
- **GTBank** (Guaranty Trust Bank)
- **Access Bank**
- **Zenith Bank**
- **UBA** (United Bank for Africa)
- **First Bank**
- **Stanbic IBTC**
- **Fidelity Bank**
- **Union Bank**

### Adding New Banks
To add support for a new bank:

1. Update `utils/bank_format_detector.py` with bank patterns
2. Add bank-specific parsing rules in extractors
3. Test with sample statements

## Troubleshooting

### Common Issues

**1. Import errors on startup**
```bash
# Ensure all dependencies are installed
pip install -r requirements.txt
```

**2. File upload fails with 413**
```bash
# Increase MAX_UPLOAD_SIZE in .env
MAX_UPLOAD_SIZE=104857600  # 100MB
```

**3. DocuClipper integration fails**
```bash
# Verify API key is set
echo $DOCUCLIPPER_API_KEY
# Check API endpoint accessibility
curl -I https://api.docuclipper.com/v1
```

**4. PDF extraction returns empty**
- Check PDF is not scanned image (use DocuClipper mode)
- Verify PDF is not password-protected
- Check PDF version compatibility

## Performance Optimization

### Recommendations
1. **Use workers**: Run with multiple Uvicorn workers
   ```bash
   uvicorn main:app --workers 4
   ```

2. **Enable caching**: Implement Redis for processed results

3. **Async processing**: For large batches, implement background tasks

4. **Database**: Add PostgreSQL for job tracking and analytics

## Security Best Practices

1. **API Keys**: Always use strong, unique API keys in production
2. **HTTPS**: Use reverse proxy (Nginx) with SSL certificates
3. **Rate Limiting**: Configure appropriate limits per client
4. **File Validation**: Enforced automatically (size, type, content)
5. **Webhook Signatures**: Verify HMAC signatures for webhooks

## Deployment

### Production Checklist
- [ ] Set `API_DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure log rotation
- [ ] Set up monitoring (Prometheus, Grafana)
- [ ] Configure database for persistence
- [ ] Set up backup strategy
- [ ] Implement rate limiting per client
- [ ] Configure firewall rules

### Docker Deployment
See `Dockerfile` for containerized deployment.

### Cloud Deployment
- **AWS**: EC2 + RDS, or ECS/Fargate
- **GCP**: Cloud Run, Cloud SQL
- **Azure**: App Service, Azure Database

## Monitoring & Logging

### Structured Logging
Logs are output in JSON format by default:
```json
{
  "timestamp": "2025-11-07T10:00:00",
  "level": "INFO",
  "logger": "bankstate",
  "message": "Processing file",
  "correlation_id": "abc123"
}
```

### Health Monitoring
```bash
# Check application health
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "version": "v1",
  "service": "bankstate-api"
}
```

## Contributing

1. Write tests for new features
2. Follow existing code structure
3. Update documentation
4. Run tests before committing
5. Follow Python best practices (PEP 8)

## Support

For issues or questions:
- GitHub Issues: Report bugs or request features
- Documentation: See `/docs` in Swagger UI

---

**Version**: 1.0.0  
**Last Updated**: November 7, 2025  
**Status**: Production Ready (Core Features)
