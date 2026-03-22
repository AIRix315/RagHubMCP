"""BaseScorer abstract interface for rerank scoring.

This module defines the abstract interface for scoring components
that compute relevance scores between queries and documents.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.2.1
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BaseScorer(ABC):
    """Abstract base class for scoring components.

    A Scorer computes relevance scores between a query and documents.
    All concrete scoring implementations (ONNX, API, Vector, etc.) must
    inherit from this class.

    The scoring process is decoupled from ranking, allowing:
    - Different scoring engines (local models, API, hybrid)
    - Score post-processing before ranking
    - Observable intermediate states

    Attributes:
        name: Unique identifier for this scorer type.
        supports_batch: Whether the scorer supports batch processing.

    Example:
        >>> class MyScorer(BaseScorer):
        ...     @property
        ...     def name(self) -> str:
        ...         return "my-scorer"
        ...
        ...     @property
        ...     def supports_batch(self) -> bool:
        ...         return True
        ...
        ...     def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
        ...         return np.array([0.5, 0.8, 0.3])
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Scorer name identifier.

        Used for logging, debugging, and configuration.

        Returns:
            Unique name for this scorer instance.
        """
        ...

    @property
    @abstractmethod
    def supports_batch(self) -> bool:
        """Whether the scorer supports batch processing.

        Batch processing allows scoring multiple query-document pairs
        in a single call for better efficiency.

        Returns:
            True if batch processing is supported.
        """
        ...

    @abstractmethod
    def compute_scores(
        self,
        query: str,
        documents: list[str],
    ) -> np.ndarray:
        """Compute relevance scores for query-document pairs.

        Args:
            query: The search query string.
            documents: List of document texts to score.

        Returns:
            NumPy array of shape (len(documents),) with scores in [0, 1].
            Higher scores indicate higher relevance.

        Raises:
            ScorerError: If scoring fails.
        """
        ...

    def compute_scores_batch(
        self,
        queries: list[str],
        documents_list: list[list[str]],
    ) -> list[np.ndarray]:
        """Compute scores for multiple query-document pairs.

        Default implementation iterates over single compute_scores.
        Subclasses that support efficient batching should override this.

        Args:
            queries: List of query strings.
            documents_list: List of document lists, one per query.

        Returns:
            List of score arrays, one per query.

        Example:
            >>> scorer.compute_scores_batch(
            ...     ["query1", "query2"],
            ...     [["doc1", "doc2"], ["doc3"]]
            ... )
            [array([0.5, 0.8]), array([0.3])]
        """
        return [
            self.compute_scores(q, docs)
            for q, docs in zip(queries, documents_list)
        ]

    def get_config(self) -> dict[str, Any]:
        """Get scorer configuration for logging/debugging.

        Returns:
            Dictionary with scorer configuration.
        """
        return {
            "name": self.name,
            "supports_batch": self.supports_batch,
        }