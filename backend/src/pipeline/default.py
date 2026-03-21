"""Default RAG Pipeline implementation.

This module provides the DefaultRAGPipeline implementation that
combines retrieval, reranking, and context building.

Reference:
- Docs/11-V2-Desing.md (Section 4.2)
- Docs/12-V2-Blueprint.md (Module 1.2)
- RULE.md (RULE-1: Pipeline是唯一执行入口)
"""

from __future__ import annotations

import time
from typing import Any

from .base import RAGPipeline
from .context_builder import ContextBuilder, DefaultContextBuilder
from .reranker import NoOpReranker, Reranker
from .result import RAGResult
from .retriever import HybridRetriever, Retriever


class DefaultRAGPipeline(RAGPipeline):
    """Default RAG pipeline implementation.

    This pipeline provides the standard RAG flow:
    1. Retrieval (Hybrid: vector + BM25)
    2. Reranking (FlashRank)
    3. Context Building (deduplication, sorting, truncation)

    Attributes:
        retriever: Document retriever instance.
        reranker: Document reranker instance.
        context_builder: Context builder instance.
        retrieval_multiplier: Multiplier for initial retrieval count.
    """

    # Default retrieval multiplier (retrieval_count = top_k * multiplier)
    DEFAULT_RETRIEVAL_MULTIPLIER = 2.0

    def __init__(
        self,
        retriever: Retriever | None = None,
        reranker: Reranker | None = None,
        context_builder: ContextBuilder | None = None,
        default_top_k: int = 5,
        default_rerank: bool = True,
        retrieval_multiplier: float | None = None,
    ) -> None:
        """Initialize default RAG pipeline.

        Args:
            retriever: Document retriever (default: HybridRetriever).
            reranker: Document reranker (default: PipelineReranker).
            context_builder: Context builder (default: DefaultContextBuilder).
            default_top_k: Default number of results.
            default_rerank: Whether to enable reranking by default.
            retrieval_multiplier: Multiplier for initial retrieval count.
                When None, retrieves top_k * 2 for reranking safety margin.
                Use 1.0 for no multiplication (exact top_k retrieval).
        """
        self._retriever = retriever or HybridRetriever()
        self._reranker = reranker
        self._context_builder = context_builder or DefaultContextBuilder()
        self._default_top_k = default_top_k
        self._default_rerank = default_rerank
        self._retrieval_multiplier = retrieval_multiplier or self.DEFAULT_RETRIEVAL_MULTIPLIER

    async def run(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> RAGResult:
        """Execute the RAG pipeline.

        Pipeline execution flow:
        1. Retrieve documents using the configured retriever
        2. Apply reranking if enabled
        3. Build final context using context builder
        4. Return results

        Args:
            query: The search query string.
            options: Optional configuration:
                - topK: Number of results to return
                - rerank: Whether to apply reranking
                - collection: Collection name
                - where: Metadata filter
                - profile: Profile name (affects retrieval multiplier)

        Returns:
            RAGResult containing the retrieved and processed documents.
        """
        options = options or {}

        # Parse options
        top_k = options.get("topK", self._default_top_k)
        enable_rerank = options.get("rerank", self._default_rerank)
        collection = options.get("collection", "default")
        where = options.get("where")
        profile = options.get("profile", "balanced")

        # Calculate retrieval count based on profile and multiplier
        # Use configurable multiplier instead of hardcoded value
        retrieval_multiplier = options.get("retrieval_multiplier", self._retrieval_multiplier)
        retrieval_count = int(top_k * retrieval_multiplier)

        # Track execution time
        start_time = time.time()

        # Prepare retrieval options
        retrieval_options = {
            "collection": collection,
            "topK": retrieval_count,
            "where": where,
        }

        # Step 1: Retrieval
        documents = await self._retriever.retrieve(query, retrieval_options)

        # Step 2: Reranking (if enabled and reranker available)
        if enable_rerank and self._reranker:
            rerank_options = {"top_k": top_k}
            documents = await self._reranker.rerank(query, documents, rerank_options)

        # Step 3: Context Building
        final_docs = self._context_builder.build(
            documents,
            limit=top_k,
            options={
                "remove_duplicates": True,
                "merge_consecutive": options.get("merge_consecutive", False),
            },
        )

        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000  # ms

        # Build result
        result = RAGResult(
            query=query,
            documents=final_docs,
            total_results=len(final_docs),
            execution_time_ms=execution_time,
            profile=profile,
        )

        return result

    @property
    def retriever(self) -> Retriever:
        """Get the retriever instance."""
        return self._retriever

    @property
    def reranker(self) -> Reranker | None:
        """Get the reranker instance."""
        return self._reranker

    @property
    def context_builder(self) -> ContextBuilder:
        """Get the context builder instance."""
        return self._context_builder

    def enable_reranking(self, reranker: Reranker) -> None:
        """Enable reranking with the given reranker.

        Args:
            reranker: Reranker instance to use.
        """
        self._reranker = reranker

    def disable_reranking(self) -> None:
        """Disable reranking."""
        self._reranker = NoOpReranker()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"DefaultRAGPipeline("
            f"retriever={self._retriever.name}, "
            f"reranker={self._reranker.name if self._reranker else 'None'}, "
            f"builder={self._context_builder.name})"
        )
