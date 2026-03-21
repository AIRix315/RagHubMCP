"""VectorStore provider abstract base class.

This module defines the interface for vector store providers that manage
document embeddings and support similarity search.

The interface is designed to be compatible with both ChromaDB and Qdrant,
providing a unified abstraction for:
- Collection management (create, delete, list)
- Document indexing with embeddings
- Vector similarity search
- Metadata filtering
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..base import BaseProvider


@dataclass
class SearchResult:
    """Search result from vector similarity query.

    Attributes:
        id: Document ID
        document: Document text content
        metadata: Document metadata dictionary
        score: Similarity score (lower = more similar for distance-based metrics)
    """

    id: str
    document: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass
class QueryResult:
    """Result container for vector query operations.

    Attributes:
        results: List of search results
        total: Total number of matching documents (if available)
    """

    results: list[SearchResult] = field(default_factory=list)
    total: int | None = None


class BaseVectorStoreProvider(BaseProvider):
    """Abstract base class for vector store providers.

    Vector store providers manage collections of documents with their
    vector embeddings and support similarity search operations.

    Subclasses must implement:
    - NAME: Class attribute for provider identification
    - add(): Add documents with embeddings to a collection
    - query(): Query documents using vector similarity
    - delete(): Delete documents from a collection
    - count(): Count documents in a collection
    - list_collections(): List all collection names
    - create_collection(): Create a new collection
    - delete_collection(): Delete a collection
    - from_config(): Factory method to create instances from config

    Example:
        class MyVectorStore(BaseVectorStoreProvider):
            NAME = "my-vectorstore"

            def add(self, collection: str, documents: list[str],
                    ids: list[str], metadatas: list[dict] | None = None) -> None:
                # Implementation
                ...
    """

    @abstractmethod
    def create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection.

        Args:
            name: Collection name
            metadata: Optional collection metadata
        """
        ...

    @abstractmethod
    def delete_collection(self, name: str) -> None:
        """Delete a collection and all its documents.

        Args:
            name: Collection name to delete
        """
        ...

    @abstractmethod
    def list_collections(self) -> list[str]:
        """List all collection names.

        Returns:
            List of collection names
        """
        ...

    @abstractmethod
    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists.

        Args:
            name: Collection name

        Returns:
            True if collection exists, False otherwise
        """
        ...

    @abstractmethod
    def add(
        self,
        collection: str,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        """Add documents to a collection.

        Args:
            collection: Target collection name
            documents: List of document texts
            ids: List of unique document IDs
            metadatas: Optional list of metadata dictionaries
            embeddings: Optional pre-computed embeddings.
                       If None, provider will generate embeddings.

        Raises:
            ValueError: If inputs are invalid
            CollectionNotFoundError: If collection doesn't exist
        """
        ...

    @abstractmethod
    def query(
        self,
        collection: str,
        query_text: str | None = None,
        query_embedding: list[float] | None = None,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> QueryResult:
        """Query documents using vector similarity.

        Args:
            collection: Collection to query
            query_text: Query text (will be embedded if no query_embedding provided)
            query_embedding: Pre-computed query embedding vector
            n_results: Maximum number of results to return
            where: Optional metadata filter (provider-specific syntax)
            where_document: Optional document content filter

        Returns:
            QueryResult containing matching documents

        Raises:
            ValueError: If neither query_text nor query_embedding provided
            CollectionNotFoundError: If collection doesn't exist
        """
        ...

    @abstractmethod
    def get(
        self,
        collection: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SearchResult]:
        """Retrieve documents from a collection.

        Args:
            collection: Collection name
            ids: Optional list of document IDs to retrieve
            where: Optional metadata filter
            limit: Maximum number of documents to return
            offset: Number of documents to skip

        Returns:
            List of search results
        """
        ...

    @abstractmethod
    def delete(
        self,
        collection: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> int:
        """Delete documents from a collection.

        Args:
            collection: Collection name
            ids: Optional list of document IDs to delete
            where: Optional metadata filter for deletion

        Returns:
            Number of documents deleted
        """
        ...

    @abstractmethod
    def count(self, collection: str) -> int:
        """Count documents in a collection.

        Args:
            collection: Collection name

        Returns:
            Number of documents in the collection
        """
        ...

    @abstractmethod
    def update(
        self,
        collection: str,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        """Update existing documents in a collection.

        Args:
            collection: Collection name
            ids: List of document IDs to update
            documents: Optional new document texts
            metadatas: Optional new metadata dictionaries
            embeddings: Optional new embeddings
        """
        ...

    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> BaseVectorStoreProvider:
        """Create an instance from configuration dictionary.

        Args:
            config: Configuration from config.yaml providers section.

        Returns:
            New provider instance

        Raises:
            ProviderInitializationError: If configuration is invalid
        """
        ...
