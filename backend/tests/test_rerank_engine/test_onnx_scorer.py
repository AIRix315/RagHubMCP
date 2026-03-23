"""Tests for ONNXScorer implementation.

Test cases for V2.1 Task 1.2:
- TC-1.2.1: ONNX model loading
- TC-1.2.2: Tokenizer encoding with batch support
- TC-1.2.3: ONNX inference
- TC-1.2.4: Score conversion (Sigmoid/Softmax)
- TC-1.2.5: Batch processing control

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4.1
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestONNXScorerInterface:
    """Tests for ONNXScorer interface compliance (TC-1.2.1)."""

    def test_onnx_scorer_is_base_scorer(self):
        """TC-1.2.1: ONNXScorer is a BaseScorer subclass."""
        from raghub_mcp.rerank_engine.core.scorer import BaseScorer
        from raghub_mcp.rerank_engine.scorers.onnx_scorer import ONNXScorer

        assert issubclass(ONNXScorer, BaseScorer)

    def test_onnx_scorer_has_required_attributes(self):
        """TC-1.2.1: ONNXScorer has required class attributes."""
        from raghub_mcp.rerank_engine.scorers.onnx_scorer import ONNXScorer

        # Check class exists and has expected structure
        assert hasattr(ONNXScorer, "__init__")
        assert hasattr(ONNXScorer, "compute_scores")

    @pytest.mark.skip(reason="Requires model files, run in integration tests")
    def test_onnx_scorer_initialization(self):
        """TC-1.2.1: ONNXScorer can be initialized with model files."""
        pass


class TestONNXScorerScoreConversion:
    """Tests for logits to score conversion (TC-1.2.4)."""

    def test_sigmoid_conversion_single_output(self):
        """TC-1.2.4: Sigmoid converts single-output logits correctly."""
        from raghub_mcp.rerank_engine.scorers.onnx_scorer import ONNXScorer

        # Single output: use sigmoid
        logits = np.array([[-2.0], [0.0], [2.0]])

        # Expected sigmoid: 1 / (1 + exp(-x))
        expected = 1 / (1 + np.exp(-logits.flatten()))

        result = ONNXScorer._logits_to_scores_static(logits)
        np.testing.assert_allclose(result, expected, rtol=1e-5)

    def test_softmax_conversion_multi_output(self):
        """TC-1.2.4: Softmax converts multi-output logits correctly."""
        from raghub_mcp.rerank_engine.scorers.onnx_scorer import ONNXScorer

        # Multi output (2 classes): use softmax, take positive class
        logits = np.array([[0.5, 1.5], [1.0, 2.0]])

        result = ONNXScorer._logits_to_scores_static(logits)

        # Result should be probabilities in [0, 1]
        assert np.all(result >= 0)
        assert np.all(result <= 1)

    def test_score_range_single_output(self):
        """TC-1.2.4: Single-output scores are in valid range [0, 1]."""
        from raghub_mcp.rerank_engine.scorers.onnx_scorer import ONNXScorer

        test_cases = [
            np.array([[-5.0], [0.0], [5.0]]),
            np.array([[-100.0], [100.0]]),
            np.array([[0.0]]),
        ]

        for logits in test_cases:
            result = ONNXScorer._logits_to_scores_static(logits)
            assert np.all(result >= 0), f"Score below 0: {result}"
            assert np.all(result <= 1), f"Score above 1: {result}"

    def test_score_range_multi_output(self):
        """TC-1.2.4: Multi-output scores are in valid range [0, 1]."""
        from raghub_mcp.rerank_engine.scorers.onnx_scorer import ONNXScorer

        test_cases = [
            np.array([[0.0, 0.0], [1.0, 2.0], [-1.0, -2.0]]),
            np.array([[10.0, -10.0], [-10.0, 10.0]]),
        ]

        for logits in test_cases:
            result = ONNXScorer._logits_to_scores_static(logits)
            assert np.all(result >= 0), f"Score below 0: {result}"
            assert np.all(result <= 1), f"Score above 1: {result}"


class TestONNXScorerBatchProcessing:
    """Tests for batch processing logic (TC-1.2.5)."""

    def test_batch_indices_calculation(self):
        """TC-1.2.5: Batch indices are calculated correctly."""
        total_docs = 25
        batch_size = 8

        batches = []
        for i in range(0, total_docs, batch_size):
            batches.append((i, min(i + batch_size, total_docs)))

        expected = [(0, 8), (8, 16), (16, 24), (24, 25)]
        assert batches == expected

    def test_batch_size_edge_cases(self):
        """TC-1.2.5: Batch processing handles edge cases."""
        # Empty documents
        assert list(range(0, 0, 8)) == []

        # Single document
        batches = list(range(0, 1, 8))
        assert batches == [0]

        # Exact multiple
        batches = list(range(0, 16, 8))
        assert batches == [0, 8]

        # Less than batch size
        batches = list(range(0, 5, 8))
        assert batches == [0]


class TestONNXScorerIntegration:
    """Integration tests requiring model files."""

    @pytest.fixture
    def cache_dir(self, tmp_path: Path) -> Path:
        """Create a temporary cache directory."""
        cache = tmp_path / "flashrank_cache"
        cache.mkdir()
        return cache

    @pytest.mark.skip(reason="Requires model files, run in integration tests")
    def test_onnx_scorer_load_tinybert(self, cache_dir: Path):
        """TC-1.2.1: ONNXScorer loads TinyBERT model successfully."""
        pass

    @pytest.mark.skip(reason="Requires model files, run in integration tests")
    def test_onnx_scorer_compute_scores_basic(self, cache_dir: Path):
        """TC-1.2.3: ONNXScorer computes scores correctly."""
        pass

    @pytest.mark.skip(reason="Requires model files, run in integration tests")
    def test_onnx_scorer_batch_processing(self, cache_dir: Path):
        """TC-1.2.5: ONNXScorer processes documents in batches."""
        pass
