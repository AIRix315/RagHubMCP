"""Chroma service - Singleton client management.

This module provides a singleton ChromaDB client with:
- Persistent storage support
- Collection management
- Vector similarity search
- Thread-safe initialization
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

logger = logging.getLogger(__name__)

# Singleton client
_client: chromadb.Client | None = None
_persist_dir: str = ""
_embedding_function: Any = None


def _get_embedding_function():
    """Create a ChromaDB-compatible embedding function.
    
    Returns:
        An embedding function that wraps the configured embedding provider.
    """
    global _embedding_function
    
    if _embedding_function is not None:
        return _embedding_function
    
    from providers.factory import factory
    
    provider = factory.get_embedding_provider()
    
    class EmbeddingFunction:
        """ChromaDB embedding function wrapper."""
        
        def __init__(self, embedding_provider):
            self._provider = embedding_provider
        
        def __call__(self, input: list[str]) -> list[list[float]]:
            """Embed a list of texts."""
            return self._provider.embed_documents(input)
        
        def name(self) -> str:
            """Return the embedding function name (required by ChromaDB)."""
            return f"raghub_{self._provider.NAME}"
    
    _embedding_function = EmbeddingFunction(provider)
    return _embedding_function


class ChromaService:
    """ChromaDB service wrapper with singleton pattern.
    
    Provides a clean interface for ChromaDB operations:
    - Client management with persistent storage
    - Collection creation and retrieval
    - Document indexing with embeddings
    - Vector similarity search
    - Thread-safe initialization
    
    Example:
        >>> service = get_chroma_service()
        >>> service.add_documents("my_collection", ["doc1"], ["id1"])
        >>> results = service.query("my_collection", "search query", n_results=5)
    """
    
    def __init__(self, persist_dir: str) -> None:
        """Initialize ChromaService.
        
        Args:
            persist_dir: Directory for ChromaDB persistent storage
        """
        self._persist_dir = persist_dir
        self._client: chromadb.Client | None = None
    
    @property
    def client(self) -> chromadb.Client:
        """Get the ChromaDB client (lazy initialization)."""
        if self._client is None:
            Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Initializing ChromaDB client with persist_dir: {self._persist_dir}")
            self._client = chromadb.PersistentClient(path=self._persist_dir)
        return self._client
    
    @property
    def persist_dir(self) -> str:
        """Get the persist directory."""
        return self._persist_dir
    
    def _get_embedding_function(self):
        """Get the embedding function for collections."""
        return _get_embedding_function()
    
    def get_or_create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        use_embedding: bool = True,
    ) -> Collection:
        """Get or create a Chroma collection.
        
        Args:
            name: Collection name
            metadata: Optional metadata for the collection
            use_embedding: Whether to use embedding function (default: True)
        
        Returns:
            ChromaDB Collection instance
            
        Raises:
            ValueError: If collection name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid collection name: {name}")
        
        # ChromaDB requires non-empty metadata
        final_metadata = metadata if metadata else {"created_by": "raghub_mcp"}
        
        embedding_function = None
        if use_embedding:
            try:
                embedding_function = self._get_embedding_function()
            except Exception as e:
                logger.warning(f"Could not create embedding function: {e}")
        
        collection = self.client.get_or_create_collection(
            name=name,
            metadata=final_metadata,
            embedding_function=embedding_function,
        )
        logger.debug(f"Got/created collection: {name}")
        return collection
    
    def get_collection(self, name: str) -> Collection:
        """Get an existing collection.
        
        Args:
            name: Collection name
        
        Returns:
            ChromaDB Collection instance
            
        Raises:
            ValueError: If collection does not exist
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid collection name: {name}")
        
        try:
            return self.client.get_collection(name=name)
        except Exception as e:
            raise ValueError(f"Collection '{name}' not found: {e}") from e
    
    def list_collections(self) -> list[Collection]:
        """List all collections.
        
        Returns:
            List of Collection objects
        """
        return list(self.client.list_collections())
    
    def list_collection_names(self) -> list[str]:
        """List all collection names.
        
        Returns:
            List of collection names
        """
        return [c.name for c in self.client.list_collections()]
    
    def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: Collection name to delete
        """
        self.client.delete_collection(name=name)
        logger.info(f"Deleted collection: {name}")
    
    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add documents to a collection.
        
        Args:
            collection_name: Target collection name
            documents: List of document texts
            ids: List of unique document IDs
            metadatas: Optional list of metadata dictionaries
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        if len(documents) != len(ids):
            raise ValueError("documents and ids must have same length")
        
        if metadatas and len(metadatas) != len(documents):
            raise ValueError("metadatas must have same length as documents")
        
        collection = self.get_or_create_collection(collection_name)
        collection.add(
            documents=documents,
            ids=ids,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query documents from a collection using vector similarity.
        
        Args:
            collection_name: Collection to query
            query_text: Query text
            n_results: Maximum number of results to return
            where: Optional metadata filter (Chroma query syntax)
            where_document: Optional document content filter
        
        Returns:
            Dictionary containing:
            - ids: List of document IDs
            - documents: List of document texts
            - metadatas: List of metadata dictionaries
            - distances: List of distance scores (lower = more similar)
            
        Raises:
            ValueError: If collection doesn't exist or query is invalid
        """
        if not query_text or not isinstance(query_text, str):
            raise ValueError("Query must be a non-empty string")
        
        if n_results <= 0:
            n_results = 10
        
        collection = self.get_collection(collection_name)
        
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        # Transform results to a cleaner format (flatten single query results)
        return {
            "ids": results.get("ids", [[]])[0],
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "distances": results.get("distances", [[]])[0],
        }
    
    def count(self, collection_name: str) -> int:
        """Count documents in a collection.
        
        Args:
            collection_name: Collection name
        
        Returns:
            Number of documents in the collection
        """
        collection = self.get_collection(collection_name)
        return collection.count()
    
    def reset(self) -> None:
        """Reset all collections (for testing).
        
        Warning: This deletes all data!
        """
        for name in self.list_collection_names():
            self.client.delete_collection(name)
        logger.warning("Reset ChromaDB - all collections deleted")


# Singleton instance
_instance: ChromaService | None = None


def get_chroma_service(persist_dir: str | None = None) -> ChromaService:
    """Get the singleton ChromaService instance.
    
    Args:
        persist_dir: Directory for persistent storage. Required on first call.
                     If None, uses the previously configured directory or config.
    
    Returns:
        ChromaService singleton instance
        
    Raises:
        ValueError: If persist_dir is not provided on first call and no config exists
    """
    global _instance
    
    if _instance is not None:
        return _instance
    
    # First call - need persist_dir
    if persist_dir is None:
        try:
            from utils.config import get_config
            persist_dir = get_config().chroma.persist_dir
        except RuntimeError:
            raise ValueError(
                "persist_dir must be provided on first call to get_chroma_service(), "
                "or configuration must be loaded."
            )
    
    _instance = ChromaService(persist_dir=persist_dir)
    return _instance


def reset_chroma_service() -> None:
    """Reset the singleton instance (for testing purposes)."""
    global _instance
    _instance = None
    logger.debug("ChromaService singleton reset")