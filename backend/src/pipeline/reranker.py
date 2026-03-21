"""Reranker interface for RAG Pipeline.

This module defines the Reranker abstract base class for document
reranking in the RAG pipeline.

Reference:
- Docs/11-V2-Desing.md (Section 6)
- Docs/12-V2-Blueprint.md (Module 2)
- RULE.md (RULE-2: 所有模块必须接口化)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .result import Document


class Reranker(ABC):
    """Abstract base class for document rerankers.

    All reranker implementations must inherit from this class and
    implement the rerank() method.

    Reranking is a critical component of the RAG pipeline that
    re-orders retrieved documents based on their relevance to the query.

    Supported implementations:
    - FlashRank: Local CPU-based reranking
    - Cohere: API-based reranking
    - Jina: API-based reranking

    Example:
        >>> class MyReranker(Reranker):
        ...     async def rerank(self, query: str, docs: list[Document]) -> list[Document]:
        ...         # Implementation
        ...         return docs
    """

    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: list[Document],
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Rerank documents by relevance to query.

        Args:
            query: The search query string.
            documents: List of documents to rerank.
            options: Optional reranking options:
                - topK: Number of results to return

        Returns:
            List of Document objects sorted by relevance (reranked).
        """
        pass

    @property
    def name(self) -> str:
        """Get reranker name."""
        return self.__class__.__name__


class PipelineReranker(Reranker):
    """Reranker implementation using FlashRank.

    This reranker wraps the existing FlashRank provider to provide
    document reranking capability in the pipeline.

    Attributes:
        model: FlashRank model name.
        top_k: Default number of results to return.
    """

    def __init__(
        self,
        model: str = "ms-marco-TinyBERT-L-2-v2",
        top_k: int = 5,
    ) -> None:
        """Initialize pipeline reranker.

        Args:
            model: FlashRank model name (default: TinyBERT).
            top_k: Default number of results to return.
        """
        self._model = model
        self._top_k = top_k
        self._provider = None

    async def rerank(
        self,
        query: str,
        documents: list[Document],
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Rerank documents using FlashRank.

        Args:
            query: The search query string.
            documents: List of documents to rerank.
            options: Optional reranking options:
                - top_k: Number of results to return

        Returns:
            List of Document objects sorted by relevance.
        """
        if not documents:
            return []

        options = options or {}
        top_k = options.get("top_k", self._top_k)

        # Lazy import to avoid circular dependency
        from src.providers.factory import factory

        # Get rerank provider from factory
        rerank_provider = factory.get_rerank_provider()

        if rerank_provider is None:
            # No reranker available, return original documents
            return documents[:top_k]

        # Extract text for reranking
        texts = [doc.text for doc in documents]

        # Perform reranking
        results = await rerank_provider.arerank(
            query=query,
            documents=texts,
            top_k=min(top_k, len(texts)),
        )

        # Map back to Document objects
        reranked_docs = []
        for result in results:
            original_doc = documents[result.index]
            doc = Document(
                id=original_doc.id,
                text=result.text,
                score=result.score,
                metadata=original_doc.metadata,
                vector_score=original_doc.vector_score,
                bm25_score=original_doc.bm25_score,
                rerank_score=result.score,
            )
            reranked_docs.append(doc)

        return reranked_docs

    @property
    def model(self) -> str:
        """Get model name."""
        return self._model

    @property
    def top_k(self) -> int:
        """Get default top_k."""
        return self._top_k


class NoOpReranker(Reranker):
    """No-op reranker that returns documents as-is.

    This reranker is used when reranking is disabled.
    """

    async def rerank(
        self,
        query: str,
        documents: list[Document],
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Return documents without reranking.

        Args:
            query: The search query string.
            documents: List of documents.
            options: Optional reranking options:
                - topK: Number of results to return

        Returns:
            Original documents (potentially truncated to topK).
        """
        options = options or {}
        top_k = options.get("topK", len(documents))
        return documents[:top_k]


class FallbackReranker(Reranker):
    """Reranker with fallback mechanism.

    This reranker wraps another reranker and falls back to the original
    order if reranking fails.
    """

    def __init__(
        self,
        primary: Reranker,
        fallback: Reranker | None = None,
    ) -> None:
        """Initialize fallback reranker.

        Args:
            primary: Primary reranker to use.
            fallback: Fallback reranker if primary fails.
        """
        self._primary = primary
        self._fallback = fallback or NoOpReranker()

    async def rerank(
        self,
        query: str,
        documents: list[Document],
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Rerank with fallback on error.

        Args:
            query: The search query string.
            documents: List of documents to rerank.
            options: Optional reranking options.

        Returns:
            Reranked documents or fallback results.
        """
        try:
            return await self._primary.rerank(query, documents, options)
        except Exception:
            # Fallback to original order
            return await self._fallback.rerank(query, documents, options)
