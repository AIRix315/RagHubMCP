"""Services module for RagHubMCP.

This module provides service layer abstractions for external systems.

Active Services:
- BM25Service: BM25 lexical search service
- HybridSearchService: Hybrid search combining vector and BM25 (deprecated, use HybridRetriever)

For vector store operations, use the factory provider:

    from src.providers.factory import factory
    vectorstore = factory.get_vectorstore_provider()
"""

from .bm25_service import BM25Service, BM25Index, get_bm25_service, reset_bm25_service
from .hybrid_search import (  # noqa: E402
    HybridSearchService,
    HybridSearchResult,
    get_hybrid_search_service,
    reset_hybrid_search_service,
    reciprocal_rank_fusion,
)

__all__ = [
    # Active
    "BM25Service",
    "BM25Index",
    "get_bm25_service",
    "reset_bm25_service",
    "HybridSearchService",
    "HybridSearchResult",
    "get_hybrid_search_service",
    "reset_hybrid_search_service",
    "reciprocal_rank_fusion",
]