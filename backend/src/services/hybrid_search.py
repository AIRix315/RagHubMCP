"""Hybrid search service combining vector and BM25 search.

This module provides hybrid search functionality:
- Reciprocal Rank Fusion (RRF) algorithm
- Configurable weights for vector and BM25 scores
- Integration with ChromaService and BM25Service
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """A single hybrid search result.
    
    Attributes:
        id: Document ID.
        text: Document text content.
        score: Combined hybrid score.
        vector_score: Vector similarity score (normalized).
        bm25_score: BM25 lexical score (normalized).
        rank: Final rank position.
        metadata: Document metadata.
        distance: Vector distance (from ChromaDB).
    """
    id: str
    text: str
    score: float
    vector_score: float = 0.0
    bm25_score: float = 0.0
    rank: int = 0
    metadata: dict[str, Any] | None = None
    distance: float | None = None


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
    
    Reference:
        Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009).
        Reciprocal rank fusion outperforms condorcet and individual rank learning methods.
        In Proceedings of the 32nd international ACM SIGIR conference.
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


class HybridSearchService:
    """Hybrid search service combining vector and BM25 search.
    
    Provides hybrid search with:
    - Reciprocal Rank Fusion (RRF) algorithm
    - Configurable weights for vector and BM25
    - Optional score normalization
    
    Example:
        >>> service = HybridSearchService(alpha=0.6, beta=0.4)
        >>> results = service.search("my_collection", "search query", n_results=10)
    """
    
    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        rrf_k: int = 60,
        normalize: bool = True,
    ) -> None:
        """Initialize HybridSearchService.
        
        Args:
            alpha: Weight for vector search results (default: 0.5).
            beta: Weight for BM25 search results (default: 0.5).
            rrf_k: RRF constant (default: 60).
            normalize: Whether to normalize scores before fusion (default: True).
        """
        if not (0 <= alpha <= 1 and 0 <= beta <= 1):
            raise ValueError("alpha and beta must be between 0 and 1")
        
        self.alpha = alpha
        self.beta = beta
        self.rrf_k = rrf_k
        self.normalize = normalize
    
    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> list[HybridSearchResult]:
        """Perform hybrid search combining vector and BM25.
        
        Args:
            collection_name: Name of the collection to search.
            query: Search query text.
            n_results: Number of results to return.
            where: Optional metadata filter (applied to vector search only).
            
        Returns:
            List of HybridSearchResult objects, sorted by combined score.
        """
        from services.chroma_service import get_chroma_service
        from services.bm25_service import get_bm25_service
        
        # Get services
        chroma_service = get_chroma_service()
        bm25_service = get_bm25_service()
        
        # Perform vector search
        vector_results = self._vector_search(
            chroma_service, collection_name, query, n_results * 2, where
        )
        
        # Perform BM25 search
        bm25_results = self._bm25_search(
            bm25_service, collection_name, query, n_results * 2
        )
        
        # Apply RRF fusion
        fused_results = self._fuse_results(vector_results, bm25_results)
        
        # Build final results with document details
        return self._build_results(
            fused_results[:n_results],
            chroma_service,
            collection_name,
            vector_results,
            bm25_results,
        )
    
    def _vector_search(
        self,
        chroma_service,
        collection_name: str,
        query: str,
        k: int,
        where: dict[str, Any] | None,
    ) -> list[tuple[str, float]]:
        """Perform vector similarity search.
        
        Args:
            chroma_service: ChromaService instance.
            collection_name: Collection to search.
            query: Query text.
            k: Number of results.
            where: Optional metadata filter.
            
        Returns:
            List of (doc_id, distance) tuples.
        """
        try:
            results = chroma_service.query(
                collection_name=collection_name,
                query_text=query,
                n_results=k,
                where=where,
            )
            
            # Convert distances to scores (lower distance = higher similarity)
            # ChromaDB uses cosine distance by default, so we invert
            ids = results.get("ids", [])
            distances = results.get("distances", [])
            
            # Return (doc_id, distance) pairs
            return list(zip(ids, distances))
            
        except Exception as e:
            logger.warning(f"Vector search failed: {e}")
            return []
    
    def _bm25_search(
        self,
        bm25_service,
        collection_name: str,
        query: str,
        k: int,
    ) -> list[tuple[str, float]]:
        """Perform BM25 lexical search.
        
        Args:
            bm25_service: BM25Service instance.
            collection_name: Collection to search.
            query: Query text.
            k: Number of results.
            
        Returns:
            List of (doc_id, score) tuples.
        """
        try:
            return bm25_service.query(collection_name, query, k)
        except Exception as e:
            logger.warning(f"BM25 search failed: {e}")
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
        # Optionally normalize scores
        if self.normalize:
            # For vector, lower distance is better, so we invert
            vector_normalized = [
                (doc_id, 1.0 / (1.0 + dist)) 
                for doc_id, dist in vector_results
            ]
            bm25_normalized = normalize_scores(bm25_results, method="minmax")
        else:
            vector_normalized = vector_results
            bm25_normalized = bm25_results
        
        # Apply RRF
        return reciprocal_rank_fusion(
            vector_normalized,
            bm25_normalized,
            k=self.rrf_k,
            alpha=self.alpha,
            beta=self.beta,
        )
    
    def _build_results(
        self,
        fused_results: list[tuple[str, float]],
        chroma_service,
        collection_name: str,
        vector_results: list[tuple[str, float]],
        bm25_results: list[tuple[str, float]],
    ) -> list[HybridSearchResult]:
        """Build final HybridSearchResult objects.
        
        Args:
            fused_results: Fused (doc_id, score) results.
            chroma_service: ChromaService for fetching document details.
            collection_name: Collection name.
            vector_results: Original vector results.
            bm25_results: Original BM25 results.
            
        Returns:
            List of HybridSearchResult objects.
        """
        # Build lookup dictionaries
        vector_scores = {doc_id: score for doc_id, score in vector_results}
        bm25_scores = {doc_id: score for doc_id, score in bm25_results}
        
        # Get all doc IDs to fetch
        doc_ids = [doc_id for doc_id, _ in fused_results]
        
        # Fetch document details from ChromaDB
        try:
            collection = chroma_service.get_collection(collection_name)
            # Get documents by IDs
            doc_results = collection.get(ids=doc_ids, include=["documents", "metadatas"])
            
            # Build lookup for documents and metadata
            docs_map = {}
            metas_map = {}
            if doc_results:
                ids = doc_results.get("ids", [])
                docs = doc_results.get("documents", [])
                metas = doc_results.get("metadatas", [])
                for i, doc_id in enumerate(ids):
                    docs_map[doc_id] = docs[i] if i < len(docs) else ""
                    metas_map[doc_id] = metas[i] if i < len(metas) else {}
        except Exception as e:
            logger.warning(f"Failed to fetch document details: {e}")
            docs_map = {}
            metas_map = {}
        
        # Build final results
        results = []
        for rank, (doc_id, score) in enumerate(fused_results, start=1):
            result = HybridSearchResult(
                id=doc_id,
                text=docs_map.get(doc_id, ""),
                score=round(score, 6),
                vector_score=round(vector_scores.get(doc_id, 0.0), 6),
                bm25_score=round(bm25_scores.get(doc_id, 0.0), 6),
                rank=rank,
                metadata=metas_map.get(doc_id),
                distance=vector_scores.get(doc_id),
            )
            results.append(result)
        
        return results


# Singleton instance
_instance: HybridSearchService | None = None
_cached_params: tuple[float, float, int] | None = None


def get_hybrid_search_service(
    alpha: float | None = None,
    beta: float | None = None,
    rrf_k: int | None = None,
) -> HybridSearchService:
    """Get the singleton HybridSearchService instance.
    
    Args:
        alpha: Vector weight (optional, uses config if not provided).
        beta: BM25 weight (optional, uses config if not provided).
        rrf_k: RRF constant (optional, uses config if not provided).
    
    Returns:
        HybridSearchService singleton instance.
    """
    global _instance, _cached_params
    
    # Get config values if not provided
    if alpha is None or beta is None or rrf_k is None:
        try:
            from utils.config import get_config
            config = get_config().hybrid
            alpha = alpha if alpha is not None else config.alpha
            beta = beta if beta is not None else config.beta
            rrf_k = rrf_k if rrf_k is not None else config.rrf_k
        except (RuntimeError, AttributeError):
            alpha = alpha if alpha is not None else 0.5
            beta = beta if beta is not None else 0.5
            rrf_k = rrf_k if rrf_k is not None else 60
    
    current_params = (alpha, beta, rrf_k)
    
    # Create or return existing instance
    if _instance is None or _cached_params != current_params:
        _instance = HybridSearchService(alpha=alpha, beta=beta, rrf_k=rrf_k)
        _cached_params = current_params
    
    return _instance


def reset_hybrid_search_service() -> None:
    """Reset the singleton instance (for testing purposes)."""
    global _instance, _cached_params
    _instance = None
    _cached_params = None
    logger.debug("HybridSearchService singleton reset")