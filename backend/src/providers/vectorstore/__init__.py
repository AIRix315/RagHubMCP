"""VectorStore providers module.

This module provides base classes and types for vector database providers.
"""

from .base import (
    BaseVectorStoreProvider,
    SearchResult,
    QueryResult,
)

__all__ = [
    # Base classes and types
    "BaseVectorStoreProvider",
    "SearchResult",
    "QueryResult",
]