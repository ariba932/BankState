from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status, Query, Path
from fastapi.responses import JSONResponse, Response
from typing import List, Optional
import os
import uuid
import shutil
from pathlib import Path as FilePath
from datetime import datetime

from extractors.pdf_extractor import extract_pdf_statement
from extractors.excel_extractor import extract_excel_statement
from integrations.docuclipper_api import extract_with_docuclipper
from mappers.camt053_mapper import map_to_camt053
from middleware.security import validate_file_size, validate_file_extension
from utils.exceptions import ValidationError, FileProcessingError
from utils.logger import get_logger
from config import get_settings
from models.api_models import (
    UploadStatementResponse,
    ListStatementsResponse,
    ErrorResponse,
)

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


def cleanup_file(file_path: str):
    """Background task to clean up temporary files."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")


@router.post(
    "/upload-statement",
    summary="Upload and process bank statements",
    description="Upload one or more bank statement files for processing and conversion to ISO 20022 camt.053 format",
    response_model=UploadStatementResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Successfully processed statements",
            "content": {
                "application/json": {
                    "example": {
                        "status": "completed",
                        "mode": "local",
                        "total_files": 1,
                        "successful": 1,
                        "failed": 0,
                        "results": [{
                            "file_id": "abc123-def456",
                            "filename": "gtbank_statement.pdf",
                            "status": "success",
                            "transaction_count": 45,
                            "account_info": {
                                "account_number": "0123456789",
                                "account_name": "JOHN DOE",
                                "bank_name": "gtbank"
                            },
                            "format_info": {
                                "bank": "gtbank",
                                "format": "tabular",
                                "confidence": 0.9,
                                "file_type": "pdf"
                            },
                            "output_file": "abc123-def456_camt053.xml",
                            "output_format": "xml"
                        }]
                    }
                }
            }
        },
        400: {"description": "Validation error (invalid input)", "model": ErrorResponse},
        413: {"description": "File size exceeds limit", "model": ErrorResponse},
        422: {"description": "Processing error", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
    },
    tags=["Statements"]
)
async def upload_statement(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(
        ...,
        description="Bank statement files (PDF, Excel). Maximum 100 files per request.",
        example="gtbank_statement.pdf"
    ),
    mode: str = Form(
        "local",
        description="Processing mode: 'local' (PyPDF2/openpyxl), 'docuclipper' (API), or 'ai' (future)",
        example="local"
    ),
    api_key: Optional[str] = Form(
        None,
        description="API key for DocuClipper integration (required when mode='docuclipper')",
        example="dc_api_key_here"
    ),
    output_format: str = Form(
        "xml",
        description="Output format: 'xml' for ISO 20022 XML or 'json' for JSON representation",
        example="xml"
    ),
):
    """
    Upload and process Nigerian bank statement files.
    
    ## Processing Modes
    
    - **local**: Process files using local extraction libraries
      - PDF: PyPDF2 for text extraction
      - Excel: pandas/openpyxl for spreadsheet parsing
      - Automatic bank detection for GTBank, Access, Zenith, UBA, etc.
    
    - **docuclipper**: Use DocuClipper API for enhanced OCR
      - 99.6% accuracy for scanned documents
      - Requires DocuClipper API key
      - Best for poor-quality scans
    
    - **ai**: Local AI model processing (future implementation)
      - LayoutLM/Donut-based extraction
      - Custom trained models
    
    ## Supported Banks
    
    - GTBank (Guaranty Trust Bank)
    - Access Bank
    - Zenith Bank
    - UBA (United Bank for Africa)
    - First Bank
    - Stanbic IBTC
    - Fidelity Bank
    - Union Bank
    
    ## File Requirements
    
    - **Formats**: PDF, XLS, XLSX
    - **Max size**: 50MB per file (configurable)
    - **Max batch**: 100 files per request
    - **Retention**: 7 days (configurable)
    
    ## Output Format
    
    Returns ISO 20022 camt.053 compliant data:
    - **XML**: Full ISO 20022 camt.053.001.02 structure
    - **JSON**: JSON representation of ISO 20022 data
    
    ## Example Response
    
    Successful processing returns:
    - File ID for retrieval
    - Extracted transaction count
    - Account information
    - Bank detection results
    - Output file reference
    """
    # Validate batch size
    if len(files) > settings.max_batch_size:
        raise ValidationError(
            f"Batch limit exceeded. Maximum {settings.max_batch_size} files allowed",
            details={"submitted": len(files), "max_allowed": settings.max_batch_size}
        )
    
    logger.info(f"Processing {len(files)} files in mode: {mode}")
    
    results = []
    processing_errors = []
    
    for file in files:
        file_id = str(uuid.uuid4())
        temp_path = None
        
        try:
            # Validate file extension
            validate_file_extension(file.filename)
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            validate_file_size(len(content))
            
            # Save to temporary location
            temp_dir = Path(settings.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            file_ext = Path(file.filename).suffix
            temp_path = temp_dir / f"{file_id}{file_ext}"
            
            with open(temp_path, "wb") as f:
                f.write(content)
            
            logger.info(f"Processing file: {file.filename} (size: {len(content)} bytes)")
            
            # Extract based on mode
            if mode == "local":
                extracted = await _process_local(str(temp_path), file.filename)
            elif mode == "docuclipper":
                extracted = await _process_docuclipper(str(temp_path), api_key)
            elif mode == "ai":
                # Future: AI model processing
                raise ValidationError("AI mode not yet implemented")
            else:
                raise ValidationError(f"Unknown processing mode: {mode}")
            
            # Map to ISO 20022 camt.053
            camt053_output = map_to_camt053(
                extracted.get("transactions", []),
                extracted.get("account_info"),
                output_format=output_format
            )
            
            # Save processed file
            processed_dir = Path(settings.processed_dir)
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            output_ext = ".xml" if output_format == "xml" else ".json"
            output_filename = f"{file_id}_camt053{output_ext}"
            output_path = processed_dir / output_filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(camt053_output)
            
            result = {
                "file_id": file_id,
                "filename": file.filename,
                "status": "success",
                "transaction_count": extracted.get("transaction_count", 0),
                "account_info": extracted.get("account_info"),
                "format_info": extracted.get("format_info"),
                "output_file": output_filename,
                "output_format": output_format,
            }
            
            results.append(result)
            logger.info(f"Successfully processed {file.filename}: {result['transaction_count']} transactions")
        
        except ValidationError as e:
            error = {
                "filename": file.filename,
                "error": e.message,
                "details": e.details
            }
            processing_errors.append(error)
            logger.warning(f"Validation error for {file.filename}: {e.message}")
        
        except Exception as e:
            error = {
                "filename": file.filename,
                "error": str(e),
                "type": type(e).__name__
            }
            processing_errors.append(error)
            logger.error(f"Error processing {file.filename}: {str(e)}", exc_info=True)
        
        finally:
            # Schedule cleanup of temporary file
            if temp_path and os.path.exists(temp_path):
                background_tasks.add_task(cleanup_file, str(temp_path))
    
    response_data = {
        "status": "completed",
        "mode": mode,
        "total_files": len(files),
        "successful": len(results),
        "failed": len(processing_errors),
        "results": results,
    }
    
    if processing_errors:
        response_data["errors"] = processing_errors
    
    return JSONResponse(content=response_data)


async def _process_local(file_path: str, filename: str) -> dict:
    """Process file using local extraction."""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext == ".pdf":
        return extract_pdf_statement(file_path)
    elif file_ext in [".xls", ".xlsx"]:
        return extract_excel_statement(file_path)
    else:
        raise FileProcessingError(f"Unsupported file type: {file_ext}")


async def _process_docuclipper(file_path: str, api_key: Optional[str]) -> dict:
    """Process file using DocuClipper API."""
    if not api_key and not settings.docuclipper_api_key:
        raise ValidationError(
            "API key required for DocuClipper mode",
            details={"hint": "Provide api_key parameter or set DOCUCLIPPER_API_KEY"}
        )
    
    return extract_with_docuclipper(file_path, api_key)


@router.get(
    "/statement/{file_id}",
    summary="Retrieve processed statement",
    description="Download a previously processed statement in ISO 20022 camt.053 format",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Successfully retrieved statement",
            "content": {
                "application/xml": {
                    "example": '<?xml version="1.0" encoding="UTF-8"?>\n<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.02">...'
                },
                "application/json": {
                    "example": {"Document": {"BkToCstmrStmt": {"GrpHdr": {"MsgId": "STMT-20251107120000"}}}}
                }
            }
        },
        404: {"description": "Statement not found", "model": ErrorResponse},
    },
    tags=["Statements"]
)
async def get_statement(
    file_id: str = Path(..., description="Unique file identifier from upload response", example="abc123-def456"),
    format: str = Query(
        "xml",
        description="Output format: 'xml' or 'json'",
        example="xml"
    )
):
    """
    Retrieve a previously processed bank statement.
    
    ## Usage
    
    After uploading and processing a statement, use the returned `file_id` to download
    the ISO 20022 camt.053 formatted output.
    
    ## Formats
    
    - **xml**: ISO 20022 camt.053.001.02 XML document
    - **json**: JSON representation of the same structure
    
    ## Retention
    
    Processed files are retained for 7 days (configurable) before automatic cleanup.
    
    ## Example
    
    ```bash
    curl "http://localhost:8000/v1/statement/abc123-def456?format=xml" > statement.xml
    ```
    """
    processed_dir = FilePath(settings.processed_dir)
    output_ext = ".xml" if format == "xml" else ".json"
    output_path = processed_dir / f"{file_id}_camt053{output_ext}"
    
    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Statement not found for file_id: {file_id}"
        )
    
    with open(output_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    media_type = "application/xml" if format == "xml" else "application/json"
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={file_id}_camt053{output_ext}"
        }
    )


@router.get(
    "/statements",
    summary="List processed statements",
    description="Get a list of all available processed bank statements",
    response_model=ListStatementsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Successfully retrieved statement list",
            "content": {
                "application/json": {
                    "example": {
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
                }
            }
        }
    },
    tags=["Statements"]
)
async def list_statements():
    """
    List all available processed statements.
    
    ## Response
    
    Returns metadata for all statements currently available:
    - File ID for retrieval
    - Filename
    - File size in bytes
    - Creation timestamp
    
    ## Retention
    
    Only files within the retention period (default 7 days) are listed.
    Older files are automatically cleaned up.
    
    ## Pagination
    
    Currently returns all available statements. For production with large volumes,
    consider implementing pagination.
    """
    processed_dir = FilePath(settings.processed_dir)
    
    if not processed_dir.exists():
        return JSONResponse(content={"statements": []})
    
    statements = []
    for file_path in processed_dir.glob("*_camt053.*"):
        stat = file_path.stat()
        file_id = file_path.stem.replace("_camt053", "")
        
        statements.append({
            "file_id": file_id,
            "filename": file_path.name,
            "size": stat.st_size,
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        })
    
    return JSONResponse(content={
        "count": len(statements),
        "statements": statements
    })
