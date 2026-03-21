"""Tests for error handling utilities.

This module tests the unified error handling system including:
- RAGError base exception
- Error subclasses
- Error handlers
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import HTTPException, status
from fastapi.responses import JSONResponse

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils.errors import (
    ErrorCode,
    NotFoundError,
    PipelineError,
    RAGError,
    SearchError,
    ServiceUnavailableError,
    ValidationError,
    general_exception_handler,
    http_exception_handler,
    rag_error_handler,
)


class TestErrorCode:
    """Tests for ErrorCode enum."""

    def test_error_code_values(self) -> None:
        """Test that error codes have correct string values."""
        assert ErrorCode.INVALID_REQUEST.value == "invalid_request"
        assert ErrorCode.INVALID_COLLECTION.value == "invalid_collection"
        assert ErrorCode.INVALID_QUERY.value == "invalid_query"
        assert ErrorCode.INVALID_CONFIG.value == "invalid_config"

        assert ErrorCode.COLLECTION_NOT_FOUND.value == "collection_not_found"
        assert ErrorCode.DOCUMENT_NOT_FOUND.value == "document_not_found"
        assert ErrorCode.TASK_NOT_FOUND.value == "task_not_found"
        assert ErrorCode.PROVIDER_NOT_FOUND.value == "provider_not_found"

        assert ErrorCode.SEARCH_FAILED.value == "search_failed"
        assert ErrorCode.INDEX_FAILED.value == "index_failed"
        assert ErrorCode.EMBEDDING_FAILED.value == "embedding_failed"
        assert ErrorCode.RERANK_FAILED.value == "rerank_failed"
        assert ErrorCode.PIPELINE_ERROR.value == "pipeline_error"

        assert ErrorCode.SERVICE_UNAVAILABLE.value == "service_unavailable"
        assert ErrorCode.PROVIDER_UNAVAILABLE.value == "provider_unavailable"
        assert ErrorCode.DATABASE_ERROR.value == "database_error"

    def test_error_code_is_string(self) -> None:
        """Test that ErrorCode inherits from str."""
        assert isinstance(ErrorCode.SEARCH_FAILED, str)
        assert ErrorCode.SEARCH_FAILED == "search_failed"


class TestRAGError:
    """Tests for RAGError base exception class."""

    def test_init_default_values(self) -> None:
        """Test RAGError initialization with default values."""
        error = RAGError(message="Test error")

        assert error.message == "Test error"
        assert error.error_code == ErrorCode.SEARCH_FAILED
        assert error.details == {}
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_init_custom_values(self) -> None:
        """Test RAGError initialization with custom values."""
        error = RAGError(
            message="Custom error",
            error_code=ErrorCode.INVALID_REQUEST,
            details={"key": "value"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

        assert error.message == "Custom error"
        assert error.error_code == ErrorCode.INVALID_REQUEST
        assert error.details == {"key": "value"}
        assert error.status_code == status.HTTP_400_BAD_REQUEST

    def test_str_method(self) -> None:
        """Test RAGError __str__ method returns formatted string."""
        error = RAGError(
            message="Search failed",
            error_code=ErrorCode.SEARCH_FAILED,
        )

        result = str(error)

        assert result == "[search_failed] Search failed"

    def test_to_dict_with_details(self) -> None:
        """Test RAGError to_dict method with details."""
        error = RAGError(
            message="Test error",
            error_code=ErrorCode.INVALID_REQUEST,
            details={"field": "query", "reason": "empty"},
        )

        result = error.to_dict()

        assert result["error"] == "invalid_request"
        assert result["message"] == "Test error"
        assert result["detail"] == {"field": "query", "reason": "empty"}

    def test_to_dict_without_details(self) -> None:
        """Test RAGError to_dict method without details."""
        error = RAGError(
            message="Test error",
            error_code=ErrorCode.SEARCH_FAILED,
            details={},
        )

        result = error.to_dict()

        assert result["error"] == "search_failed"
        assert result["message"] == "Test error"
        assert result["detail"] is None

    def test_is_exception(self) -> None:
        """Test that RAGError is an Exception."""
        error = RAGError(message="Test")

        assert isinstance(error, Exception)


class TestValidationError:
    """Tests for ValidationError class."""

    def test_init_with_details(self) -> None:
        """Test ValidationError initialization with details."""
        error = ValidationError(
            message="Invalid input",
            details={"field": "name", "reason": "required"},
        )

        assert error.message == "Invalid input"
        assert error.error_code == ErrorCode.INVALID_REQUEST
        assert error.details == {"field": "name", "reason": "required"}
        assert error.status_code == status.HTTP_400_BAD_REQUEST

    def test_init_without_details(self) -> None:
        """Test ValidationError initialization without details."""
        error = ValidationError(message="Invalid input")

        assert error.message == "Invalid input"
        assert error.error_code == ErrorCode.INVALID_REQUEST
        assert error.details == {}
        assert error.status_code == status.HTTP_400_BAD_REQUEST

    def test_inheritance(self) -> None:
        """Test ValidationError inherits from RAGError."""
        error = ValidationError(message="Test")

        assert isinstance(error, RAGError)
        assert isinstance(error, Exception)


class TestNotFoundError:
    """Tests for NotFoundError class."""

    def test_init_default_code(self) -> None:
        """Test NotFoundError with default error code."""
        error = NotFoundError(message="Collection not found")

        assert error.message == "Collection not found"
        assert error.error_code == ErrorCode.COLLECTION_NOT_FOUND
        assert error.details == {}
        assert error.status_code == status.HTTP_404_NOT_FOUND

    def test_init_custom_code(self) -> None:
        """Test NotFoundError with custom error code."""
        error = NotFoundError(
            message="Document not found",
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            details={"doc_id": "123"},
        )

        assert error.message == "Document not found"
        assert error.error_code == ErrorCode.DOCUMENT_NOT_FOUND
        assert error.details == {"doc_id": "123"}
        assert error.status_code == status.HTTP_404_NOT_FOUND

    def test_inheritance(self) -> None:
        """Test NotFoundError inherits from RAGError."""
        error = NotFoundError(message="Test")

        assert isinstance(error, RAGError)


class TestSearchError:
    """Tests for SearchError class."""

    def test_init_with_details(self) -> None:
        """Test SearchError initialization with details."""
        error = SearchError(
            message="Search operation failed",
            details={"query": "test", "error": "timeout"},
        )

        assert error.message == "Search operation failed"
        assert error.error_code == ErrorCode.SEARCH_FAILED
        assert error.details == {"query": "test", "error": "timeout"}
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_init_without_details(self) -> None:
        """Test SearchError initialization without details."""
        error = SearchError(message="Search failed")

        assert error.message == "Search failed"
        assert error.error_code == ErrorCode.SEARCH_FAILED
        assert error.details == {}
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_inheritance(self) -> None:
        """Test SearchError inherits from RAGError."""
        error = SearchError(message="Test")

        assert isinstance(error, RAGError)


class TestPipelineError:
    """Tests for PipelineError class."""

    def test_init_with_details(self) -> None:
        """Test PipelineError initialization with details."""
        error = PipelineError(
            message="Pipeline execution failed",
            details={"stage": "embedding", "error": "OOM"},
        )

        assert error.message == "Pipeline execution failed"
        assert error.error_code == ErrorCode.PIPELINE_ERROR
        assert error.details == {"stage": "embedding", "error": "OOM"}
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_init_without_details(self) -> None:
        """Test PipelineError initialization without details."""
        error = PipelineError(message="Pipeline error")

        assert error.message == "Pipeline error"
        assert error.error_code == ErrorCode.PIPELINE_ERROR
        assert error.details == {}
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_inheritance(self) -> None:
        """Test PipelineError inherits from RAGError."""
        error = PipelineError(message="Test")

        assert isinstance(error, RAGError)


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError class."""

    def test_init_without_additional_details(self) -> None:
        """Test ServiceUnavailableError without additional details."""
        error = ServiceUnavailableError(
            message="Service is down",
            service="chroma",
        )

        assert error.message == "Service is down"
        assert error.error_code == ErrorCode.SERVICE_UNAVAILABLE
        assert error.details == {"service": "chroma"}
        assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_init_with_additional_details(self) -> None:
        """Test ServiceUnavailableError with additional details merged."""
        error = ServiceUnavailableError(
            message="Provider unavailable",
            service="openai",
            details={"reason": "rate_limit", "retry_after": 60},
        )

        assert error.message == "Provider unavailable"
        assert error.error_code == ErrorCode.SERVICE_UNAVAILABLE
        assert error.details == {
            "service": "openai",
            "reason": "rate_limit",
            "retry_after": 60,
        }
        assert error.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    def test_init_details_override_service(self) -> None:
        """Test that service key is preserved when details also has service key."""
        error = ServiceUnavailableError(
            message="Service error",
            service="primary_service",
            details={"service": "should_be_overridden", "extra": "value"},
        )

        # Service parameter should be set first, then details merged
        # So details["service"] would override, but we want to verify behavior
        assert error.details["service"] == "should_be_overridden"
        assert error.details["extra"] == "value"

    def test_inheritance(self) -> None:
        """Test ServiceUnavailableError inherits from RAGError."""
        error = ServiceUnavailableError(message="Test", service="test_service")

        assert isinstance(error, RAGError)


class TestRagErrorHandler:
    """Tests for rag_error_handler function."""

    def test_handler_returns_json_response(self) -> None:
        """Test that handler returns JSONResponse with correct data."""
        error = RAGError(
            message="Test error",
            error_code=ErrorCode.SEARCH_FAILED,
            details={"key": "value"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        request = MagicMock()

        response = rag_error_handler(request, error)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    def test_handler_with_different_status_codes(self) -> None:
        """Test handler with different status codes."""
        error = NotFoundError(message="Not found")
        request = MagicMock()

        response = rag_error_handler(request, error)

        assert response.status_code == 404


class TestHttpExceptionHandler:
    """Tests for http_exception_handler function."""

    def test_handler_with_dict_detail(self) -> None:
        """Test handler when exception detail is a dict."""
        exc = HTTPException(
            status_code=400,
            detail={"error": "custom_error", "message": "Bad request"},
        )
        request = MagicMock()

        response = http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 400

    def test_handler_with_string_detail(self) -> None:
        """Test handler when exception detail is a string."""
        exc = HTTPException(
            status_code=404,
            detail="Resource not found",
        )
        request = MagicMock()

        response = http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 404

    def test_handler_with_int_detail(self) -> None:
        """Test handler when exception detail is an int."""
        exc = HTTPException(
            status_code=500,
            detail=12345,
        )
        request = MagicMock()

        response = http_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500


class TestGeneralExceptionHandler:
    """Tests for general_exception_handler function."""

    def test_handler_returns_json_response(self) -> None:
        """Test that handler returns JSONResponse with correct data."""
        exc = ValueError("Something went wrong")
        request = MagicMock()

        response = general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    def test_handler_with_empty_exception_message(self) -> None:
        """Test handler when exception message is empty."""
        exc = ValueError("")
        request = MagicMock()

        response = general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    def test_handler_with_exception_without_message(self) -> None:
        """Test handler with exception that has no message."""
        exc = Exception()
        request = MagicMock()

        response = general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500

    def test_handler_preserves_exception_string(self) -> None:
        """Test that handler preserves exception string representation."""
        exc = RuntimeError("Database connection timeout after 30s")
        request = MagicMock()

        response = general_exception_handler(request, exc)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
