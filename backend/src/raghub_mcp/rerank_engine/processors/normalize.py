"""NormalizeProcessor - Score normalization.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..core.processor import BasePostProcessor


class NormalizeProcessor(BasePostProcessor):
    """Score normalization processor.

    Normalizes scores to [0, 1] range using different methods.

    Attributes:
        method: Normalization method ("minmax" or "softmax").

    Example:
        >>> processor = NormalizeProcessor(method="minmax")
        >>> processed = processor.process(np.array([0, 5, 10]), docs)
        # Result: [0.0, 0.5, 1.0]
    """

    def __init__(self, method: str = "minmax") -> None:
        """Initialize normalize processor.

        Args:
            method: Normalization method ("minmax" or "softmax").
        """
        self._method = method

    @property
    def name(self) -> str:
        """Processor name."""
        return "normalize"

    @property
    def method(self) -> str:
        """Get normalization method."""
        return self._method

    def process(
        self,
        scores: np.ndarray,
        documents: list[str],
        **kwargs: Any,
    ) -> np.ndarray:
        """Normalize scores.

        Args:
            scores: Raw scores.
            documents: Document texts (unused).
            **kwargs: Additional parameters.

        Returns:
            Normalized scores in [0, 1].
        """
        if self._method == "minmax":
            return self._minmax_normalize(scores)
        elif self._method == "softmax":
            return self._softmax_normalize(scores)
        else:
            raise ValueError(f"Unknown normalization method: {self._method}")

    def _minmax_normalize(self, scores: np.ndarray) -> np.ndarray:
        """Min-max normalization to [0, 1]."""
        min_val = float(np.min(scores))
        max_val = float(np.max(scores))

        if max_val == min_val:
            # All values are the same
            return np.ones_like(scores) * 0.5

        result: np.ndarray = (scores - min_val) / (max_val - min_val)
        return result

    def _softmax_normalize(self, scores: np.ndarray) -> np.ndarray:
        """Softmax normalization (sum to 1)."""
        exp_scores: np.ndarray = np.exp(scores - np.max(scores))
        result: np.ndarray = exp_scores / np.sum(exp_scores)
        return result

    def get_config(self) -> dict[str, Any]:
        """Get processor configuration."""
        return {
            "name": self.name,
            "method": self._method,
        }
