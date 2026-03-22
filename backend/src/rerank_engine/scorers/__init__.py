"""Scorers module.

This module provides various scoring implementations for computing
relevance scores between queries and documents.

Available Scorers:
- ONNXScorer: Neural reranker using ONNX runtime (FlashRank models)
- BM25Scorer: Traditional BM25 lexical scoring
- VectorScorer: Vector similarity scoring (cosine, dot, euclidean)
- HybridFusionScorer: Combines multiple scorers with fusion strategies
- APIScorer: External API rerank (Cohere, Jina)
- CohereScorer: Cohere rerank API
- JinaScorer: Jina rerank API

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

from .onnx_scorer import ONNXScorer
from .bm25_scorer import BM25Scorer
from .vector_scorer import VectorScorer
from .hybrid_scorer import HybridFusionScorer
from .api_scorer import APIScorer, CohereScorer, JinaScorer, create_api_scorer

__all__ = [
    "ONNXScorer",
    "BM25Scorer",
    "VectorScorer",
    "HybridFusionScorer",
    "APIScorer",
    "CohereScorer",
    "JinaScorer",
    "create_api_scorer",
]