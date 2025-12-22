"""Custom exceptions for ZAS."""

from typing import Optional


class ZASException(Exception):
    """Base exception for all ZAS errors."""
    pass


class ConfigurationException(ZASException):
    """Raised when configuration is invalid or missing."""
    pass


class APIException(ZASException):
    """Raised when an API call fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ValidationException(ZASException):
    """Raised when input validation fails."""
    pass


from typing import Optional
