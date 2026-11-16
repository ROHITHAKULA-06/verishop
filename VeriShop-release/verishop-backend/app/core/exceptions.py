"""
VeriShop Custom Exceptions
Structured exception hierarchy with HTTP status codes.
"""


class VeriShopError(Exception):
    """Base exception for all VeriShop errors."""

    def __init__(self, message: str = "An error occurred", detail: str = "", status_code: int = 500):
        self.message = message
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.message)


class ModelNotLoadedError(VeriShopError):
    """Raised when a required ML model is not loaded."""

    def __init__(self, message: str = "Model not loaded", detail: str = ""):
        super().__init__(message, detail, status_code=503)


class InvalidQueryError(VeriShopError):
    """Raised when a search query is invalid."""

    def __init__(self, message: str = "Invalid query", detail: str = ""):
        super().__init__(message, detail, status_code=400)


class ProcessingError(VeriShopError):
    """Raised when processing pipeline fails."""

    def __init__(self, message: str = "Processing error", detail: str = ""):
        super().__init__(message, detail, status_code=500)


class StorageError(VeriShopError):
    """Raised when storage operations fail."""

    def __init__(self, message: str = "Storage error", detail: str = ""):
        super().__init__(message, detail, status_code=500)


class ExternalServiceError(VeriShopError):
    """Raised when an external service call fails."""

    def __init__(self, message: str = "External service error", detail: str = ""):
        super().__init__(message, detail, status_code=502)
