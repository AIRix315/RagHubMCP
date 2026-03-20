"""Unified error handling for RagHubMCP.

This module provides a unified error handling system:
- RAGError: Base exception class for all RAG-related errors
- Error handling middleware for FastAPI
- Unified error response format

Reference:
- Docs/11-V2-Desing.md (Section 5)
- Docs/12-V2-Blueprint.md (Module 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ErrorCode(str, Enum):
    """Standardized error codes for RAG operations."""
    
    # Validation errors (400)
    INVALID_REQUEST = "invalid_request"
    INVALID_COLLECTION = "invalid_collection"
    INVALID_QUERY = "invalid_query"
    INVALID_CONFIG = "invalid_config"
    
    # Not found errors (404)
    COLLECTION_NOT_FOUND = "collection_not_found"
    DOCUMENT_NOT_FOUND = "document_not_found"
    TASK_NOT_FOUND = "task_not_found"
    PROVIDER_NOT_FOUND = "provider_not_found"
    
    # Operation errors (500)
    SEARCH_FAILED = "search_failed"
    INDEX_FAILED = "index_failed"
    EMBEDDING_FAILED = "embedding_failed"
    RERANK_FAILED = "rerank_failed"
    PIPELINE_ERROR = "pipeline_error"
    
    # Service errors (503)
    SERVICE_UNAVAILABLE = "service_unavailable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    DATABASE_ERROR = "database_error"


@dataclass
class RAGError(Exception):
    """Base exception class for RAG-related errors.
    
    Provides structured error information for consistent error handling
    across the application.
    
    Attributes:
        message: Human-readable error description
        error_code: Machine-readable error code
        details: Additional context as a dictionary
        status_code: HTTP status code for API responses
    """
    message: str
    error_code: ErrorCode = ErrorCode.SEARCH_FAILED
    details: dict[str, Any] = field(default_factory=dict)
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for API response."""
        return {
            "error": self.error_code.value,
            "message": self.message,
            "detail": self.details if self.details else None,
        }


class ValidationError(RAGError):
    """Raised for request validation errors."""
    
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_REQUEST,
            details=details or {},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotFoundError(RAGError):
    """Raised when a resource is not found."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.COLLECTION_NOT_FOUND,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details or {},
            status_code=status.HTTP_404_NOT_FOUND,
        )


class SearchError(RAGError):
    """Raised when search operation fails."""
    
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.SEARCH_FAILED,
            details=details or {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class PipelineError(RAGError):
    """Raised when pipeline execution fails."""
    
    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            error_code=ErrorCode.PIPELINE_ERROR,
            details=details or {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ServiceUnavailableError(RAGError):
    """Raised when a service is unavailable."""
    
    def __init__(
        self,
        message: str,
        service: str,
        details: dict[str, Any] | None = None,
    ):
        error_details = {"service": service}
        if details:
            error_details.update(details)
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            details=error_details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


def rag_error_handler(request: Request, exc: RAGError) -> JSONResponse:
    """Handle RAGError exceptions and return JSON response.
    
    Args:
        request: The FastAPI request object.
        exc: The RAGError exception.
        
    Returns:
        JSONResponse with error details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException and return unified JSON response.
    
    Args:
        request: The FastAPI request object.
        exc: The HTTPException.
        
    Returns:
        JSONResponse with error details.
    """
    # If detail is already a dict, use it directly
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {
            "error": "http_error",
            "message": str(exc.detail),
            "detail": None,
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions and return JSON response.
    
    Args:
        request: The FastAPI request object.
        exc: The exception.
        
    Returns:
        JSONResponse with error details.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if str(exc) else None,
        },
    )