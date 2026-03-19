"""Services module for RagHubMCP.

This module provides service layer abstractions for external systems:
- ChromaService: Vector database client wrapper
- BM25Service: BM25 lexical search service
- HybridSearchService: Combined vector + BM25 search
"""

from .chroma_service import ChromaService, get_chroma_service
from .bm25_service import BM25Service, BM25Index, get_bm25_service, reset_bm25_service
from .hybrid_search import (
    HybridSearchService,
    HybridSearchResult,
    get_hybrid_search_service,
    reset_hybrid_search_service,
    reciprocal_rank_fusion,
)

__all__ = [
    "ChromaService",
    "get_chroma_service",
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