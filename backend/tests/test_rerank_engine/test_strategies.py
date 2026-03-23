"""Tests for ranking strategies.

Test cases for V2.1 Task 1.4:
- TC-1.4.1: StandardRankStrategy
- TC-1.4.2: DiversityRankStrategy (MMR)

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4.3
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


# =============================================================================
# TC-1.4.1: StandardRankStrategy Tests
# =============================================================================


class TestStandardRankStrategy:
    """Tests for StandardRankStrategy (TC-1.4.1)."""

    def test_standard_strategy_import(self):
        """TC-1.4.1: StandardRankStrategy can be imported."""
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        assert StandardRankStrategy is not None

    def test_standard_strategy_is_base_strategy(self):
        """TC-1.4.1: StandardRankStrategy is a BaseRankStrategy."""
        from raghub_mcp.rerank_engine.core.ranker import BaseRankStrategy
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        assert issubclass(StandardRankStrategy, BaseRankStrategy)

    def test_standard_strategy_name(self):
        """TC-1.4.1: StandardRankStrategy has correct name."""
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        strategy = StandardRankStrategy()
        assert strategy.name == "standard"

    def test_standard_strategy_sorts_by_score_descending(self):
        """TC-1.4.1: StandardRankStrategy sorts by score descending."""
        from raghub_mcp.rerank_engine.core.ranker import ScoredDocument
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        strategy = StandardRankStrategy()

        docs = [
            ScoredDocument("d1", "text1", 0.3, {}, 0),
            ScoredDocument("d2", "text2", 0.9, {}, 1),
            ScoredDocument("d3", "text3", 0.5, {}, 2),
        ]

        ranked = strategy.rank(docs)

        assert ranked[0].score == 0.9
        assert ranked[1].score == 0.5
        assert ranked[2].score == 0.3

    def test_standard_strategy_respects_top_k(self):
        """TC-1.4.1: StandardRankStrategy respects top_k parameter."""
        from raghub_mcp.rerank_engine.core.ranker import ScoredDocument
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        strategy = StandardRankStrategy()

        docs = [
            ScoredDocument("d1", "text1", 0.3, {}, 0),
            ScoredDocument("d2", "text2", 0.9, {}, 1),
            ScoredDocument("d3", "text3", 0.5, {}, 2),
        ]

        ranked = strategy.rank(docs, top_k=2)
        assert len(ranked) == 2

    def test_standard_strategy_preserves_metadata(self):
        """TC-1.4.1: StandardRankStrategy preserves document metadata."""
        from raghub_mcp.rerank_engine.core.ranker import ScoredDocument
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        strategy = StandardRankStrategy()

        docs = [
            ScoredDocument("d1", "text1", 0.9, {"source": "wiki"}, 0),
        ]

        ranked = strategy.rank(docs)
        assert ranked[0].metadata == {"source": "wiki"}

    def test_standard_strategy_empty_documents(self):
        """TC-1.4.1: StandardRankStrategy handles empty list."""
        from raghub_mcp.rerank_engine.strategies.standard import StandardRankStrategy

        strategy = StandardRankStrategy()
        ranked = strategy.rank([])
        assert ranked == []


# =============================================================================
# TC-1.4.2: DiversityRankStrategy Tests
# =============================================================================


class TestDiversityRankStrategy:
    """Tests for DiversityRankStrategy with MMR (TC-1.4.2)."""

    def test_diversity_strategy_import(self):
        """TC-1.4.2: DiversityRankStrategy can be imported."""
        from raghub_mcp.rerank_engine.strategies.diversity import DiversityRankStrategy

        assert DiversityRankStrategy is not None

    def test_diversity_strategy_is_base_strategy(self):
        """TC-1.4.2: DiversityRankStrategy is a BaseRankStrategy."""
        from raghub_mcp.rerank_engine.core.ranker import BaseRankStrategy
        from raghub_mcp.rerank_engine.strategies.diversity import DiversityRankStrategy

        assert issubclass(DiversityRankStrategy, BaseRankStrategy)

    def test_diversity_strategy_name(self):
        """TC-1.4.2: DiversityRankStrategy has correct name."""
        from raghub_mcp.rerank_engine.strategies.diversity import DiversityRankStrategy

        strategy = DiversityRankStrategy()
        assert strategy.name == "diversity"

    def test_diversity_strategy_lambda_parameter(self):
        """TC-1.4.2: DiversityRankStrategy accepts lambda parameter."""
        from raghub_mcp.rerank_engine.strategies.diversity import DiversityRankStrategy

        # Default lambda
        strategy_default = DiversityRankStrategy()
        assert strategy_default.lambda_param == 0.5

        # Custom lambda
        strategy_custom = DiversityRankStrategy(lambda_param=0.7)
        assert strategy_custom.lambda_param == 0.7

    def test_diversity_strategy_promotes_diversity(self):
        """TC-1.4.2: DiversityRankStrategy promotes document diversity."""
        from raghub_mcp.rerank_engine.core.ranker import ScoredDocument
        from raghub_mcp.rerank_engine.strategies.diversity import DiversityRankStrategy

        strategy = DiversityRankStrategy(lambda_param=0.5)

        # Documents with same high score but different content
        docs = [
            ScoredDocument("d1", "machine learning ai", 0.9, {}, 0),
            ScoredDocument("d2", "machine learning models", 0.9, {}, 1),
            ScoredDocument("d3", "python programming", 0.8, {}, 2),
        ]

        ranked = strategy.rank(docs, top_k=3)

        # All documents should be included
        assert len(ranked) == 3

    def test_diversity_strategy_respects_top_k(self):
        """TC-1.4.2: DiversityRankStrategy respects top_k parameter."""
        from raghub_mcp.rerank_engine.core.ranker import ScoredDocument
        from raghub_mcp.rerank_engine.strategies.diversity import DiversityRankStrategy

        strategy = DiversityRankStrategy()

        docs = [
            ScoredDocument("d1", "text1", 0.9, {}, 0),
            ScoredDocument("d2", "text2", 0.8, {}, 1),
            ScoredDocument("d3", "text3", 0.7, {}, 2),
        ]

        ranked = strategy.rank(docs, top_k=2)
        assert len(ranked) == 2


class TestRankStrategyFactory:
    """Tests for rank strategy factory."""

    def test_factory_creates_standard(self):
        """Factory can create StandardRankStrategy."""
        pass

    def test_factory_creates_diversity(self):
        """Factory can create DiversityRankStrategy."""
        pass

    def test_factory_raises_for_unknown(self):
        """Factory raises error for unknown strategy."""
        pass
