"""REST API module for RagHubMCP.

This module provides REST API endpoints for the Web console.
"""

from .router import api_router
from .schemas import (
    BenchmarkConfig,
    # Benchmark
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkResult,
    # Config
    ConfigModel,
    ConfigUpdateRequest,
    # Common
    ErrorResponse,
    # Index
    IndexRequest,
    IndexResponse,
    IndexTaskStatus,
    # Provider (Task 1.10)
    ProviderCreateRequest,
    ProviderDeleteResponse,
    ProviderInfo,
    ProvidersListResponse,
    ProviderStatus,
    ProviderUpdateResponse,
    RerankResult,
    RerankTestRequest,
    RerankTestResponse,
    # Search
    SearchRequest,
    SearchResponse,
    SearchResult,
    SetDefaultProviderResponse,
    SuccessResponse,
    TaskStatus,
)

__all__ = [
    # Router
    "api_router",
    # Common
    "ErrorResponse",
    "SuccessResponse",
    # Config
    "ConfigModel",
    "ConfigUpdateRequest",
    # Index
    "IndexRequest",
    "IndexResponse",
    "IndexTaskStatus",
    "TaskStatus",
    # Search
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    # Benchmark
    "BenchmarkRequest",
    "BenchmarkResponse",
    "BenchmarkResult",
    "BenchmarkConfig",
    # Provider (Task 1.10)
    "ProviderInfo",
    "ProviderStatus",
    "ProvidersListResponse",
    "RerankTestRequest",
    "RerankTestResponse",
    "RerankResult",
    "ProviderCreateRequest",
    "ProviderUpdateResponse",
    "ProviderDeleteResponse",
    "SetDefaultProviderResponse",
]
