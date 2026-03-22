"""RerankEngine - Composable reranking for RAG pipelines.

This module provides the core reranking engine with:
- Pluggable scorers (ONNX, API, Vector)
- Configurable ranking strategies
- Score post-processing pipeline
- Full observability of intermediate states

Reference: Docs/20-RerankEngine-Architecture.md
"""

from .models import (
    RerankContext,
    RerankRequest,
    RerankResult,
    RankStrategyType,
    ScorerType,
)
from .core import BaseScorer, BaseRankStrategy, BasePostProcessor, ScoredDocument

__all__ = [
    # Models
    "RerankRequest",
    "RerankResult",
    "RerankContext",
    "ScorerType",
    "RankStrategyType",
    # Core abstractions
    "BaseScorer",
    "BaseRankStrategy",
    "BasePostProcessor",
    "ScoredDocument",
]