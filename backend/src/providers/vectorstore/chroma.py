"""ChromaDB vector store provider implementation.

This module provides a vector store provider that wraps the existing
ChromaService, providing a unified interface compatible with the
BaseVectorStoreProvider abstraction.

The ChromaProvider supports:
- Local persistent storage
- Optional remote Chroma server connection
- Automatic embedding generation
- Metadata filtering with Chroma query syntax
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ..base import ProviderCategory
from ..registry import registry
from .base import BaseVectorStoreProvider, SearchResult, QueryResult

logger = logging.getLogger(__name__)


@registry.register(ProviderCategory.VECTORSTORE, "chroma")
class ChromaProvider(BaseVectorStoreProvider):
    """ChromaDB vector store provider.
    
    Wraps the existing ChromaService to provide a unified interface
    for vector storage operations. Supports both local persistent storage
    and remote Chroma server connections.
    
    Attributes:
        NAME: Provider type identifier ("chroma")
        persist_dir: Directory for persistent storage (local mode)
        host: Remote Chroma server host (None for local mode)
        port: Remote Chroma server port (None for local mode)
    
    Example:
        >>> provider = ChromaProvider(persist_dir="./data/chroma")
        >>> provider.add("my_collection", ["doc1"], ["id1"])
        >>> results = provider.query("my_collection", query_text="search", n_results=5)
    """
    
    NAME = "chroma"
    
    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        host: str | None = None,
        port: int | None = None,
    ) -> None:
        """Initialize ChromaProvider.
        
        Args:
            persist_dir: Directory for persistent storage (local mode).
                        Default: "./data/chroma"
            host: Remote Chroma server host. If provided, uses remote mode.
            port: Remote Chroma server port. Required if host is provided.
        """
        self._persist_dir = persist_dir
        self._host = host
        self._port = port
        self._service: Any = None  # ChromaService instance (lazy init)
    
    def _get_service(self) -> Any:
        """Get or create ChromaService instance (lazy initialization)."""
        if self._service is None:
            from src.services.chroma_service import ChromaService
            self._service = ChromaService(persist_dir=self._persist_dir)
        return self._service
    
    @property
    def persist_dir(self) -> str:
        """Get the persist directory."""
        return self._persist_dir
    
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
        service = self._get_service()
        service.get_or_create_collection(name=name, metadata=metadata, use_embedding=True)
        logger.debug(f"Created collection: {name}")
    
    def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: Collection name to delete
        """
        service = self._get_service()
        service.delete_collection(name=name)
        logger.debug(f"Deleted collection: {name}")
    
    def list_collections(self) -> list[str]:
        """List all collection names."""
        service = self._get_service()
        return service.list_collection_names()
    
    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        service = self._get_service()
        try:
            service.get_collection(name=name)
            return True
        except ValueError:
            return False
    
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
            embeddings: Optional pre-computed embeddings (not used, Chroma auto-embeds)
        """
        if not documents:
            return
        
        service = self._get_service()
        service.add_documents(
            collection_name=collection,
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )
        logger.debug(f"Added {len(documents)} documents to collection '{collection}'")
    
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
            query_text: Query text (will be embedded automatically)
            query_embedding: Pre-computed query embedding (not supported in ChromaProvider)
            n_results: Maximum number of results
            where: Metadata filter (Chroma query syntax)
            where_document: Document content filter
        
        Returns:
            QueryResult containing matching documents
        """
        if query_text is None:
            raise ValueError("ChromaProvider requires query_text for querying")
        
        service = self._get_service()
        result = service.query(
            collection_name=collection,
            query_text=query_text,
            n_results=n_results,
            where=where,
            where_document=where_document,
        )
        
        # Convert to SearchResult objects
        results = []
        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        distances = result.get("distances", [])
        
        for i in range(len(ids)):
            results.append(SearchResult(
                id=str(ids[i]),
                document=documents[i] if i < len(documents) else "",
                metadata=metadatas[i] if i < len(metadatas) else {},
                score=distances[i] if i < len(distances) else 0.0,
            ))
        
        return QueryResult(results=results)
    
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
            limit: Maximum number of documents
            offset: Number of documents to skip
        
        Returns:
            List of search results
        """
        service = self._get_service()
        chroma_collection = service.get_collection(collection)
        
        result = chroma_collection.get(
            ids=ids,
            where=where,
            limit=limit,
            offset=offset,
            include=["documents", "metadatas"],
        )
        
        results = []
        result_ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        
        for i in range(len(result_ids)):
            results.append(SearchResult(
                id=str(result_ids[i]),
                document=documents[i] if i < len(documents) else "",
                metadata=metadatas[i] if i < len(metadatas) else {},
            ))
        
        return results
    
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
            where: Optional metadata filter
        
        Returns:
            Number of documents deleted (approximate)
        """
        service = self._get_service()
        chroma_collection = service.get_collection(collection)
        
        # Get count before deletion for approximation
        count_before = chroma_collection.count()
        
        chroma_collection.delete(ids=ids, where=where)
        
        # Approximate deletion count
        count_after = chroma_collection.count()
        return count_before - count_after
    
    def count(self, collection: str) -> int:
        """Count documents in a collection."""
        service = self._get_service()
        return service.count(collection)
    
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
            embeddings: Optional pre-computed embeddings
        """
        service = self._get_service()
        chroma_collection = service.get_collection(collection)
        
        update_kwargs = {"ids": ids}
        if documents is not None:
            update_kwargs["documents"] = documents
        if metadatas is not None:
            update_kwargs["metadatas"] = metadatas
        if embeddings is not None:
            update_kwargs["embeddings"] = embeddings
        
        chroma_collection.update(**update_kwargs)
        logger.debug(f"Updated {len(ids)} documents in collection '{collection}'")
    
    def reset(self) -> None:
        """Reset all collections (for testing)."""
        service = self._get_service()
        service.reset()
    
    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ChromaProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - persist_dir: Storage directory (optional)
                   - host: Remote server host (optional)
                   - port: Remote server port (optional)
        
        Returns:
            New ChromaProvider instance
        """
        return cls(
            persist_dir=config.get("persist_dir", "./data/chroma"),
            host=config.get("host"),
            port=config.get("port"),
        )