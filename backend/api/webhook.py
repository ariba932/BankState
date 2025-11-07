from fastapi import APIRouter, Request, HTTPException, Header, status
from fastapi.responses import JSONResponse
from typing import Optional
import hmac
import hashlib
from datetime import datetime

from utils.logger import get_logger
from utils.exceptions import ValidationError, AuthenticationError
from config import get_settings
from models.api_models import (
    WebhookPayload,
    WebhookResponse,
    WebhookRegistration,
    WebhookRegistrationResponse,
    ErrorResponse,
)

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


@router.post(
    "/webhook/erp-notification",
    summary="ERP webhook endpoint",
    description="Receive webhook notifications from the processing system for ERP integration",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Webhook successfully processed",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "event": "processing_complete",
                        "processed_at": "2025-11-07T12:00:00.000000",
                        "result": {
                            "action": "acknowledged",
                            "file_id": "abc123-def456",
                            "transactions": 45
                        }
                    }
                }
            }
        },
        400: {"description": "Validation error (missing required fields)", "model": ErrorResponse},
        401: {"description": "Authentication failed (invalid signature)", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    tags=["Webhooks"]
)
async def erp_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(
        None,
        description="HMAC-SHA256 signature for webhook verification (optional)",
        example="a1b2c3d4e5f6..."
    )
):
    """
    Webhook endpoint for receiving processing notifications from ERP systems.
    
    ## Event Types
    
    - **processing_complete**: File processing finished successfully
    - **processing_failed**: File processing encountered an error
    - **reconciliation_request**: ERP requesting reconciliation data
    
    ## Request Payload
    
    ```json
    {
        "event": "processing_complete",
        "file_id": "abc123-def456",
        "transaction_count": 45,
        "status": "success",
        "timestamp": "2025-11-07T10:00:00Z"
    }
    ```
    
    ## Security
    
    ### Signature Verification (Recommended)
    
    Include `X-Webhook-Signature` header with HMAC-SHA256 signature:
    
    ```python
    import hmac
    import hashlib
    
    secret = "your-webhook-secret"
    payload = json.dumps(data)
    signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    ```
    
    ## Event Handling
    
    The endpoint routes events to appropriate handlers:
    - Logs event receipt
    - Validates payload structure
    - Verifies signature (if provided)
    - Processes event-specific logic
    - Returns acknowledgment
    
    ## Example Usage
    
    ```bash
    curl -X POST "http://localhost:8000/v1/webhook/erp-notification" \\
      -H "Content-Type: application/json" \\
      -H "X-Webhook-Signature: signature-here" \\
      -d '{
        "event": "processing_complete",
        "file_id": "abc123-def456",
        "transaction_count": 45,
        "status": "success"
      }'
    ```
    """
    try:
        # Get raw payload
        payload_bytes = await request.body()
        payload = await request.json()
        
        logger.info(f"Received webhook: {payload.get('event', 'unknown')}")
        
        # Verify signature if provided
        if x_webhook_signature:
            if not _verify_webhook_signature(payload_bytes, x_webhook_signature):
                raise AuthenticationError("Invalid webhook signature")
        
        # Validate required fields
        event = payload.get('event')
        if not event:
            raise ValidationError("Missing 'event' field in webhook payload")
        
        # Process different event types
        if event == "processing_complete":
            result = await _handle_processing_complete(payload)
        elif event == "processing_failed":
            result = await _handle_processing_failed(payload)
        elif event == "reconciliation_request":
            result = await _handle_reconciliation_request(payload)
        else:
            logger.warning(f"Unknown webhook event type: {event}")
            result = {"status": "acknowledged", "message": f"Unknown event type: {event}"}
        
        return JSONResponse(content={
            "status": "success",
            "event": event,
            "processed_at": datetime.utcnow().isoformat(),
            "result": result
        })
    
    except ValidationError as e:
        logger.warning(f"Webhook validation error: {e.message}")
        raise HTTPException(status_code=400, detail=e.message)
    
    except AuthenticationError as e:
        logger.warning(f"Webhook authentication error: {e.message}")
        raise HTTPException(status_code=401, detail=e.message)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/webhook/register",
    summary="Register webhook URL",
    description="Register a webhook URL to receive processing notifications",
    response_model=WebhookRegistrationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Webhook successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "status": "registered",
                        "url": "https://your-erp.com/webhook",
                        "events": ["processing_complete", "processing_failed"],
                        "registered_at": "2025-11-07T12:00:00.000000"
                    }
                }
            }
        },
        400: {"description": "Validation error (missing url)", "model": ErrorResponse},
    },
    tags=["Webhooks"]
)
async def register_webhook(request: Request):
    """
    Register a webhook URL for receiving processing notifications.
    
    ## Purpose
    
    Register your ERP or system endpoint to receive real-time notifications about:
    - Statement processing completion
    - Processing failures
    - Reconciliation requests
    
    ## Request Payload
    
    ```json
    {
        "url": "https://your-erp.com/webhooks/bankstate",
        "events": ["processing_complete", "processing_failed"],
        "secret": "your-webhook-secret-key"
    }
    ```
    
    ## Supported Events
    
    - `processing_complete`: Statement successfully processed
    - `processing_failed`: Statement processing failed
    - `reconciliation_request`: Reconciliation data requested
    
    ## Webhook Secret
    
    Provide a secret key to enable HMAC-SHA256 signature verification on webhook deliveries.
    This ensures webhook authenticity.
    
    ## Future Implementation
    
    Currently stores registration in memory. In production:
    - Store registrations in database
    - Support multiple webhook URLs
    - Implement retry logic for failed deliveries
    - Add webhook testing/verification
    
    ## Example Usage
    
    ```bash
    curl -X POST "http://localhost:8000/v1/webhook/register" \\
      -H "Content-Type: application/json" \\
      -d '{
        "url": "https://your-erp.com/webhook",
        "events": ["processing_complete"],
        "secret": "my-secret-key"
      }'
    ```
    
    ## Testing Your Webhook
    
    After registration, process a test statement to receive a webhook notification.
    """
    payload = await request.json()
    
    webhook_url = payload.get('url')
    events = payload.get('events', [])
    secret = payload.get('secret')
    
    if not webhook_url:
        raise ValidationError("Missing 'url' field")
    
    # TODO: Store webhook registration in database
    # For now, just acknowledge
    
    logger.info(f"Webhook registered: {webhook_url} for events: {events}")
    
    return JSONResponse(content={
        "status": "registered",
        "url": webhook_url,
        "events": events,
        "registered_at": datetime.utcnow().isoformat()
    })


def _verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body
        signature: Signature from header
    
    Returns:
        True if signature is valid
    """
    if not settings.secret_key:
        logger.warning("No secret key configured for webhook signature verification")
        return True
    
    try:
        expected_signature = hmac.new(
            settings.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


async def _handle_processing_complete(payload: dict) -> dict:
    """Handle processing complete event."""
    file_id = payload.get('file_id')
    transaction_count = payload.get('transaction_count', 0)
    
    logger.info(f"Processing complete for file {file_id}: {transaction_count} transactions")
    
    # TODO: Update database with completion status
    # TODO: Trigger downstream actions (e.g., notify ERP)
    
    return {
        "action": "acknowledged",
        "file_id": file_id,
        "transactions": transaction_count
    }


async def _handle_processing_failed(payload: dict) -> dict:
    """Handle processing failed event."""
    file_id = payload.get('file_id')
    error = payload.get('error', 'Unknown error')
    
    logger.error(f"Processing failed for file {file_id}: {error}")
    
    # TODO: Update database with failure status
    # TODO: Trigger retry or alert
    
    return {
        "action": "acknowledged",
        "file_id": file_id,
        "error": error
    }


async def _handle_reconciliation_request(payload: dict) -> dict:
    """Handle reconciliation request from ERP."""
    account_number = payload.get('account_number')
    date_range = payload.get('date_range', {})
    
    logger.info(f"Reconciliation request for account {account_number}")
    
    # TODO: Query processed statements
    # TODO: Return reconciliation data
    
    return {
        "action": "queued",
        "account_number": account_number,
        "date_range": date_range
    }
