"""Error response schemas for API."""

from enum import Enum

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Error codes for API responses."""

    INVALID_ID_FORMAT = "INVALID_ID_FORMAT"
    CONVERSATION_NOT_FOUND = "CONVERSATION_NOT_FOUND"
    ACCESS_DENIED = "ACCESS_DENIED"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    """Error detail structure."""

    code: ErrorCode
    message: str


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    error: ErrorDetail
