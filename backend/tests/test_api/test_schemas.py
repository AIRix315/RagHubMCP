"""Tests for API schemas.

Test cases cover:
- TC-SCH-001: ErrorResponse validation
- TC-SCH-002: SuccessResponse validation
- TC-SCH-003: IndexRequest validation
- TC-SCH-004: IndexTaskStatus validation
- TC-SCH-005: SearchRequest validation
- TC-SCH-006: SearchResult validation
- TC-SCH-007: SearchResponse validation
- TC-SCH-008: BenchmarkConfig validation
- TC-SCH-009: BenchmarkRequest validation
- TC-SCH-010: CollectionInfo validation
- TC-SCH-011: Edge cases and boundary conditions
"""

from __future__ import annotations

from datetime import datetime

import pytest
from pydantic import ValidationError

from api.schemas import (
    BenchmarkConfig,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkResult,
    CollectionDeleteResponse,
    CollectionInfo,
    CollectionsListResponse,
    ErrorResponse,
    IndexRequest,
    IndexTaskStatus,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SuccessResponse,
    TaskStatus,
)


class TestErrorResponse:
    """Tests for ErrorResponse model (TC-SCH-001)."""

    def test_minimal_error(self) -> None:
        """Test minimal error response."""
        error = ErrorResponse(error="NotFoundError", message="Resource not found")

        assert error.error == "NotFoundError"
        assert error.message == "Resource not found"
        assert error.detail is None

    def test_error_with_detail(self) -> None:
        """Test error response with detail."""
        error = ErrorResponse(
            error="ValidationError",
            message="Invalid input",
            detail={"field": "email", "reason": "invalid format"},
        )

        assert error.error == "ValidationError"
        assert error.detail == {"field": "email", "reason": "invalid format"}

    def test_error_serialization(self) -> None:
        """Test error response serialization."""
        error = ErrorResponse(
            error="TypeError",
            message="Expected string",
            detail={"expected": "str", "received": "int"},
        )

        data = error.model_dump()

        assert data["error"] == "TypeError"
        assert data["message"] == "Expected string"
        assert data["detail"]["expected"] == "str"

    def test_error_required_fields(self) -> None:
        """Test that error and message are required."""
        with pytest.raises(ValidationError):
            ErrorResponse()

        with pytest.raises(ValidationError):
            ErrorResponse(error="Error")


class TestSuccessResponse:
    """Tests for SuccessResponse model (TC-SCH-002)."""

    def test_success_default_status(self) -> None:
        """Test default status value."""
        response = SuccessResponse(message="Operation completed")

        assert response.status == "success"
        assert response.message == "Operation completed"

    def test_success_custom_status(self) -> None:
        """Test custom status value."""
        response = SuccessResponse(status="accepted", message="Request accepted")

        assert response.status == "accepted"


class TestIndexRequest:
    """Tests for IndexRequest model (TC-SCH-003)."""

    def test_index_request_minimal(self) -> None:
        """Test minimal index request."""
        request = IndexRequest(path="/data/docs")

        assert request.path == "/data/docs"
        assert request.collection_name == "default"
        assert request.recursive is True

    def test_index_request_full(self) -> None:
        """Test full index request with all fields."""
        request = IndexRequest(
            path="/data/docs",
            collection_name="my_collection",
            embedding_provider="ollama",
            chunk_size=512,
            chunk_overlap=64,
            recursive=False,
        )

        assert request.path == "/data/docs"
        assert request.collection_name == "my_collection"
        assert request.embedding_provider == "ollama"
        assert request.chunk_size == 512
        assert request.chunk_overlap == 64
        assert request.recursive is False

    def test_index_request_path_required(self) -> None:
        """Test that path is required."""
        with pytest.raises(ValidationError):
            IndexRequest()

    def test_index_request_serialization(self) -> None:
        """Test index request serialization."""
        request = IndexRequest(path="/test")
        data = request.model_dump()

        assert "path" in data
        assert data["path"] == "/test"


class TestIndexTaskStatus:
    """Tests for IndexTaskStatus model (TC-SCH-004)."""

    def test_task_status_minimal(self) -> None:
        """Test minimal task status."""
        now = datetime.now()
        status = IndexTaskStatus(
            task_id="task-123",
            status=TaskStatus.PENDING,
            created_at=now,
        )

        assert status.task_id == "task-123"
        assert status.status == TaskStatus.PENDING
        assert status.progress == 0.0
        assert status.created_at == now
        assert status.completed_at is None

    def test_task_status_full(self) -> None:
        """Test full task status."""
        created = datetime.now()
        completed = datetime.now()
        status = IndexTaskStatus(
            task_id="task-456",
            status=TaskStatus.COMPLETED,
            progress=1.0,
            message="All files processed",
            total_files=100,
            processed_files=100,
            total_chunks=500,
            created_at=created,
            completed_at=completed,
        )

        assert status.progress == 1.0
        assert status.total_files == 100
        assert status.processed_files == 100
        assert status.total_chunks == 500
        assert status.completed_at == completed

    def test_task_status_progress_range(self) -> None:
        """Test progress value range validation."""
        now = datetime.now()

        # Valid values
        status = IndexTaskStatus(
            task_id="task-1",
            status=TaskStatus.RUNNING,
            progress=0.5,
            created_at=now,
        )
        assert status.progress == 0.5

        # Boundary values
        status = IndexTaskStatus(
            task_id="task-2",
            status=TaskStatus.RUNNING,
            progress=0.0,
            created_at=now,
        )
        assert status.progress == 0.0

        status = IndexTaskStatus(
            task_id="task-3",
            status=TaskStatus.COMPLETED,
            progress=1.0,
            created_at=now,
        )
        assert status.progress == 1.0

    def test_task_status_invalid_progress(self) -> None:
        """Test that invalid progress raises validation error."""
        now = datetime.now()

        with pytest.raises(ValidationError):
            IndexTaskStatus(
                task_id="task-1",
                status=TaskStatus.RUNNING,
                progress=1.5,  # > 1.0
                created_at=now,
            )

        with pytest.raises(ValidationError):
            IndexTaskStatus(
                task_id="task-2",
                status=TaskStatus.RUNNING,
                progress=-0.1,  # < 0.0
                created_at=now,
            )


class TestSearchRequest:
    """Tests for SearchRequest model (TC-SCH-005)."""

    def test_search_request_minimal(self) -> None:
        """Test minimal search request."""
        request = SearchRequest(query="machine learning")

        assert request.query == "machine learning"
        assert request.collection_name == "default"
        assert request.top_k == 5
        assert request.use_rerank is True

    def test_search_request_full(self) -> None:
        """Test full search request."""
        request = SearchRequest(
            query="test query",
            collection_name="my_collection",
            top_k=20,
            embedding_provider="openai",
            rerank_provider="flashrank",
            use_rerank=False,
        )

        assert request.query == "test query"
        assert request.collection_name == "my_collection"
        assert request.top_k == 20
        assert request.embedding_provider == "openai"
        assert request.rerank_provider == "flashrank"
        assert request.use_rerank is False

    def test_search_request_top_k_range(self) -> None:
        """Test top_k range validation."""
        request = SearchRequest(query="test", top_k=1)
        assert request.top_k == 1

        request = SearchRequest(query="test", top_k=100)
        assert request.top_k == 100

    def test_search_request_invalid_top_k(self) -> None:
        """Test that invalid top_k raises validation error."""
        with pytest.raises(ValidationError):
            SearchRequest(query="test", top_k=0)  # < 1

        with pytest.raises(ValidationError):
            SearchRequest(query="test", top_k=101)  # > 100

    def test_search_request_query_required(self) -> None:
        """Test that query is required."""
        with pytest.raises(ValidationError):
            SearchRequest()


class TestSearchResult:
    """Tests for SearchResult model (TC-SCH-006)."""

    def test_search_result_minimal(self) -> None:
        """Test minimal search result."""
        result = SearchResult(id="doc-1", text="Document content", score=0.95)

        assert result.id == "doc-1"
        assert result.text == "Document content"
        assert result.score == 0.95
        assert result.metadata == {}
        assert result.rerank_score is None

    def test_search_result_full(self) -> None:
        """Test full search result."""
        result = SearchResult(
            id="doc-2",
            text="Another document",
            score=0.75,
            metadata={"source": "file.py", "language": "python"},
            rerank_score=0.92,
        )

        assert result.metadata["source"] == "file.py"
        assert result.rerank_score == 0.92

    def test_search_result_serialization(self) -> None:
        """Test search result serialization."""
        result = SearchResult(
            id="doc-3",
            text="Text",
            score=0.8,
            metadata={"key": "value"},
        )

        data = result.model_dump()

        assert data["id"] == "doc-3"
        assert "metadata" in data


class TestSearchResponse:
    """Tests for SearchResponse model (TC-SCH-007)."""

    def test_search_response_minimal(self) -> None:
        """Test minimal search response."""
        response = SearchResponse(
            query="test",
            results=[],
            total=0,
            collection="default",
            embedding_provider="ollama",
        )

        assert response.query == "test"
        assert response.results == []
        assert response.total == 0

    def test_search_response_with_results(self) -> None:
        """Test search response with results."""
        results = [
            SearchResult(id="1", text="doc1", score=0.9),
            SearchResult(id="2", text="doc2", score=0.8),
        ]

        response = SearchResponse(
            query="test",
            results=results,
            total=2,
            collection="test_collection",
            embedding_provider="openai",
            rerank_provider="flashrank",
        )

        assert len(response.results) == 2
        assert response.rerank_provider == "flashrank"


class TestBenchmarkConfig:
    """Tests for BenchmarkConfig model (TC-SCH-008)."""

    def test_benchmark_config_minimal(self) -> None:
        """Test minimal benchmark config."""
        config = BenchmarkConfig(
            name="test-config",
            embedding_provider="ollama",
        )

        assert config.name == "test-config"
        assert config.embedding_provider == "ollama"
        assert config.rerank_provider is None
        assert config.top_k == 5

    def test_benchmark_config_full(self) -> None:
        """Test full benchmark config."""
        config = BenchmarkConfig(
            name="high-accuracy",
            embedding_provider="openai",
            rerank_provider="flashrank",
            top_k=20,
        )

        assert config.rerank_provider == "flashrank"
        assert config.top_k == 20

    def test_benchmark_config_required_fields(self) -> None:
        """Test that name and embedding_provider are required."""
        with pytest.raises(ValidationError):
            BenchmarkConfig()

        with pytest.raises(ValidationError):
            BenchmarkConfig(name="test")


class TestBenchmarkRequest:
    """Tests for BenchmarkRequest model (TC-SCH-009)."""

    def test_benchmark_request_minimal(self) -> None:
        """Test minimal benchmark request."""
        configs = [BenchmarkConfig(name="cfg1", embedding_provider="ollama")]
        request = BenchmarkRequest(query="test query", configs=configs)

        assert request.query == "test query"
        assert len(request.configs) == 1
        assert request.collection_name == "default"

    def test_benchmark_request_multiple_configs(self) -> None:
        """Test benchmark request with multiple configs."""
        configs = [
            BenchmarkConfig(name="cfg1", embedding_provider="ollama"),
            BenchmarkConfig(name="cfg2", embedding_provider="openai"),
        ]
        request = BenchmarkRequest(
            query="test",
            configs=configs,
            collection_name="my_collection",
        )

        assert len(request.configs) == 2

    def test_benchmark_request_configs_required(self) -> None:
        """Test that configs is required and non-empty."""
        with pytest.raises(ValidationError):
            BenchmarkRequest(query="test")

        with pytest.raises(ValidationError):
            BenchmarkRequest(query="test", configs=[])


class TestBenchmarkResult:
    """Tests for BenchmarkResult model."""

    def test_benchmark_result(self) -> None:
        """Test benchmark result."""
        results = [
            SearchResult(id="1", text="doc1", score=0.9),
        ]
        benchmark = BenchmarkResult(
            config_name="test-config",
            results=results,
            latency_ms=150.5,
            embedding_provider="ollama",
        )

        assert benchmark.config_name == "test-config"
        assert benchmark.latency_ms == 150.5
        assert len(benchmark.results) == 1


class TestBenchmarkResponse:
    """Tests for BenchmarkResponse model."""

    def test_benchmark_response(self) -> None:
        """Test benchmark response."""
        config = BenchmarkConfig(name="cfg", embedding_provider="test")
        request = BenchmarkRequest(query="test", configs=[config])

        result = BenchmarkResult(
            config_name="cfg",
            results=[],
            latency_ms=100.0,
            embedding_provider="test",
        )

        response = BenchmarkResponse(
            query="test",
            collection="default",
            results=[result],
            total_latency_ms=150.0,
        )

        assert response.query == "test"
        assert len(response.results) == 1


class TestCollectionModels:
    """Tests for Collection models (TC-SCH-010)."""

    def test_collection_info_minimal(self) -> None:
        """Test minimal collection info."""
        info = CollectionInfo(name="my_collection", count=100)

        assert info.name == "my_collection"
        assert info.count == 100
        assert info.metadata == {}

    def test_collection_info_full(self) -> None:
        """Test full collection info."""
        info = CollectionInfo(
            name="test_collection",
            count=500,
            metadata={"created": "2024-01-01", "type": "docs"},
        )

        assert info.metadata["created"] == "2024-01-01"

    def test_collections_list_response(self) -> None:
        """Test collections list response."""
        collections = [
            CollectionInfo(name="col1", count=10),
            CollectionInfo(name="col2", count=20),
        ]

        response = CollectionsListResponse(collections=collections, total=2)

        assert len(response.collections) == 2
        assert response.total == 2

    def test_collection_delete_response(self) -> None:
        """Test collection delete response."""
        response = CollectionDeleteResponse(name="deleted_collection")

        assert response.name == "deleted_collection"
        assert response.message == "Collection deleted successfully"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions (TC-SCH-011)."""

    def test_empty_query(self) -> None:
        """Test empty query string."""
        # Empty string is allowed by default
        request = SearchRequest(query="")
        assert request.query == ""

    def test_special_characters_in_path(self) -> None:
        """Test path with special characters."""
        request = IndexRequest(path="/data/test folder/docs")
        assert request.path == "/data/test folder/docs"

    def test_unicode_in_query(self) -> None:
        """Test unicode characters in query."""
        request = SearchRequest(query="中文查询")
        assert request.query == "中文查询"

    def test_very_long_query(self) -> None:
        """Test very long query string."""
        long_query = "test " * 1000
        request = SearchRequest(query=long_query)
        assert len(request.query) == 5000

    def test_metadata_with_nested_data(self) -> None:
        """Test metadata with nested data structures."""
        metadata = {
            "source": "test.py",
            "nested": {"key": "value"},
            "list": [1, 2, 3],
        }
        result = SearchResult(
            id="1",
            text="doc",
            score=0.5,
            metadata=metadata,
        )

        assert result.metadata["nested"]["key"] == "value"
        assert result.metadata["list"] == [1, 2, 3]

    def test_search_result_with_special_score(self) -> None:
        """Test search result with boundary scores."""
        # Score at boundaries
        result = SearchResult(id="1", text="doc", score=0.0)
        assert result.score == 0.0

        result = SearchResult(id="2", text="doc", score=1.0)
        assert result.score == 1.0

    def test_task_status_enum_values(self) -> None:
        """Test TaskStatus enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"

    def test_index_request_chunk_size_types(self) -> None:
        """Test chunk size can be None or int."""
        # None is valid
        request = IndexRequest(path="/test", chunk_size=None)
        assert request.chunk_size is None

        # Integer is valid
        request = IndexRequest(path="/test", chunk_size=1024)
        assert request.chunk_size == 1024


class TestModelSerialization:
    """Tests for model serialization/deserialization."""

    def test_json_serialization(self) -> None:
        """Test JSON serialization roundtrip."""
        request = SearchRequest(
            query="test",
            collection_name="my_collection",
            top_k=10,
        )

        json_str = request.model_dump_json()
        request_copy = SearchRequest.model_validate_json(json_str)

        assert request_copy.query == request.query
        assert request_copy.collection_name == request.collection_name
        assert request_copy.top_k == request.top_k

    def test_dict_conversion(self) -> None:
        """Test dict conversion."""
        error = ErrorResponse(
            error="TestError",
            message="Test message",
            detail={"key": "value"},
        )

        data = error.model_dump()

        assert isinstance(data, dict)
        assert data["error"] == "TestError"
        assert data["detail"]["key"] == "value"

    def test_model_copy(self) -> None:
        """Test model copy."""
        config = BenchmarkConfig(
            name="original",
            embedding_provider="ollama",
            top_k=10,
        )

        config_copy = config.model_copy(update={"top_k": 20})

        assert config.top_k == 10  # Original unchanged
        assert config_copy.top_k == 20
