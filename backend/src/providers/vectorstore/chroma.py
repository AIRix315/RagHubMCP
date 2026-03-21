"""ChromaDB vector store provider implementation.

This module provides a vector store provider that directly wraps ChromaDB
using the BaseVectorStoreProvider interface.

The ChromaProvider supports:
- Local persistent storage
- Automatic embedding generation
- Metadata filtering with Chroma query syntax

Reference:
- RULE.md (RULE-3: 禁止直接依赖具体实现)
- Docs/12-V2-Blueprint.md (Module 3: Provider抽象)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import chromadb

from ..base import ProviderCategory
from ..embedding.base import BaseEmbeddingProvider
from ..registry import registry
from .base import BaseVectorStoreProvider, QueryResult, SearchResult

logger = logging.getLogger(__name__)


class ChromaCollectionWrapper:
    """Wrapper for ChromaDB collection to provide cleaner interface."""

    def __init__(self, collection: chromadb.api.models.Collection) -> None:
        self._collection = collection

    def add(
        self,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {"ids": ids}
        if documents is not None:
            kwargs["documents"] = documents
        if metadatas is not None:
            kwargs["metadatas"] = metadatas
        if embeddings is not None:
            kwargs["embeddings"] = embeddings
        self._collection.add(**kwargs)

    def query(
        self,
        query_texts: list[str] | None = None,
        query_embeddings: list[list[float]] | None = None,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if query_texts is not None:
            kwargs["query_texts"] = query_texts
        if query_embeddings is not None:
            kwargs["query_embeddings"] = query_embeddings
        kwargs["n_results"] = n_results
        if where is not None:
            kwargs["where"] = where
        if where_document is not None:
            kwargs["where_document"] = where_document
        if include is not None:
            kwargs["include"] = include
        else:
            kwargs["include"] = ["documents", "metadatas", "distances"]
        return self._collection.query(**kwargs)

    def get(
        self,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
        include: list[str] | None = None,
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if ids is not None:
            kwargs["ids"] = ids
        if where is not None:
            kwargs["where"] = where
        if limit is not None:
            kwargs["limit"] = limit
        if offset is not None:
            kwargs["offset"] = offset
        if include is not None:
            kwargs["include"] = include
        else:
            kwargs["include"] = ["documents", "metadatas"]
        return self._collection.get(**kwargs)

    def count(self) -> int:
        return self._collection.count()

    def delete(
        self,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {}
        if ids is not None:
            kwargs["ids"] = ids
        if where is not None:
            kwargs["where"] = where
        self._collection.delete(**kwargs)

    def update(
        self,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        kwargs: dict[str, Any] = {"ids": ids}
        if documents is not None:
            kwargs["documents"] = documents
        if metadatas is not None:
            kwargs["metadatas"] = metadatas
        if embeddings is not None:
            kwargs["embeddings"] = embeddings
        self._collection.update(**kwargs)


class ChromaEmbeddingFunction:
    """ChromaDB-compatible embedding function wrapper."""

    def __init__(self, embedding_provider: BaseEmbeddingProvider) -> None:
        self._provider = embedding_provider

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self._provider.embed_documents(input)

    def name(self) -> str:
        """Return the name of the embedding function (ChromaDB requires callable)."""
        return f"raghub_{self._provider.NAME}"


@registry.register(ProviderCategory.VECTORSTORE, "chroma")
class ChromaProvider(BaseVectorStoreProvider):
    """ChromaDB vector store provider.

    Directly wraps ChromaDB to provide a unified interface compatible with
    the BaseVectorStoreProvider abstraction.

    Attributes:
        NAME: Provider type identifier ("chroma")
        persist_dir: Directory for persistent storage

    Example:
        >>> from providers.factory import factory
        >>> provider = factory.get_vectorstore_provider("chroma")
        >>> provider.add("my_collection", ["doc1"], ["id1"])
        >>> results = provider.query("my_collection", query_text="search", n_results=5)
    """

    NAME = "chroma"

    def __init__(
        self,
        persist_dir: str = "./data/chroma",
        embedding_provider: BaseEmbeddingProvider | None = None,
    ) -> None:
        """Initialize ChromaProvider.

        Args:
            persist_dir: Directory for persistent storage.
            embedding_provider: Optional embedding provider for auto-embedding.
        """
        self._persist_dir = persist_dir
        self._embedding_provider = embedding_provider
        self._client: chromadb.PersistentClient | None = None
        self._embedding_function: ChromaEmbeddingFunction | None = None

    def _get_client(self) -> chromadb.PersistentClient:
        """Get or create ChromaDB client (lazy initialization)."""
        if self._client is None:
            Path(self._persist_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"Initializing ChromaDB client with persist_dir: {self._persist_dir}")
            self._client = chromadb.PersistentClient(path=self._persist_dir)
        return self._client

    def _get_embedding_function(self) -> ChromaEmbeddingFunction | None:
        """Get or create embedding function."""
        if self._embedding_function is None and self._embedding_provider is not None:
            self._embedding_function = ChromaEmbeddingFunction(self._embedding_provider)
        return self._embedding_function

    @property
    def persist_dir(self) -> str:
        """Get the persist directory."""
        return self._persist_dir

    def create_collection(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Create a new collection."""
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid collection name: {name}")

        final_metadata = metadata if metadata else {"created_by": "raghub_mcp"}
        embedding_function = self._get_embedding_function()

        client = self._get_client()
        client.get_or_create_collection(
            name=name,
            metadata=final_metadata,
            embedding_function=embedding_function,
        )
        logger.debug(f"Created collection: {name}")

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        client = self._get_client()
        client.delete_collection(name=name)
        logger.debug(f"Deleted collection: {name}")

    def list_collections(self) -> list[str]:
        """List all collection names."""
        client = self._get_client()
        return [c.name for c in client.list_collections()]

    def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        try:
            client = self._get_client()
            client.get_collection(name=name)
            return True
        except Exception:
            return False

    def add(
        self,
        collection: str,
        documents: list[str],
        ids: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        """Add documents to a collection."""
        if not documents:
            return

        client = self._get_client()
        chroma_collection = client.get_or_create_collection(
            name=collection,
            embedding_function=self._get_embedding_function(),
        )

        wrapper = ChromaCollectionWrapper(chroma_collection)
        wrapper.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
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
        """Query documents using vector similarity."""
        if query_text is None and query_embedding is None:
            raise ValueError("Either query_text or query_embedding must be provided")

        client = self._get_client()
        chroma_collection = client.get_collection(name=collection)

        wrapper = ChromaCollectionWrapper(chroma_collection)

        if query_text is not None:
            result = wrapper.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where,
                where_document=where_document,
            )
        else:
            result = wrapper.query(
                query_embeddings=[query_embedding],  # type: ignore
                n_results=n_results,
                where=where,
                where_document=where_document,
            )

        # Convert to SearchResult objects
        results: list[SearchResult] = []
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for i in range(len(ids)):
            results.append(
                SearchResult(
                    id=str(ids[i]),
                    document=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    score=distances[i] if i < len(distances) else 0.0,
                )
            )

        return QueryResult(results=results)

    def get(
        self,
        collection: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[SearchResult]:
        """Retrieve documents from a collection."""
        client = self._get_client()
        chroma_collection = client.get_collection(name=collection)

        wrapper = ChromaCollectionWrapper(chroma_collection)
        result = wrapper.get(
            ids=ids,
            where=where,
            limit=limit,
            offset=offset,
        )

        results: list[SearchResult] = []
        result_ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        for i in range(len(result_ids)):
            results.append(
                SearchResult(
                    id=str(result_ids[i]),
                    document=documents[i] if i < len(documents) else "",
                    metadata=metadatas[i] if i < len(metadatas) else {},
                )
            )

        return results

    def delete(
        self,
        collection: str,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> int:
        """Delete documents from a collection."""
        client = self._get_client()
        chroma_collection = client.get_collection(name=collection)

        count_before = chroma_collection.count()

        wrapper = ChromaCollectionWrapper(chroma_collection)
        wrapper.delete(ids=ids, where=where)

        count_after = chroma_collection.count()
        return count_before - count_after

    def count(self, collection: str) -> int:
        """Count documents in a collection."""
        client = self._get_client()
        chroma_collection = client.get_collection(name=collection)
        return chroma_collection.count()

    def update(
        self,
        collection: str,
        ids: list[str],
        documents: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> None:
        """Update existing documents in a collection."""
        client = self._get_client()
        chroma_collection = client.get_collection(name=collection)

        wrapper = ChromaCollectionWrapper(chroma_collection)
        wrapper.update(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.debug(f"Updated {len(ids)} documents in collection '{collection}'")

    def reset(self) -> None:
        """Reset all collections (for testing)."""
        client = self._get_client()
        for coll in client.list_collections():
            client.delete_collection(name=coll.name)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> ChromaProvider:
        """Create an instance from configuration dictionary.

        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - persist_dir: Storage directory (optional)
                   - embedding_provider: Optional embedding provider instance

        Returns:
            New ChromaProvider instance
        """
        embedding_provider = config.get("embedding_provider")

        # If no embedding provider provided, try to get from factory
        if embedding_provider is None:
            try:
                from src.providers.factory import factory

                embedding_provider = factory.get_embedding_provider()
            except Exception:
                # No embedding provider available, will use ChromaDB default
                pass

        return cls(
            persist_dir=config.get("persist_dir", "./data/chroma"),
            embedding_provider=embedding_provider,
        )
