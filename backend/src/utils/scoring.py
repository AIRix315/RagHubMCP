"""Scoring utilities for RAG pipeline.

This module provides common scoring and ranking utilities:
- Reciprocal Rank Fusion (RRF) algorithm
- Score normalization functions
- Distance to score conversion

Reference:
- RULE.md (RULE-2: 所有模块必须接口化)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence


def reciprocal_rank_fusion(
    vector_results: Sequence[tuple[str, float]],
    bm25_results: Sequence[tuple[str, float]],
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
    results: Sequence[tuple[str, float]],
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
        return list(results)
    
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


def distance_to_score(distance: float) -> float:
    """Convert distance to similarity score.
    
    ChromaDB and similar vector databases return distance (lower = better).
    This function converts distance to a score where higher = better.
    
    Args:
        distance: Distance value (e.g., from ChromaDB query result).
        
    Returns:
        Similarity score where 1.0 is most similar, 0.0 is least similar.
    
    Example:
        >>> distance_to_score(0.0)
        1.0
        >>> distance_to_score(1.0)
        0.5
        >>> distance_to_score(float('inf'))
        0.0
    """
    if distance is None:
        return 0.0
    if distance <= 0:
        return 1.0
    return 1.0 / (1.0 + distance)
