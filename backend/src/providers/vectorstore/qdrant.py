"""Qdrant vector store provider implementation.

This module provides a vector store provider that uses Qdrant for
vector similarity search. Supports both local (in-memory/persistent)
and remote (server/cloud) modes.

Features:
- Local mode: In-memory or persistent storage
- Remote mode: Connect to Qdrant server or Qdrant Cloud
- gRPC support for faster uploads
- Metadata filtering with Qdrant filter syntax

ID Requirements:
- Qdrant supports two ID types: 64-bit unsigned integers or UUID strings
- Non-UUID string IDs are NOT supported by Qdrant
- If you need custom string IDs, store them in payload and use integer/UUID as point ID
"""

from __future__ import annotations

import logging
from typing import Any

from ..base import ProviderCategory
from ..registry import registry
from .base import BaseVectorStoreProvider, SearchResult, QueryResult

logger = logging.getLogger(__name__)

# Default embedding dimension
DEFAULT_EMBEDDING_DIMENSION = 768


@registry.register(ProviderCategory.VECTORSTORE, "qdrant")
class QdrantProvider(BaseVectorStoreProvider):
    """Qdrant vector store provider.
    
    Provides vector storage using Qdrant with support for:
    - Local in-memory mode (for testing)
    - Local persistent storage
    - Remote Qdrant server
    - Qdrant Cloud with API key
    
    Attributes:
        NAME: Provider type identifier ("qdrant")
    
    Example:
        >>> # Local in-memory mode
        >>> provider = QdrantProvider(mode="memory")
        >>> 
        >>> # Local persistent mode
        >>> provider = QdrantProvider(mode="local", path="./data/qdrant")
        >>> 
        >>> # Remote server
        >>> provider = QdrantProvider(mode="remote", host="localhost", port=6333)
        >>> 
        >>> # Qdrant Cloud
        >>> provider = QdrantProvider(
        ...     mode="cloud",
        ...     url="https://your-cluster.cloud.qdrant.io:6333",
        ...     api_key="your-api-key"
        ... )
    """
    
    NAME = "qdrant"
    
    def __init__(
        self,
        mode: str = "local",
        path: str | None = None,
        host: str | None = None,
        port: int | None = None,
        url: str | None = None,
        api_key: str | None = None,
        embedding_dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        prefer_grpc: bool = False,
    ) -> None:
        """Initialize QdrantProvider.
        
        Args:
            mode: Operating mode - "memory", "local", "remote", or "cloud"
            path: Storage path for local mode (default: "./data/qdrant")
            host: Qdrant server host (for remote mode)
            port: Qdrant server port (default: 6333 for REST, 6334 for gRPC)
            url: Full URL for Qdrant Cloud
            api_key: API key for Qdrant Cloud
            embedding_dimension: Dimension for vectors (default: 768)
            prefer_grpc: Use gRPC for faster operations
        """
        self._mode = mode
        self._path = path or "./data/qdrant"
        self._host = host
        self._port = port
        self._url = url
        self._api_key = api_key
        self._embedding_dimension = embedding_dimension
        self._prefer_grpc = prefer_grpc
        self._client: Any = None  # QdrantClient instance (lazy init)
        self._embedding_provider: Any = None  # Lazy init
    
    def _get_client(self) -> Any:
        """Get or create QdrantClient instance (lazy initialization)."""
        if self._client is None:
            from qdrant_client import QdrantClient
            
            if self._mode == "memory":
                self._client = QdrantClient(":memory:")
            elif self._mode == "local":
                self._client = QdrantClient(path=self._path)
            elif self._mode == "cloud" and self._url:
                self._client = QdrantClient(
                    url=self._url,
                    api_key=self._api_key,
                )
            elif self._mode == "remote" or (self._host or self._url):
                if self._url:
                    self._client = QdrantClient(
                        url=self._url,
                        api_key=self._api_key,
                        grpc_port=self._port or 6334 if self._prefer_grpc else None,
                        prefer_grpc=self._prefer_grpc,
                    )
                else:
                    self._client = QdrantClient(
                        host=self._host or "localhost",
                        port=self._port or (6334 if self._prefer_grpc else 6333),
                        prefer_grpc=self._prefer_grpc,
                    )
            else:
                # Default to local mode
                self._client = QdrantClient(path=self._path)
            
            logger.info(f"Initialized Qdrant client in {self._mode} mode")
        
        return self._client
    
    def _get_embedding_provider(self) -> Any:
        """Get the embedding provider for auto-embedding."""
        if self._embedding_provider is None:
            from providers.factory import factory
            self._embedding_provider = factory.get_embedding_provider()
        return self._embedding_provider
    
    def _get_collection_config(self) -> dict:
        """Get vector configuration for collection creation."""
        from qdrant_client import models
        return {
            "vectors_config": models.VectorParams(
                size=self._embedding_dimension,
                distance=models.Distance.COSINE,
            )
        }
    
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
        from qdrant_client import models
        
        client = self._get_client()
        
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=self._embedding_dimension,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.debug(f"Created Qdrant collection: {name}")
    
    def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: Collection name to delete
        """
        client = self._get_client()
        client.delete_collection(collection_name=name)
        logger.debug(f"Deleted Qdrant collection: {name}")
    
    def list_collections(self) -> list[str]:
        """List all collection names."""
        client = self._get_client()
        collections = client.get_collections()
        return [c.name for c in collections.collections]
    
    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        client = self._get_client()
        return client.collection_exists(name)
    
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
                       If None, will generate embeddings automatically.
        """
        if not documents:
            return
        
        from qdrant_client import models
        
        client = self._get_client()
        
        # Create collection if not exists
        if not self.collection_exists(collection):
            self.create_collection(collection)
        
        # Generate embeddings if not provided
        if embeddings is None:
            embedding_provider = self._get_embedding_provider()
            embeddings = embedding_provider.embed_documents(documents)
        
        # Build points - Qdrant requires integer or UUID format IDs
        points = []
        for i, (doc_id, doc, emb) in enumerate(zip(ids, documents, embeddings)):
            payload = {"document": doc}
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])
            
            points.append(models.PointStruct(
                id=doc_id,  # Qdrant accepts int or UUID string
                vector=emb,
                payload=payload,
            ))
        
        # Upsert points
        client.upsert(
            collection_name=collection,
            points=points,
            wait=True,
        )
        logger.debug(f"Added {len(points)} documents to Qdrant collection '{collection}'")
    
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
            n_results: Maximum number of results
            where: Metadata filter (Qdrant filter syntax)
            where_document: Document content filter (converted to payload filter)
        
        Returns:
            QueryResult containing matching documents
        """
        from qdrant_client import models
        
        client = self._get_client()
        
        # Generate embedding if needed
        if query_embedding is None:
            if query_text is None:
                raise ValueError("Either query_text or query_embedding must be provided")
            embedding_provider = self._get_embedding_provider()
            query_embedding = embedding_provider.embed_query(query_text)
        
        # Build filter
        query_filter = None
        if where:
            query_filter = self._build_filter(where)
        elif where_document:
            query_filter = self._build_document_filter(where_document)
        
        # Query
        results = client.query_points(
            collection_name=collection,
            query=query_embedding,
            query_filter=query_filter,
            limit=n_results,
            with_payload=True,
        )
        
        # Convert to SearchResult
        search_results = []
        for point in results.points:
            payload = point.payload or {}
            search_results.append(SearchResult(
                id=str(point.id),
                document=payload.get("document", ""),
                metadata={k: v for k, v in payload.items() if k != "document"},
                score=point.score,
            ))
        
        return QueryResult(results=search_results)
    
    def _build_filter(self, where: dict[str, Any]) -> Any:
        """Build Qdrant filter from metadata filter dict."""
        from qdrant_client import models
        
        conditions = []
        for key, value in where.items():
            if isinstance(value, dict):
                # Range filter
                if "$gt" in value or "$gte" in value or "$lt" in value or "$lte" in value:
                    conditions.append(models.FieldCondition(
                        key=key,
                        range=models.Range(
                            gt=value.get("$gt"),
                            gte=value.get("$gte"),
                            lt=value.get("$lt"),
                            lte=value.get("$lte"),
                        )
                    ))
                elif "$contains" in value:
                    conditions.append(models.FieldCondition(
                        key=key,
                        match=models.MatchText(text=value["$contains"]),
                    ))
            else:
                # Exact match
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                ))
        
        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return models.Filter(must=conditions)
        else:
            return models.Filter(must=conditions)
    
    def _build_document_filter(self, where_document: dict[str, Any]) -> Any:
        """Build Qdrant filter for document content."""
        from qdrant_client import models
        
        if "$contains" in where_document:
            return models.Filter(
                must=[
                    models.FieldCondition(
                        key="document",
                        match=models.MatchText(text=where_document["$contains"]),
                    )
                ]
            )
        return None
    
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
            ids: Optional list of document IDs to retrieve (int or UUID format)
            where: Optional metadata filter
            limit: Maximum number of documents
            offset: Number of documents to skip
        
        Returns:
            List of search results
        """
        client = self._get_client()
        
        if ids:
            # Retrieve by IDs - Qdrant accepts int or UUID
            points = client.retrieve(
                collection_name=collection,
                ids=ids,
                with_payload=True,
            )
            
            results = []
            for point in points:
                payload = point.payload or {}
                results.append(SearchResult(
                    id=str(point.id),
                    document=payload.get("document", ""),
                    metadata={k: v for k, v in payload.items() if k != "document"},
                ))
            return results
        else:
            # Scroll through collection
            query_filter = None
            if where:
                query_filter = self._build_filter(where)
            
            points, _ = client.scroll(
                collection_name=collection,
                scroll_filter=query_filter,
                limit=limit or 100,
                offset=offset,
                with_payload=True,
            )
            
            results = []
            for point in points:
                payload = point.payload or {}
                results.append(SearchResult(
                    id=str(point.id),
                    document=payload.get("document", ""),
                    metadata={k: v for k, v in payload.items() if k != "document"},
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
            ids: Optional list of document IDs to delete (int or UUID format)
            where: Optional metadata filter
        
        Returns:
            Number of documents deleted
        """
        client = self._get_client()
        
        if ids:
            # Delete by IDs - Qdrant accepts int or UUID
            client.delete(
                collection_name=collection,
                points_selector=ids,
            )
            return len(ids)
        elif where:
            query_filter = self._build_filter(where)
            result = client.delete(
                collection_name=collection,
                points_selector=query_filter,
            )
            return result.operation_id if hasattr(result, 'operation_id') else 0
        return 0
    
    def count(self, collection: str) -> int:
        """Count documents in a collection."""
        client = self._get_client()
        info = client.get_collection(collection)
        return info.points_count
    
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
            ids: List of document IDs to update (int or UUID format)
            documents: Optional new document texts
            metadatas: Optional new metadata dictionaries
            embeddings: Optional new embeddings
        """
        from qdrant_client import models
        
        client = self._get_client()
        
        # Generate embeddings if documents provided but no embeddings
        if documents and embeddings is None:
            embedding_provider = self._get_embedding_provider()
            embeddings = embedding_provider.embed_documents(documents)
        
        # Build points for update
        points = []
        for i, doc_id in enumerate(ids):
            payload = {}
            if documents and i < len(documents):
                payload["document"] = documents[i]
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])
            
            point_data = {"id": doc_id, "payload": payload if payload else None}
            if embeddings and i < len(embeddings):
                point_data["vector"] = embeddings[i]
            
            points.append(models.PointStruct(**point_data))
        
        client.upsert(
            collection_name=collection,
            points=points,
            wait=True,
        )
        logger.debug(f"Updated {len(ids)} documents in Qdrant collection '{collection}'")
    
    @classmethod
    def from_config(cls, config: dict[str, Any]) -> QdrantProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - mode: "memory", "local", "remote", or "cloud"
                   - path: Storage path (for local mode)
                   - host: Server host (for remote mode)
                   - port: Server port
                   - url: Full URL (for cloud mode)
                   - api_key: API key (for cloud mode)
                   - embedding_dimension: Vector dimension
        
        Returns:
            New QdrantProvider instance
        """
        return cls(
            mode=config.get("mode", "local"),
            path=config.get("path"),
            host=config.get("host"),
            port=config.get("port"),
            url=config.get("url"),
            api_key=config.get("api_key"),
            embedding_dimension=config.get("embedding_dimension", DEFAULT_EMBEDDING_DIMENSION),
            prefer_grpc=config.get("prefer_grpc", False),
        )