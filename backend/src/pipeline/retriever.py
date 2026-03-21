"""Retriever interface for RAG Pipeline.

This module defines the Retriever abstract base class for document
retrieval in the RAG pipeline.

Reference:
- Docs/11-V2-Desing.md (Section 5)
- Docs/12-V2-Blueprint.md (Module 1)
- RULE.md (RULE-2: 所有模块必须接口化)
- RULE.md (RULE-3: 禁止在模块中直接依赖具体实现)
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from .result import Document

logger = logging.getLogger(__name__)


class Retriever(ABC):
    """Abstract base class for document retrievers.
    
    All retriever implementations must inherit from this class and
    implement the retrieve() method.
    
    Supported retrieval methods:
    - Vector Search: Semantic similarity search
    - BM25: Lexical matching search
    - Hybrid: Combination of vector and BM25 (RRF)
    
    Example:
        >>> class MyRetriever(Retriever):
        ...     async def retrieve(self, query: str, options: dict) -> list[Document]:
        ...         # Implementation
        ...         return [Document(id="1", text="doc", score=0.9)]
    """
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Retrieve documents for a query.
        
        Args:
            query: The search query string.
            options: Optional retrieval options:
                - collection: Collection name to query
                - topK: Number of results to retrieve
                - where: Metadata filter
                
        Returns:
            List of Document objects sorted by relevance.
        """
        pass
    
    @property
    def name(self) -> str:
        """Get retriever name."""
        return self.__class__.__name__


def reciprocal_rank_fusion(
    vector_results: list[tuple[str, float]],
    bm25_results: list[tuple[str, float]],
    k: int = 60,
    alpha: float = 0.5,
    beta: float = 0.5,
) -> list[tuple[str, float]]:
    """Apply Reciprocal Rank Fusion (RRF) to combine rankings.
    
    RRF formula: score(d) = alpha * Σ 1/(k + rank_v(d)) + beta * Σ 1/(k + rank_b(d))
    
    Args:
        vector_results: List of (doc_id, score) from vector search.
        bm25_results: List of (doc_id, score) from BM25 search.
        k: RRF constant (default: 60). Higher values make ranking differences smaller.
        alpha: Weight for vector search results (default: 0.5).
        beta: Weight for BM25 search results (default: 0.5).
        
    Returns:
        List of (doc_id, fused_score) tuples, sorted by score descending.
    """
    fused_scores: dict[str, float] = defaultdict(float)
    
    # Add vector search contributions
    for rank, (doc_id, _) in enumerate(vector_results, start=1):
        fused_scores[doc_id] += alpha / (k + rank)
    
    # Add BM25 search contributions
    for rank, (doc_id, _) in enumerate(bm25_results, start=1):
        fused_scores[doc_id] += beta / (k + rank)
    
    # Sort by fused score descending
    sorted_results = sorted(
        fused_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    return sorted_results


def normalize_scores(
    results: list[tuple[str, float]],
    method: str = "minmax",
) -> list[tuple[str, float]]:
    """Normalize scores to [0, 1] range.
    
    Args:
        results: List of (doc_id, score) tuples.
        method: Normalization method - "minmax" or "rank".
        
    Returns:
        List of (doc_id, normalized_score) tuples.
    """
    if not results:
        return results
    
    if method == "rank":
        # Rank-based normalization: 1/rank
        n = len(results)
        return [
            (doc_id, 1.0 - (rank - 1) / max(n - 1, 1))
            for rank, (doc_id, _) in enumerate(results, start=1)
        ]
    
    # Min-max normalization
    scores = [score for _, score in results]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score
    
    if score_range == 0:
        # All scores are the same
        return [(doc_id, 1.0) for doc_id, _ in results]
    
    return [
        (doc_id, (score - min_score) / score_range)
        for doc_id, score in results
    ]


class HybridRetriever(Retriever):
    """Hybrid retriever combining vector and BM25 search.
    
    This retriever uses Provider interfaces (RULE-3 compliant) to provide
    combined vector and lexical search results using RRF fusion.
    
    Attributes:
        alpha: Weight for vector search (default: 0.5)
        beta: Weight for BM25 search (default: 0.5)
        rrf_k: RRF constant (default: 60)
    """
    
    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        rrf_k: int = 60,
    ) -> None:
        """Initialize hybrid retriever.
        
        Args:
            alpha: Weight for vector search (default: 0.5)
            beta: Weight for BM25 search (default: 0.5)
            rrf_k: RRF constant (default: 60)
        """
        self._alpha = alpha
        self._beta = beta
        self._rrf_k = rrf_k
        self._vectorstore_provider = None
        self._bm25_service = None
    
    def _get_vectorstore_provider(self) -> Any:
        """Get VectorStore provider through Factory (RULE-3 compliant).
        
        Returns:
            VectorStoreProvider instance from factory.
        """
        if self._vectorstore_provider is None:
            # Use Provider Factory - RULE-3 compliant
            from src.providers.factory import factory
            self._vectorstore_provider = factory.get_vectorstore_provider()
        return self._vectorstore_provider
    
    def _get_bm25_service(self) -> Any:
        """Get BM25 service instance.
        
        Returns:
            BM25Service singleton instance.
        """
        if self._bm25_service is None:
            from src.services.bm25_service import get_bm25_service
            self._bm25_service = get_bm25_service()
        return self._bm25_service
    
    async def retrieve(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Retrieve documents using hybrid search.
        
        Uses Provider interfaces directly (RULE-3 compliant) instead of
        HybridSearchService.
        
        Args:
            query: The search query string.
            options: Optional retrieval options:
                - collection: Collection name (required)
                - topK: Number of results (default: 10)
                - where: Metadata filter
                
        Returns:
            List of Document objects sorted by relevance.
        """
        options = options or {}
        
        collection = options.get("collection", "default")
        top_k = options.get("topK", 10)
        where = options.get("where")
        
        # Get providers through Factory (RULE-3 compliant)
        vectorstore = self._get_vectorstore_provider()
        bm25_service = self._get_bm25_service()
        
        # Perform vector search
        vector_results = self._vector_search(
            vectorstore, collection, query, top_k * 2, where
        )
        
        # Perform BM25 search
        bm25_results = self._bm25_search(
            bm25_service, collection, query, top_k * 2
        )
        
        # Check if we have any results
        if not vector_results and not bm25_results:
            logger.info(f"No results found for '{collection}' with query: {query[:50]}...")
            return []
        
        # Apply RRF fusion
        fused_results = self._fuse_results(vector_results, bm25_results)
        
        # Build final documents with details
        return await self._build_documents(
            fused_results[:top_k],
            vectorstore,
            collection,
            vector_results,
            bm25_results,
        )
    
    def _vector_search(
        self,
        vectorstore_provider: Any,
        collection: str,
        query: str,
        k: int,
        where: dict[str, Any] | None,
    ) -> list[tuple[str, float]]:
        """Perform vector similarity search using Provider interface.
        
        Args:
            vectorstore_provider: VectorStoreProvider instance.
            collection: Collection to search.
            query: Query text.
            k: Number of results.
            where: Optional metadata filter.
            
        Returns:
            List of (doc_id, distance) tuples.
        """
        try:
            # Use Provider interface (RULE-3 compliant)
            results = vectorstore_provider.query(
                collection=collection,
                query_text=query,
                n_results=k,
                where=where,
            )
            
            # Convert QueryResult to (doc_id, score) pairs
            # Provider returns distance (lower = more similar)
            # Convert to similarity score: 1/(1+distance)
            return [(r.id, r.score) for r in results.results]
            
        except ValueError as e:
            # Collection not found - re-raise
            logger.error(f"Collection '{collection}' not found: {e}")
            raise
        except Exception as e:
            # Other errors - log and return empty for graceful degradation
            logger.warning(f"Vector search failed for '{collection}': {e}")
            return []
    
    def _bm25_search(
        self,
        bm25_service: Any,
        collection: str,
        query: str,
        k: int,
    ) -> list[tuple[str, float]]:
        """Perform BM25 lexical search.
        
        Args:
            bm25_service: BM25Service instance.
            collection: Collection to search.
            query: Query text.
            k: Number of results.
            
        Returns:
            List of (doc_id, score) tuples.
        """
        try:
            return bm25_service.query(collection, query, k)
        except Exception as e:
            # BM25 index may not exist for all collections
            logger.debug(f"BM25 search not available for '{collection}': {e}")
            return []
    
    def _fuse_results(
        self,
        vector_results: list[tuple[str, float]],
        bm25_results: list[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        """Fuse vector and BM25 results using RRF.
        
        Args:
            vector_results: Vector search results.
            bm25_results: BM25 search results.
            
        Returns:
            Fused results sorted by combined score.
        """
        # Normalize vector scores (distance to similarity)
        vector_normalized = [
            (doc_id, 1.0 / (1.0 + dist)) 
            for doc_id, dist in vector_results
        ]
        
        # Normalize BM25 scores
        bm25_normalized = normalize_scores(bm25_results, method="minmax")
        
        # Apply RRF
        return reciprocal_rank_fusion(
            vector_normalized,
            bm25_normalized,
            k=self._rrf_k,
            alpha=self._alpha,
            beta=self._beta,
        )
    
    async def _build_documents(
        self,
        fused_results: list[tuple[str, float]],
        vectorstore_provider: Any,
        collection: str,
        vector_results: list[tuple[str, float]],
        bm25_results: list[tuple[str, float]],
    ) -> list[Document]:
        """Build final Document objects using Provider interface.
        
        Args:
            fused_results: Fused (doc_id, score) results.
            vectorstore_provider: VectorStoreProvider for fetching document details.
            collection: Collection name.
            vector_results: Original vector results.
            bm25_results: Original BM25 results.
            
        Returns:
            List of Document objects.
        """
        # Build lookup dictionaries
        vector_scores = {doc_id: score for doc_id, score in vector_results}
        bm25_scores = {doc_id: score for doc_id, score in bm25_results}
        
        # Get all doc IDs to fetch
        doc_ids = [doc_id for doc_id, _ in fused_results]
        
        # Fetch document details using Provider interface
        try:
            search_results = vectorstore_provider.get(
                collection=collection,
                ids=doc_ids,
            )
            
            # Build lookup for documents and metadata
            docs_map = {r.id: r.document for r in search_results}
            metas_map = {r.id: r.metadata for r in search_results}
        except Exception as e:
            logger.warning(f"Failed to fetch document details: {e}")
            docs_map = {}
            metas_map = {}
        
        # Build final results
        documents = []
        for rank, (doc_id, score) in enumerate(fused_results, start=1):
            doc = Document(
                id=doc_id,
                text=docs_map.get(doc_id, ""),
                score=round(score, 6),
                vector_score=round(vector_scores.get(doc_id, 0.0), 6),
                bm25_score=round(bm25_scores.get(doc_id, 0.0), 6),
                metadata=metas_map.get(doc_id) or {},
            )
            documents.append(doc)
        
        return documents
    
    @property
    def alpha(self) -> float:
        """Get vector search weight."""
        return self._alpha
    
    @property
    def beta(self) -> float:
        """Get BM25 search weight."""
        return self._beta


class VectorRetriever(Retriever):
    """Vector-only retriever using semantic similarity.
    
    This retriever uses vector similarity search only via the
    BaseVectorStoreProvider interface.
    """
    
    def __init__(self, collection: str = "default") -> None:
        """Initialize vector retriever.
        
        Args:
            collection: Collection name to query.
        """
        self._collection = collection
    
    async def retrieve(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Retrieve documents using vector similarity.
        
        Args:
            query: The search query string.
            options: Optional retrieval options:
                - collection: Collection name
                - topK: Number of results
                - where: Metadata filter
                
        Returns:
            List of Document objects sorted by relevance.
        """
        options = options or {}
        
        collection = options.get("collection", self._collection)
        top_k = options.get("topK", 10)
        where = options.get("where")
        
        # Use VectorDBProvider interface (RULE-3 compliance)
        # Uses default provider from config - configuration driven
        from src.providers.factory import factory
        
        vectorstore = factory.get_vectorstore_provider()
        
        result = vectorstore.query(
            collection=collection,
            query_text=query,
            n_results=top_k,
            where=where,
        )
        
        documents = []
        for search_result in result.results:
            # Convert distance-based score from ChromaDB
            # ChromaDB returns distance (lower = better), we convert to score (higher = better)
            distance = search_result.score
            # Handle None or negative distance as default 0.0
            if distance is not None and distance >= 0:
                score = 1.0 / (1.0 + distance)
            else:
                score = 0.0
            
            # Handle None metadata
            metadata = search_result.metadata if search_result.metadata is not None else {}
            
            doc = Document(
                id=search_result.id,
                text=search_result.document,
                score=score,
                metadata=metadata,
                vector_score=score,
            )
            documents.append(doc)
        
        return documents