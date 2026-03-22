"""Tests for score post-processors.

Test cases for V2.1 Task 1.5:
- TC-1.5.1: ThresholdProcessor
- TC-1.5.2: NormalizeProcessor

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


# =============================================================================
# TC-1.5.1: ThresholdProcessor Tests
# =============================================================================


class TestThresholdProcessor:
    """Tests for ThresholdProcessor (TC-1.5.1)."""

    def test_threshold_processor_import(self):
        """TC-1.5.1: ThresholdProcessor can be imported."""
        from rerank_engine.processors.threshold import ThresholdProcessor

        assert ThresholdProcessor is not None

    def test_threshold_processor_is_base_processor(self):
        """TC-1.5.1: ThresholdProcessor is a BasePostProcessor."""
        from rerank_engine.core.processor import BasePostProcessor
        from rerank_engine.processors.threshold import ThresholdProcessor

        assert issubclass(ThresholdProcessor, BasePostProcessor)

    def test_threshold_processor_name(self):
        """TC-1.5.1: ThresholdProcessor has correct name."""
        from rerank_engine.processors.threshold import ThresholdProcessor

        processor = ThresholdProcessor()
        assert processor.name == "threshold"

    def test_threshold_processor_default_min_score(self):
        """TC-1.5.1: ThresholdProcessor has default min_score."""
        from rerank_engine.processors.threshold import ThresholdProcessor

        processor = ThresholdProcessor()
        assert processor.min_score == 0.0

    def test_threshold_processor_custom_min_score(self):
        """TC-1.5.1: ThresholdProcessor accepts custom min_score."""
        from rerank_engine.processors.threshold import ThresholdProcessor

        processor = ThresholdProcessor(min_score=0.3)
        assert processor.min_score == 0.3

    def test_threshold_processor_filters_low_scores(self):
        """TC-1.5.1: ThresholdProcessor filters scores below threshold."""
        from rerank_engine.processors.threshold import ThresholdProcessor

        processor = ThresholdProcessor(min_score=0.5)

        scores = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        documents = ["d1", "d2", "d3", "d4", "d5"]

        processed = processor.process(scores, documents)

        # Scores below 0.5 should be set to 0
        assert processed[0] == 0.0
        assert processed[1] == 0.0
        assert processed[2] == 0.5
        assert processed[3] == 0.7
        assert processed[4] == 0.9

    def test_threshold_processor_preserves_shape(self):
        """TC-1.5.1: ThresholdProcessor preserves array shape."""
        from rerank_engine.processors.threshold import ThresholdProcessor

        processor = ThresholdProcessor(min_score=0.5)

        scores = np.array([0.1, 0.9])
        documents = ["d1", "d2"]

        processed = processor.process(scores, documents)
        assert processed.shape == scores.shape


# =============================================================================
# TC-1.5.2: NormalizeProcessor Tests
# =============================================================================


class TestNormalizeProcessor:
    """Tests for NormalizeProcessor (TC-1.5.2)."""

    def test_normalize_processor_import(self):
        """TC-1.5.2: NormalizeProcessor can be imported."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        assert NormalizeProcessor is not None

    def test_normalize_processor_is_base_processor(self):
        """TC-1.5.2: NormalizeProcessor is a BasePostProcessor."""
        from rerank_engine.core.processor import BasePostProcessor
        from rerank_engine.processors.normalize import NormalizeProcessor

        assert issubclass(NormalizeProcessor, BasePostProcessor)

    def test_normalize_processor_name(self):
        """TC-1.5.2: NormalizeProcessor has correct name."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        processor = NormalizeProcessor()
        assert processor.name == "normalize"

    def test_normalize_processor_default_method(self):
        """TC-1.5.2: NormalizeProcessor has default method."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        processor = NormalizeProcessor()
        assert processor.method == "minmax"

    def test_normalize_processor_minmax(self):
        """TC-1.5.2: NormalizeProcessor performs minmax normalization."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        processor = NormalizeProcessor(method="minmax")

        scores = np.array([0.0, 5.0, 10.0])
        documents = ["d1", "d2", "d3"]

        processed = processor.process(scores, documents)

        # MinMax: (x - min) / (max - min)
        expected = np.array([0.0, 0.5, 1.0])
        np.testing.assert_allclose(processed, expected)

    def test_normalize_processor_softmax(self):
        """TC-1.5.2: NormalizeProcessor performs softmax normalization."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        processor = NormalizeProcessor(method="softmax")

        scores = np.array([1.0, 2.0, 3.0])
        documents = ["d1", "d2", "d3"]

        processed = processor.process(scores, documents)

        # Softmax results should sum to 1
        assert np.isclose(np.sum(processed), 1.0)
        # All values should be in [0, 1]
        assert np.all(processed >= 0)
        assert np.all(processed <= 1)

    def test_normalize_processor_handles_constant_scores(self):
        """TC-1.5.2: NormalizeProcessor handles constant scores."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        processor = NormalizeProcessor(method="minmax")

        scores = np.array([0.5, 0.5, 0.5])
        documents = ["d1", "d2", "d3"]

        processed = processor.process(scores, documents)

        # When all values are the same, should return uniform distribution
        # or the original values
        assert len(processed) == 3

    def test_normalize_processor_preserves_shape(self):
        """TC-1.5.2: NormalizeProcessor preserves array shape."""
        from rerank_engine.processors.normalize import NormalizeProcessor

        processor = NormalizeProcessor()

        scores = np.array([0.1, 0.5, 0.9])
        documents = ["d1", "d2", "d3"]

        processed = processor.process(scores, documents)
        assert processed.shape == scores.shape


class TestProcessorChaining:
    """Tests for chaining multiple processors."""

    def test_threshold_then_normalize(self):
        """Processors can be chained: threshold then normalize."""
        from rerank_engine.processors.normalize import NormalizeProcessor
        from rerank_engine.processors.threshold import ThresholdProcessor

        threshold = ThresholdProcessor(min_score=0.3)
        normalize = NormalizeProcessor(method="minmax")

        scores = np.array([0.1, 0.5, 0.9])
        documents = ["d1", "d2", "d3"]

        # Apply threshold first
        after_threshold = threshold.process(scores, documents)
        # Then normalize
        after_normalize = normalize.process(after_threshold, documents)

        assert len(after_normalize) == 3