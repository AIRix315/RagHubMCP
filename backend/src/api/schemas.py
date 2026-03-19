"""Pydantic models for REST API request/response schemas.

This module defines all the data models used by the REST API endpoints.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# =============================================================================
# Common Response Models
# =============================================================================


class ErrorResponse(BaseModel):
    """Standard error response format.

    All API errors should return this format for consistency.
    """

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: dict[str, Any] | None = Field(default=None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response format."""

    status: str = Field(default="success", description="Response status")
    message: str = Field(..., description="Human-readable message")


# =============================================================================
# Config API Models
# =============================================================================


class ServerConfigModel(BaseModel):
    """Server configuration."""

    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    debug: bool = Field(default=True)


class ChromaConfigModel(BaseModel):
    """Chroma configuration."""

    persist_dir: str = Field(default="./data/chroma")
    host: str | None = Field(default=None)
    port: int | None = Field(default=None)


class ProviderInstanceModel(BaseModel):
    """Provider instance configuration."""

    name: str
    type: str
    model: str
    base_url: str | None = Field(default=None)
    dimension: int | None = Field(default=None)


class ProviderCategoryModel(BaseModel):
    """Provider category configuration."""

    default: str
    instances: list[dict[str, Any]] = Field(default_factory=list)


class ProvidersConfigModel(BaseModel):
    """All provider configurations."""

    embedding: ProviderCategoryModel
    rerank: ProviderCategoryModel
    llm: ProviderCategoryModel


class IndexerConfigModel(BaseModel):
    """Indexer configuration."""

    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)
    max_file_size: int = Field(default=1048576)
    file_types: list[str] = Field(default_factory=lambda: [".py", ".ts", ".js", ".md", ".vue"])
    exclude_dirs: list[str] = Field(
        default_factory=lambda: ["node_modules", ".git", "__pycache__", "venv"]
    )


class LoggingConfigModel(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file: str | None = Field(default=None)


class ConfigModel(BaseModel):
    """Full configuration model."""

    server: ServerConfigModel
    chroma: ChromaConfigModel
    providers: ProvidersConfigModel
    indexer: IndexerConfigModel
    logging: LoggingConfigModel


class ConfigUpdateRequest(BaseModel):
    """Request body for updating configuration.

    Only include the fields you want to update.
    """

    server: ServerConfigModel | None = None
    chroma: ChromaConfigModel | None = None
    providers: ProvidersConfigModel | None = None
    indexer: IndexerConfigModel | None = None
    logging: LoggingConfigModel | None = None


# =============================================================================
# Index API Models
# =============================================================================


class TaskStatus(str, Enum):
    """Index task status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IndexRequest(BaseModel):
    """Request to start an indexing task."""

    path: str = Field(..., description="Directory or file path to index")
    collection_name: str = Field(default="default", description="Chroma collection name")
    embedding_provider: str | None = Field(default=None, description="Embedding provider name")
    chunk_size: int | None = Field(default=None, description="Override chunk size")
    chunk_overlap: int | None = Field(default=None, description="Override chunk overlap")
    recursive: bool = Field(default=True, description="Scan directories recursively")


class IndexTaskStatus(BaseModel):
    """Status of an indexing task."""

    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress (0.0 - 1.0)")
    message: str = Field(default="", description="Status message")
    total_files: int = Field(default=0, description="Total files to process")
    processed_files: int = Field(default=0, description="Files processed so far")
    total_chunks: int = Field(default=0, description="Total chunks created")
    created_at: datetime = Field(..., description="Task creation time")
    completed_at: datetime | None = Field(default=None, description="Task completion time")
    error: str | None = Field(default=None, description="Error message if failed")


class IndexResponse(BaseModel):
    """Response after starting an indexing task."""

    task_id: str = Field(..., description="Unique task identifier")
    message: str = Field(default="Indexing task started")
    status_url: str = Field(..., description="URL to check task status")


# =============================================================================
# Search API Models
# =============================================================================


class SearchRequest(BaseModel):
    """Request to perform a search."""

    query: str = Field(..., description="Search query text")
    collection_name: str = Field(default="default", description="Collection to search")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results")
    embedding_provider: str | None = Field(default=None, description="Embedding provider")
    rerank_provider: str | None = Field(default=None, description="Rerank provider")
    use_rerank: bool = Field(default=True, description="Whether to use reranking")


class SearchResult(BaseModel):
    """Single search result."""

    id: str = Field(..., description="Document ID")
    text: str = Field(..., description="Document text content")
    score: float = Field(..., description="Relevance score")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    rerank_score: float | None = Field(default=None, description="Rerank score if reranked")


class SearchResponse(BaseModel):
    """Response from a search query."""

    query: str = Field(..., description="Original query")
    results: list[SearchResult] = Field(default_factory=list, description="Search results")
    total: int = Field(..., description="Total results found")
    collection: str = Field(..., description="Collection searched")
    embedding_provider: str = Field(..., description="Embedding provider used")
    rerank_provider: str | None = Field(default=None, description="Rerank provider used")


# =============================================================================
# Benchmark API Models
# =============================================================================


class BenchmarkConfig(BaseModel):
    """Configuration for a single benchmark run."""

    name: str = Field(..., description="Configuration name/identifier")
    embedding_provider: str = Field(..., description="Embedding provider to use")
    rerank_provider: str | None = Field(default=None, description="Rerank provider to use")
    top_k: int = Field(default=5, description="Number of results")


class BenchmarkRequest(BaseModel):
    """Request to run a benchmark comparison."""

    query: str = Field(..., description="Test query")
    collection_name: str = Field(default="default", description="Collection to search")
    configs: list[BenchmarkConfig] = Field(
        ..., min_length=1, description="Configurations to compare"
    )


class BenchmarkResult(BaseModel):
    """Result from a single benchmark configuration."""

    config_name: str = Field(..., description="Configuration name")
    results: list[SearchResult] = Field(default_factory=list, description="Search results")
    latency_ms: float = Field(..., description="Search latency in milliseconds")
    embedding_provider: str = Field(..., description="Embedding provider used")
    rerank_provider: str | None = Field(default=None, description="Rerank provider used")


class BenchmarkResponse(BaseModel):
    """Response from a benchmark comparison."""

    query: str = Field(..., description="Test query")
    collection: str = Field(..., description="Collection searched")
    results: list[BenchmarkResult] = Field(
        default_factory=list, description="Results per configuration"
    )
    total_latency_ms: float = Field(..., description="Total benchmark time")


# =============================================================================
# Collection API Models
# =============================================================================


class CollectionInfo(BaseModel):
    """Information about a collection."""

    name: str = Field(..., description="Collection name")
    count: int = Field(..., description="Number of documents")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Collection metadata")


class CollectionsListResponse(BaseModel):
    """Response listing all collections."""

    collections: list[CollectionInfo] = Field(
        default_factory=list, description="List of collections"
    )
    total: int = Field(..., description="Total number of collections")


class CollectionDeleteResponse(BaseModel):
    """Response after deleting a collection."""

    name: str = Field(..., description="Deleted collection name")
    message: str = Field(default="Collection deleted successfully")
