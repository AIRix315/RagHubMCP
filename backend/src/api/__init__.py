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
    # Search
    SearchRequest,
    SearchResponse,
    SearchResult,
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
]
