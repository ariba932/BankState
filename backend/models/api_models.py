from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class TransactionResponse(BaseModel):
    """Transaction response model."""
    date: str = Field(..., description="Transaction date in ISO format")
    description: str = Field(..., description="Transaction description/narration")
    debit: float = Field(..., description="Debit amount")
    credit: float = Field(..., description="Credit amount")
    amount: float = Field(..., description="Net transaction amount (positive for credit, negative for debit)")
    balance: float = Field(..., description="Account balance after transaction")
    type: str = Field(..., description="Transaction type: 'credit' or 'debit'")
    currency: str = Field(default="NGN", description="Currency code (ISO 4217)")
    reference: Optional[str] = Field(None, description="Transaction reference number")


class AccountInfo(BaseModel):
    """Account information model."""
    account_number: Optional[str] = Field(None, description="Bank account number")
    account_name: Optional[str] = Field(None, description="Account holder name")
    bank_name: Optional[str] = Field(None, description="Bank name or code")
    statement_period: Optional[Dict[str, str]] = Field(None, description="Statement period (from/to dates)")
    opening_balance: Optional[float] = Field(None, description="Opening balance")
    closing_balance: Optional[float] = Field(None, description="Closing balance")


class FormatInfo(BaseModel):
    """Bank format detection information."""
    bank: str = Field(..., description="Detected bank identifier")
    format: str = Field(..., description="Document format type")
    confidence: float = Field(..., description="Detection confidence score (0-1)")
    file_type: str = Field(..., description="File type (pdf, excel, etc.)")


class UploadResult(BaseModel):
    """Single file upload result."""
    file_id: str = Field(..., description="Unique identifier for the processed file")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Processing status")
    transaction_count: int = Field(..., description="Number of transactions extracted")
    account_info: Optional[AccountInfo] = Field(None, description="Extracted account information")
    format_info: Optional[FormatInfo] = Field(None, description="Bank format detection results")
    output_file: str = Field(..., description="Name of the generated output file")
    output_format: str = Field(..., description="Output format (xml or json)")


class UploadError(BaseModel):
    """Upload error model."""
    filename: str = Field(..., description="Filename that failed")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class UploadStatementResponse(BaseModel):
    """Upload statement response model."""
    status: str = Field(..., description="Overall processing status", example="completed")
    mode: str = Field(..., description="Processing mode used", example="local")
    total_files: int = Field(..., description="Total number of files submitted")
    successful: int = Field(..., description="Number of successfully processed files")
    failed: int = Field(..., description="Number of failed files")
    results: List[UploadResult] = Field(..., description="List of processing results")
    errors: Optional[List[UploadError]] = Field(None, description="List of errors (if any)")


class StatementInfo(BaseModel):
    """Statement file information."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Filename")
    size: int = Field(..., description="File size in bytes")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")


class ListStatementsResponse(BaseModel):
    """List statements response."""
    count: int = Field(..., description="Total number of statements")
    statements: List[StatementInfo] = Field(..., description="List of statement files")


class WebhookPayload(BaseModel):
    """Webhook payload model."""
    event: str = Field(..., description="Event type", example="processing_complete")
    file_id: Optional[str] = Field(None, description="File identifier")
    transaction_count: Optional[int] = Field(None, description="Number of transactions")
    status: Optional[str] = Field(None, description="Processing status")
    timestamp: Optional[str] = Field(None, description="Event timestamp")
    error: Optional[str] = Field(None, description="Error message (if applicable)")


class WebhookResponse(BaseModel):
    """Webhook response model."""
    status: str = Field(..., description="Response status", example="success")
    event: str = Field(..., description="Event type that was processed")
    processed_at: str = Field(..., description="Processing timestamp (ISO format)")
    result: Dict[str, Any] = Field(..., description="Processing result details")


class WebhookRegistration(BaseModel):
    """Webhook registration request."""
    url: str = Field(..., description="Webhook URL to receive notifications", example="https://your-erp.com/webhook")
    events: List[str] = Field(..., description="List of events to subscribe to", example=["processing_complete", "processing_failed"])
    secret: Optional[str] = Field(None, description="Webhook secret for signature verification")


class WebhookRegistrationResponse(BaseModel):
    """Webhook registration response."""
    status: str = Field(..., description="Registration status", example="registered")
    url: str = Field(..., description="Registered webhook URL")
    events: List[str] = Field(..., description="Subscribed events")
    registered_at: str = Field(..., description="Registration timestamp (ISO format)")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status", example="healthy")
    version: str = Field(..., description="API version", example="v1")
    service: str = Field(..., description="Service name", example="bankstate-api")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")
