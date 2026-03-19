"""VectorStore providers module.

This module provides vector database providers for storing and querying
document embeddings. Available providers:
- ChromaProvider: Uses ChromaDB (local persistent storage)
- QdrantProvider: Uses Qdrant (local, remote, or cloud mode)

Example:
    >>> from providers.vectorstore import ChromaProvider, QdrantProvider
    >>> 
    >>> # Chroma (local)
    >>> chroma = ChromaProvider(persist_dir="./data/chroma")
    >>> chroma.add("docs", ["Hello world"], ["doc1"])
    >>> results = chroma.query("docs", query_text="Hello")
    >>> 
    >>> # Qdrant (in-memory for testing)
    >>> qdrant = QdrantProvider(mode="memory")
    >>> qdrant.add("docs", ["Hello world"], ["doc1"])
    >>> results = qdrant.query("docs", query_text="Hello")
"""

from .base import (
    BaseVectorStoreProvider,
    SearchResult,
    QueryResult,
)
from .chroma import ChromaProvider
from .qdrant import QdrantProvider

__all__ = [
    # Base classes
    "BaseVectorStoreProvider",
    "SearchResult",
    "QueryResult",
    # Providers
    "ChromaProvider",
    "QdrantProvider",
]