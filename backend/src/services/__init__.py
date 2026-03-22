"""Services module for RagHubMCP.

.. deprecated:: 2.1
    This module is deprecated and will be removed in v3.0.
    Use the Pipeline module instead for all search operations.

    See src/services/DEPRECATED.md for migration guide.

This module provides service layer abstractions for external systems.

Active Services:
- BM25Service: BM25 lexical search service
- HybridSearchService: Hybrid search combining vector and BM25 (deprecated, use HybridRetriever)

For vector store operations, use the factory provider:

    from src.providers.factory import factory
    vectorstore = factory.get_vectorstore_provider()
"""

from __future__ import annotations

import logging
import warnings

# Emit deprecation warning on module import
warnings.warn(
    "services module is deprecated and will be removed in v3.0. "
    "Use pipeline module instead. See src/services/DEPRECATED.md for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

logger = logging.getLogger(__name__)
logger.debug("services module imported (deprecated)")

from .bm25_service import BM25Index, BM25Service, get_bm25_service, reset_bm25_service
from .hybrid_search import (  # noqa: E402
    HybridSearchResult,
    HybridSearchService,
    get_hybrid_search_service,
    reciprocal_rank_fusion,
    reset_hybrid_search_service,
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
