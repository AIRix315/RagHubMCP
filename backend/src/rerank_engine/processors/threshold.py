"""ThresholdProcessor - Score threshold filtering.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..core.processor import BasePostProcessor


class ThresholdProcessor(BasePostProcessor):
    """Score threshold processor.

    Filters out scores below a minimum threshold by setting them to 0.

    Attributes:
        min_score: Minimum score threshold (default: 0.0).

    Example:
        >>> processor = ThresholdProcessor(min_score=0.5)
        >>> processed = processor.process(np.array([0.3, 0.7]), ["d1", "d2"])
        # Result: [0.0, 0.7]
    """

    def __init__(self, min_score: float = 0.0) -> None:
        """Initialize threshold processor.

        Args:
            min_score: Minimum score threshold.
        """
        self._min_score = min_score

    @property
    def name(self) -> str:
        """Processor name."""
        return "threshold"

    @property
    def min_score(self) -> float:
        """Get minimum score threshold."""
        return self._min_score

    def process(
        self,
        scores: np.ndarray,
        documents: list[str],
        **kwargs: Any,
    ) -> np.ndarray:
        """Apply threshold filter.

        Args:
            scores: Raw scores.
            documents: Document texts (unused for threshold).
            **kwargs: Additional parameters.

        Returns:
            Scores with values below threshold set to 0.
        """
        return np.where(scores >= self._min_score, scores, 0.0)

    def get_config(self) -> dict[str, Any]:
        """Get processor configuration."""
        return {
            "name": self.name,
            "min_score": self._min_score,
        }