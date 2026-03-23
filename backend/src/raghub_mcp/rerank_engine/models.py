"""RerankEngine data models.

This module defines data models for rerank requests, results,
and execution context.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.3
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np


class ScorerType(StrEnum):
    """Scorer type enumeration."""

    ONNX = "onnx"
    API = "api"
    VECTOR = "vector"
    HYBRID = "hybrid"
    CUSTOM = "custom"


class RankStrategyType(StrEnum):
    """Rank strategy type enumeration."""

    STANDARD = "standard"
    DIVERSITY = "diversity"
    WEIGHTED = "weighted"
    POSITION_AWARE = "position_aware"


@dataclass
class RerankRequest:
    """Rerank request data model.

    Encapsulates all information needed for a rerank operation.

    Attributes:
        query: The search query string.
        documents: List of document dicts with 'id', 'text', and optional 'metadata'.
        top_k: Maximum number of results to return. None returns all.
        scorer_config: Configuration for the scorer (batch_size, etc.).
        rank_strategy_config: Configuration for the rank strategy.
        post_processors: List of post-processor configurations.

    Example:
        >>> request = RerankRequest(
        ...     query="machine learning",
        ...     documents=[
        ...         {"id": "1", "text": "ML is a subset of AI."},
        ...         {"id": "2", "text": "Python is a language."},
        ...     ],
        ...     top_k=5,
        ... )
    """

    query: str
    documents: list[dict[str, Any]]
    top_k: int | None = None
    scorer_config: dict[str, Any] = field(default_factory=dict)
    rank_strategy_config: dict[str, Any] = field(default_factory=dict)
    post_processors: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RerankResult:
    """Rerank result data model.

    Represents a single document in the ranked result list.

    Attributes:
        document_id: Unique identifier for the document.
        text: The document text content.
        score: Final relevance score after processing.
        rank: Position in the ranked result list (1-indexed).
        metadata: Additional document metadata.
        original_index: Position in the original input document list.
        processing_info: Debug information about score transformations.

    Example:
        >>> result = RerankResult(
        ...     document_id="doc-1",
        ...     text="Machine learning is...",
        ...     score=0.85,
        ...     rank=1,
        ...     metadata={"source": "wiki"},
        ...     original_index=0,
        ... )
    """

    document_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any] = field(default_factory=dict)
    original_index: int = 0
    processing_info: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "document_id": self.document_id,
            "text": self.text,
            "score": self.score,
            "rank": self.rank,
            "metadata": self.metadata,
            "original_index": self.original_index,
            "processing_info": self.processing_info,
        }


@dataclass
class RerankContext:
    """Rerank execution context for debugging and observability.

    Tracks the complete execution state for debugging, logging,
    and performance analysis.

    Attributes:
        request: The original rerank request.
        intermediate_scores: Scores at each processing stage.
        processing_steps: List of processing step records.
        latency_ms: Total execution time in milliseconds.
        scorer_name: Name of the scorer used.
        rank_strategy_name: Name of the rank strategy used.

    Example:
        >>> context = RerankContext(request=request)
        >>> context.intermediate_scores["raw"] = raw_scores
        >>> context.intermediate_scores["normalized"] = normalized_scores
        >>> context.latency_ms = 42.5
    """

    request: RerankRequest
    intermediate_scores: dict[str, np.ndarray] = field(default_factory=dict)
    processing_steps: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
    scorer_name: str = ""
    rank_strategy_name: str = ""

    def add_step(self, name: str, details: dict[str, Any] | None = None) -> None:
        """Record a processing step.

        Args:
            name: Step name (e.g., "scoring", "threshold_filter").
            details: Optional step details.
        """
        self.processing_steps.append(
            {
                "name": name,
                "details": details or {},
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "latency_ms": self.latency_ms,
            "scorer_name": self.scorer_name,
            "rank_strategy_name": self.rank_strategy_name,
            "processing_steps": self.processing_steps,
            "intermediate_score_keys": list(self.intermediate_scores.keys()),
        }
