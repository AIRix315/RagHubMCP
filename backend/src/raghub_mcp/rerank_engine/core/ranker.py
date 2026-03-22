"""BaseRankStrategy abstract interface and ScoredDocument dataclass.

This module defines the abstract interface for ranking strategies
and the ScoredDocument dataclass for intermediate results.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.2.2
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScoredDocument:
    """A document with its computed relevance score.

    Intermediate data structure used between scoring and ranking phases.
    Carries all information needed for ranking strategies and final output.

    Attributes:
        document_id: Unique identifier for the document.
        text: The document text content.
        score: Relevance score from the scorer, typically in [0, 1].
        metadata: Additional document metadata (source, timestamp, etc.).
        original_index: Position in the original input document list.

    Example:
        >>> doc = ScoredDocument(
        ...     document_id="doc-123",
        ...     text="Machine learning is...",
        ...     score=0.85,
        ...     metadata={"source": "wiki"},
        ...     original_index=0,
        ... )
    """

    document_id: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    original_index: int = 0

    def __lt__(self, other: ScoredDocument) -> bool:
        """Enable sorting by score (descending order).

        Higher scores should sort first, so we invert the comparison.

        Args:
            other: Another ScoredDocument to compare with.

        Returns:
            True if this document should sort before the other.
        """
        return self.score > other.score

    def __eq__(self, other: object) -> bool:
        """Check equality based on document_id and score."""
        if not isinstance(other, ScoredDocument):
            return NotImplemented
        return self.document_id == other.document_id and self.score == other.score


class BaseRankStrategy(ABC):
    """Abstract base class for ranking strategies.

    A RankStrategy determines how documents are ordered based on their
    scores. Different strategies can implement:
    - Standard sorting by score
    - Diversity-aware ranking (MMR)
    - Position-aware blending
    - Weighted fusion of multiple scores

    The ranking phase is decoupled from scoring, allowing:
    - Different ordering strategies for the same scores
    - Post-processing integration (thresholds, diversity)
    - Observable and configurable ranking behavior

    Attributes:
        name: Unique identifier for this strategy.

    Example:
        >>> class MyStrategy(BaseRankStrategy):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my-strategy"
        ...
        ...     def rank(self, scored_docs, top_k=5):
        ...         return sorted(scored_docs)[:top_k]
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Strategy name identifier.

        Used for logging, debugging, and configuration.

        Returns:
            Unique name for this strategy.
        """
        ...

    @abstractmethod
    def rank(
        self,
        scored_docs: list[ScoredDocument],
        top_k: int | None = None,
        **kwargs: Any,
    ) -> list[ScoredDocument]:
        """Rank documents based on their scores.

        Args:
            scored_docs: List of documents with computed scores.
            top_k: Maximum number of documents to return. None returns all.
            **kwargs: Strategy-specific parameters.

        Returns:
            List of documents sorted by relevance (highest first).
            Length is min(top_k, len(scored_docs)) if top_k is set.

        Example:
            >>> ranked = strategy.rank(scored_docs, top_k=5)
            >>> for doc in ranked:
            ...     print(f"{doc.document_id}: {doc.score}")
        """
        ...

    def get_config(self) -> dict[str, Any]:
        """Get strategy configuration for logging/debugging.

        Returns:
            Dictionary with strategy configuration.
        """
        return {"name": self.name}