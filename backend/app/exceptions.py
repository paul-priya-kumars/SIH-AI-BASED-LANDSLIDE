"""
Application-specific exceptions for GeoShield AI.
"""
from typing import Optional, Dict, Any


class GeoShieldException(Exception):
    """Base exception for GeoShield AI application."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ModelNotAvailable(GeoShieldException):
    """Raised when a required ML model is not available for inference."""

    def __init__(
        self,
        model_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{model_type} model is not available for inference"
        error_code = "MODEL_UNAVAILABLE"
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details=details or {"model_type": model_type}
        )


class InferenceError(GeoShieldException):
    """Raised when ML model inference fails."""

    def __init__(
        self,
        model_type: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{model_type} inference failed"
        error_code = "INFERENCE_ERROR"
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details or {"model_type": model_type}
        )


class CacheError(GeoShieldException):
    """Raised when cache operations fail (though cache failures are typically non-fatal)."""

    def __init__(
        self,
        operation: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"Cache {operation} failed"
        error_code = "CACHE_ERROR"
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            details=details or {"operation": operation}
        )


class ServiceUnavailable(GeoShieldException):
    """Raised when a dependent service is unavailable."""

    def __init__(
        self,
        service_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        message = f"{service_name} service is unavailable"
        error_code = "SERVICE_UNAVAILABLE"
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details=details or {"service": service_name}
        )


class ValidationError(GeoShieldException):
    """Raised when input validation fails (though Pydantic handles most validation)."""

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        error_code = "VALIDATION_ERROR"
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details or {}
        )