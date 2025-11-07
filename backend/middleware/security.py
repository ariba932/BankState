from fastapi import Request, HTTPException, status
from fastapi.security import APIKeyHeader
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional
import secrets
from utils.exceptions import AuthenticationError, RateLimitError
from utils.logger import get_logger
from config import get_settings
from datetime import datetime, timedelta
from collections import defaultdict

logger = get_logger(__name__)
settings = get_settings()

# API Key security scheme
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # Remove old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security checks and rate limiting."""
    
    async def dispatch(self, request: Request, call_next):
        # Add correlation ID for request tracking
        correlation_id = request.headers.get("X-Correlation-ID", secrets.token_urlsafe(16))
        request.state.correlation_id = correlation_id
        
        # Skip security for health check and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        
        # Rate limiting
        client_ip = request.client.host
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={"correlation_id": correlation_id}
            )
            raise RateLimitError("Too many requests. Please try again later.")
        
        # Process request
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response


async def verify_api_key(api_key: Optional[str] = None) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from header
    
    Returns:
        Verified API key
    
    Raises:
        AuthenticationError: If API key is invalid
    """
    # For development, allow requests without API key
    if settings.api_debug:
        return "dev-key"
    
    if not api_key:
        raise AuthenticationError("API key required")
    
    # TODO: Implement actual API key validation against database
    # For now, accept any non-empty key
    if not api_key or len(api_key) < 10:
        raise AuthenticationError("Invalid API key")
    
    return api_key


def validate_file_size(file_size: int) -> None:
    """
    Validate uploaded file size.
    
    Args:
        file_size: File size in bytes
    
    Raises:
        ValidationError: If file size exceeds limit
    """
    from utils.exceptions import ValidationError
    
    if file_size > settings.max_upload_size:
        raise ValidationError(
            f"File size exceeds maximum allowed size of {settings.max_upload_size / 1048576:.2f}MB",
            details={"file_size": file_size, "max_size": settings.max_upload_size}
        )


def validate_file_extension(filename: str, allowed_extensions: list = None) -> None:
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.xlsx'])
    
    Raises:
        ValidationError: If file extension is not allowed
    """
    from utils.exceptions import ValidationError
    import os
    
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.xls', '.xlsx']
    
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"File type not supported. Allowed types: {', '.join(allowed_extensions)}",
            details={"filename": filename, "extension": ext}
        )
