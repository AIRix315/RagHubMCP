"""Pydantic models for REST API request/response schemas.

This module defines all the data models used by the REST API endpoints.
Configuration models are imported from utils/config.py to avoid duplication.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# Import configuration models from utils/config.py (single source of truth)
from src.utils.config import (
    AppConfig,
    ChromaConfig,
    HybridConfig,
    IndexerConfig,
    LoggingConfig,
    ProvidersConfig,
    ServerConfig,
    WatcherConfig,
)

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
# Config API Models (re-export from utils/config.py)
# =============================================================================

# Re-export for backward compatibility
ConfigModel = AppConfig


class ProviderInstanceModel(BaseModel):
    """Provider instance configuration (for API documentation)."""

    name: str
    type: str
    model: str
    base_url: str | None = Field(default=None)
    dimension: int | None = Field(default=None)


class ProviderCategoryModel(BaseModel):
    """Provider category configuration (for API documentation)."""

    default: str
    instances: list[dict[str, Any]] = Field(default_factory=list)


class ConfigUpdateRequest(BaseModel):
    """Request body for updating configuration.

    Only include the fields you want to update.
    """

    server: ServerConfig | None = None
    chroma: ChromaConfig | None = None
    providers: ProvidersConfig | None = None
    indexer: IndexerConfig | None = None
    logging: LoggingConfig | None = None
    hybrid: HybridConfig | None = None
    watcher: WatcherConfig | None = None


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


# =============================================================================
# Provider API Models (Task 1.10)
# =============================================================================


class ProviderStatus(str, Enum):
    """Provider status values."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ProviderInfo(BaseModel):
    """Information about a provider instance."""

    name: str = Field(..., description="Provider instance name")
    type: str = Field(..., description="Provider type (e.g., onnx, ollama, openai)")
    status: ProviderStatus = Field(..., description="Provider status")
    is_default: bool = Field(default=False, description="Whether this is the default provider")
    model: str | None = Field(default=None, description="Model name")
    config: dict[str, Any] | None = Field(default=None, description="Provider configuration")
    error_message: str | None = Field(default=None, description="Error message if status is error")
    capabilities: dict[str, Any] | None = Field(default=None, description="Provider capabilities")


class ProvidersListResponse(BaseModel):
    """Response listing all providers grouped by category."""

    embedding: list[ProviderInfo] = Field(default_factory=list, description="Embedding providers")
    rerank: list[ProviderInfo] = Field(default_factory=list, description="Rerank providers")
    llm: list[ProviderInfo] = Field(default_factory=list, description="LLM providers")
    vectorstore: list[ProviderInfo] = Field(
        default_factory=list, description="Vector store providers"
    )


class RerankResult(BaseModel):
    """Single rerank result."""

    index: int = Field(..., ge=0, description="Original document index")
    text: str = Field(..., description="Document text")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0.0 - 1.0)")
    rank: int = Field(..., ge=1, description="Rank position (1-based)")
    processing_time_ms: float | None = Field(default=None, description="Processing time")


class RerankTestRequest(BaseModel):
    """Request to test a rerank provider."""

    query: str = Field(..., min_length=1, description="Search query")
    documents: list[str] = Field(..., min_length=1, description="Documents to rerank")
    top_k: int = Field(default=5, ge=1, le=100, description="Number of results to return")


class RerankTestResponse(BaseModel):
    """Response from testing a rerank provider."""

    results: list[RerankResult] = Field(default_factory=list, description="Reranked results")
    latency_ms: float = Field(..., description="Total latency in milliseconds")
    engine_info: dict[str, Any] = Field(..., description="Engine information")
    intermediate_scores: dict[str, list[float]] | None = Field(
        default=None, description="Intermediate scores (raw, normalized)"
    )


class ProviderCreateRequest(BaseModel):
    """Request to create or update a provider."""

    type: str = Field(..., description="Provider type (e.g., onnx, ollama)")
    config: dict[str, Any] = Field(..., description="Provider configuration")
    set_as_default: bool = Field(default=False, description="Set as default provider")


class ProviderUpdateResponse(BaseModel):
    """Response after creating or updating a provider."""

    name: str = Field(..., description="Provider name")
    message: str = Field(..., description="Result message")
    is_new: bool = Field(..., description="Whether this was a new provider")


class ProviderDeleteResponse(BaseModel):
    """Response after deleting a provider."""

    name: str = Field(..., description="Deleted provider name")
    message: str = Field(default="Provider deleted successfully")


class SetDefaultProviderResponse(BaseModel):
    """Response after setting default provider."""

    name: str = Field(..., description="Provider name")
    type: str = Field(..., description="Provider category")
    message: str = Field(default="Default provider updated")
