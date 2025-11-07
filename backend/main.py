from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.routes import router as statement_router
from api.webhook import router as webhook_router
from middleware.error_handler import (
    bankstate_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
)
from middleware.security import SecurityMiddleware
from utils.exceptions import BankStateException
from utils.logger import setup_logger, get_logger
from config import get_settings, ensure_directories

# Initialize settings and logger
settings = get_settings()
logger = setup_logger(
    name="bankstate",
    level=settings.log_level,
    log_format=settings.log_format,
    log_file=settings.log_file,
)

# Ensure required directories exist
ensure_directories()

# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    description="""
## Overview

AI-powered middleware for Nigerian bank statement reconciliation. Ingests PDF/Excel statements, 
extracts transactions using intelligent parsing or external APIs, and outputs ISO 20022 
camt.053-compliant data for ERP integration and open banking.

## Key Features

* **Multi-format Support**: PDF and Excel bank statements
* **Auto Bank Detection**: Automatic identification of 8 major Nigerian banks
* **ISO 20022 Compliant**: Full camt.053 XML/JSON output
* **External Integration**: DocuClipper API for enhanced OCR
* **Production Ready**: Error handling, logging, security, rate limiting
* **Webhook Support**: Real-time ERP notifications

## Supported Banks

* GTBank (Guaranty Trust Bank)
* Access Bank
* Zenith Bank
* UBA (United Bank for Africa)
* First Bank
* Stanbic IBTC
* Fidelity Bank
* Union Bank

## Processing Modes

1. **Local**: PyPDF2/openpyxl extraction (free, fast)
2. **DocuClipper**: API-based OCR (99.6% accuracy, requires API key)
3. **AI**: Custom models (future implementation)

## Quick Start

1. Upload bank statement via `/v1/upload-statement`
2. Receive file_id and transaction data
3. Download ISO 20022 output via `/v1/statement/{file_id}`

## Documentation

* **API Reference**: This page
* **GitHub**: [BankState Repository](https://github.com/ariba932/BankState)
* **Support**: See deployment documentation
""",
    version=settings.api_version,
    debug=settings.api_debug,
    contact={
        "name": "BankState API Support",
        "email": "support@bankstate.example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    terms_of_service="https://bankstate.example.com/terms",
    openapi_tags=[
        {
            "name": "Statements",
            "description": "Bank statement upload, processing, and retrieval operations. Core functionality for converting bank statements to ISO 20022 format.",
        },
        {
            "name": "Webhooks",
            "description": "Webhook management for ERP integration. Register webhooks to receive real-time processing notifications.",
        },
        {
            "name": "Health",
            "description": "System health and monitoring endpoints for operational visibility.",
        },
    ],
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(SecurityMiddleware)

# Register exception handlers
app.add_exception_handler(BankStateException, bankstate_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Health check endpoint
@app.get(
    "/health",
    summary="Health check",
    description="Check API health status and version information",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "v1",
                        "service": "bankstate-api"
                    }
                }
            }
        }
    },
    tags=["Health"]
)
async def health_check():
    """
    Health check endpoint for monitoring and load balancer health checks.
    
    ## Response
    
    Returns current health status and version information:
    - **status**: "healthy" or "unhealthy"
    - **version**: API version
    - **service**: Service identifier
    
    ## Usage
    
    Use this endpoint for:
    - Load balancer health checks
    - Monitoring system probes
    - Deployment verification
    - Uptime monitoring
    
    ## Example
    
    ```bash
    curl http://localhost:8000/health
    ```
    """
    return {
        "status": "healthy",
        "version": settings.api_version,
        "service": "bankstate-api"
    }

@app.get(
    "/",
    summary="API root",
    description="Get API information and available endpoints",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "API information",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Bank Statement Reconciliation API",
                        "version": "v1",
                        "docs": "/docs",
                        "health": "/health"
                    }
                }
            }
        }
    },
    tags=["Health"]
)
def read_root():
    """
    Root endpoint providing API information and navigation.
    
    ## Response
    
    Returns basic API information and links to:
    - Interactive API documentation (Swagger UI)
    - Health check endpoint
    - API version information
    
    ## Quick Links
    
    - **Documentation**: [/docs](/docs)
    - **Alternative Docs**: [/redoc](/redoc)
    - **OpenAPI Schema**: [/openapi.json](/openapi.json)
    - **Health Check**: [/health](/health)
    """
    return {
        "message": "Bank Statement Reconciliation API",
        "version": settings.api_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health"
    }

# Include routers
app.include_router(statement_router, prefix=f"/{settings.api_version}", tags=["statements"])
app.include_router(webhook_router, prefix=f"/{settings.api_version}", tags=["webhooks"])

# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {'Development' if settings.api_debug else 'Production'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Shutting down API")
