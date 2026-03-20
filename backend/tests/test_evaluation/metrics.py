"""RAG Evaluation Metrics.

This module provides metrics for evaluating RAG pipeline quality.

Reference:
- Docs/12-V2-Blueprint.md (Section 3.2)
- RULE.md (Section 7: 测试验收标准)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """Result of evaluating RAG pipeline performance.
    
    Attributes:
        hit_rate: Top-K hit rate (percentage of correct results in top K).
        avg_relevance_score: Average relevance score.
        noise_ratio: Ratio of irrelevant results.
        total_queries: Number of queries evaluated.
    """
    hit_rate: float
    avg_relevance_score: float
    noise_ratio: float
    total_queries: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hit_rate": round(self.hit_rate, 2),
            "avg_relevance_score": round(self.avg_relevance_score, 2),
            "noise_ratio": round(self.noise_ratio, 2),
            "total_queries": self.total_queries,
        }


def calculate_top_k_hit_rate(
    expected_ids: list[str],
    retrieved_ids: list[str],
    k: int = 3,
) -> float:
    """Calculate Top-K hit rate.
    
    Args:
        expected_ids: List of expected document IDs.
        retrieved_ids: List of retrieved document IDs.
        k: Top K results to consider.
        
    Returns:
        Hit rate as a percentage (0-100).
    """
    if not expected_ids or not retrieved_ids:
        return 0.0
    
    top_k = retrieved_ids[:k]
    hits = sum(1 for expected in expected_ids if expected in top_k)
    
    return (hits / len(expected_ids)) * 100


def calculate_relevance_score(
    retrieved_docs: list[dict[str, Any]],
    expected_keywords: list[str],
) -> float:
    """Calculate average relevance score based on keyword presence.
    
    Args:
        retrieved_docs: List of retrieved documents with text.
        expected_keywords: List of expected keywords.
        
    Returns:
        Average relevance score (0-1).
    """
    if not retrieved_docs or not expected_keywords:
        return 0.0
    
    total_score = 0.0
    
    for doc in retrieved_docs:
        text = doc.get("text", "").lower()
        keyword_matches = sum(
            1 for kw in expected_keywords 
            if kw.lower() in text
        )
        score = keyword_matches / len(expected_keywords)
        total_score += score
    
    return total_score / len(retrieved_docs)


def calculate_noise_ratio(
    retrieved_docs: list[dict[str, Any]],
    relevant_keywords: list[str],
) -> float:
    """Calculate ratio of irrelevant documents.
    
    Args:
        retrieved_docs: List of retrieved documents.
        relevant_keywords: Keywords that indicate relevance.
        
    Returns:
        Noise ratio (0-1, lower is better).
    """
    if not retrieved_docs:
        return 0.0
    
    irrelevant_count = 0
    
    for doc in retrieved_docs:
        text = doc.get("text", "").lower()
        is_relevant = any(kw.lower() in text for kw in relevant_keywords)
        if not is_relevant:
            irrelevant_count += 1
    
    return irrelevant_count / len(retrieved_docs)


def evaluate_pipeline(
    queries: list[dict[str, Any]],
    retrieval_results: dict[int, list[dict[str, Any]]],
    k: int = 3,
) -> EvaluationResult:
    """Evaluate pipeline performance across multiple queries.
    
    Args:
        queries: List of test questions.
        retrieval_results: Dictionary mapping query ID to retrieved documents.
        k: Top K to consider for hit rate.
        
    Returns:
        EvaluationResult with metrics.
    """
    total_queries = len(queries)
    total_hit_rate = 0.0
    total_relevance = 0.0
    total_noise = 0.0
    
    for query in queries:
        qid = query.get("id")
        expected_keywords = query.get("keywords", [])
        
        retrieved = retrieval_results.get(qid, [])
        
        # Calculate metrics
        hit_rate = calculate_top_k_hit_rate(
            expected_ids=[],  # Would need ground truth IDs
            retrieved_ids=[d.get("id", "") for d in retrieved],
            k=k,
        )
        relevance = calculate_relevance_score(retrieved, expected_keywords)
        noise = calculate_noise_ratio(retrieved, expected_keywords)
        
        total_hit_rate += hit_rate
        total_relevance += relevance
        total_noise += noise
    
    return EvaluationResult(
        hit_rate=total_hit_rate / total_queries if total_queries > 0 else 0,
        avg_relevance_score=total_relevance / total_queries if total_queries > 0 else 0,
        noise_ratio=total_noise / total_queries if total_queries > 0 else 0,
        total_queries=total_queries,
    )