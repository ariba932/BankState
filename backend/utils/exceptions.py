"""Custom exceptions for the application."""


class BankStateException(Exception):
    """Base exception for all application errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(BankStateException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)


class FileProcessingError(BankStateException):
    """Raised when file processing fails."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)


class ExtractionError(BankStateException):
    """Raised when data extraction fails."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)


class MappingError(BankStateException):
    """Raised when data mapping fails."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=422, details=details)


class IntegrationError(BankStateException):
    """Raised when external integration fails."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=502, details=details)


class AuthenticationError(BankStateException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(message, status_code=401, details=details)


class AuthorizationError(BankStateException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied", details: dict = None):
        super().__init__(message, status_code=403, details=details)


class NotFoundError(BankStateException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=404, details=details)


class RateLimitError(BankStateException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: dict = None):
        super().__init__(message, status_code=429, details=details)
