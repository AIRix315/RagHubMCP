"""BasePostProcessor abstract interface for score post-processing.

This module defines the abstract interface for post-processing components
that transform raw scores before ranking.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.2.3
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


class BasePostProcessor(ABC):
    """Abstract base class for score post-processors.

    A PostProcessor transforms raw scores from the scorer before ranking.
    Common operations include:
    - Threshold filtering (remove low scores)
    - Score normalization (min-max, softmax)
    - Temperature scaling
    - Score clipping

    Multiple processors can be chained in sequence.

    Attributes:
        name: Unique identifier for this processor.

    Example:
        >>> class ThresholdProcessor(BasePostProcessor):
        ...     @property
        ...     def name(self) -> str:
        ...         return "threshold"
        ...
        ...     def process(self, scores, documents, min_score=0.3):
        ...         return np.where(scores >= min_score, scores, 0.0)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Processor name identifier.

        Used for logging, debugging, and configuration.

        Returns:
            Unique name for this processor.
        """
        ...

    @abstractmethod
    def process(
        self,
        scores: np.ndarray,
        documents: list[str],
        **kwargs: Any,
    ) -> np.ndarray:
        """Process raw scores.

        Args:
            scores: Raw scores from the scorer, shape (n_documents,).
            documents: Corresponding document texts for context.
            **kwargs: Processor-specific parameters.

        Returns:
            Processed scores with same shape as input.

        Note:
            - Processors should not change the number of documents.
            - Document order must be preserved.
            - Use 0.0 score to indicate "filtered out" rather than removing.
        """
        ...

    def get_config(self) -> dict[str, Any]:
        """Get processor configuration for logging/debugging.

        Returns:
            Dictionary with processor configuration.
        """
        return {"name": self.name}