"""Tests for RerankEngine core abstractions.

Test cases for V2.1:
- TC-1.1.1: BaseScorer interface contract
- TC-1.1.2: BaseRankStrategy interface contract  
- TC-1.1.3: BasePostProcessor interface contract
- ScoredDocument dataclass

Reference: Docs/20-RerankEngine-Architecture.md Section 4.2
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


# =============================================================================
# TC-1.1.1: BaseScorer Tests
# =============================================================================


class TestBaseScorer:
    """Tests for BaseScorer abstract interface (TC-1.1.1)."""

    def test_base_scorer_is_abstract(self):
        """TC-1.1.1: BaseScorer cannot be instantiated directly."""
        from rerank_engine.core.scorer import BaseScorer

        with pytest.raises(TypeError):
            BaseScorer()

    def test_base_scorer_requires_name_property(self):
        """TC-1.1.1: Concrete scorer must implement name property."""
        from rerank_engine.core.scorer import BaseScorer

        with pytest.raises(TypeError):

            class IncompleteScorer(BaseScorer):
                @property
                def supports_batch(self) -> bool:
                    return True

                def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
                    return np.array([])

            IncompleteScorer()

    def test_base_scorer_requires_supports_batch_property(self):
        """TC-1.1.1: Concrete scorer must implement supports_batch property."""
        from rerank_engine.core.scorer import BaseScorer

        with pytest.raises(TypeError):

            class IncompleteScorer(BaseScorer):
                @property
                def name(self) -> str:
                    return "test"

                def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
                    return np.array([])

            IncompleteScorer()

    def test_base_scorer_requires_compute_scores_method(self):
        """TC-1.1.1: Concrete scorer must implement compute_scores method."""
        from rerank_engine.core.scorer import BaseScorer

        with pytest.raises(TypeError):

            class IncompleteScorer(BaseScorer):
                @property
                def name(self) -> str:
                    return "test"

                @property
                def supports_batch(self) -> bool:
                    return True

            IncompleteScorer()

    def test_concrete_scorer_implementation(self):
        """TC-1.1.1: A properly implemented scorer works correctly."""
        from rerank_engine.core.scorer import BaseScorer

        class MockScorer(BaseScorer):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def supports_batch(self) -> bool:
                return True

            def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
                return np.ones(len(documents)) * 0.5

        scorer = MockScorer()
        assert scorer.name == "mock"
        assert scorer.supports_batch is True

        scores = scorer.compute_scores("test", ["doc1", "doc2"])
        assert len(scores) == 2
        assert np.allclose(scores, [0.5, 0.5])

    def test_compute_scores_batch_default_implementation(self):
        """TC-1.1.1: Default batch implementation delegates to single compute_scores."""
        from rerank_engine.core.scorer import BaseScorer

        class MockScorer(BaseScorer):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def supports_batch(self) -> bool:
                return False

            def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
                return np.ones(len(documents)) * 0.5

        scorer = MockScorer()
        results = scorer.compute_scores_batch(["q1", "q2"], [["d1", "d2"], ["d3"]])

        assert len(results) == 2
        assert np.allclose(results[0], [0.5, 0.5])
        assert np.allclose(results[1], [0.5])

    def test_empty_documents_returns_empty_array(self):
        """TC-1.1.1: Scorer handles empty document list correctly."""
        from rerank_engine.core.scorer import BaseScorer

        class MockScorer(BaseScorer):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def supports_batch(self) -> bool:
                return True

            def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
                return np.array([]) if not documents else np.ones(len(documents))

        scorer = MockScorer()
        scores = scorer.compute_scores("test", [])
        assert len(scores) == 0

    def test_scorer_get_config(self):
        """TC-1.1.1: Scorer provides configuration info."""
        from rerank_engine.core.scorer import BaseScorer

        class MockScorer(BaseScorer):
            @property
            def name(self) -> str:
                return "mock"

            @property
            def supports_batch(self) -> bool:
                return True

            def compute_scores(self, query: str, documents: list[str]) -> np.ndarray:
                return np.array([])

        scorer = MockScorer()
        config = scorer.get_config()

        assert config["name"] == "mock"
        assert config["supports_batch"] is True


# =============================================================================
# ScoredDocument Tests
# =============================================================================


class TestScoredDocument:
    """Tests for ScoredDocument dataclass."""

    def test_scored_document_creation(self):
        """ScoredDocument can be created with all fields."""
        from rerank_engine.core.ranker import ScoredDocument

        doc = ScoredDocument(
            document_id="doc1",
            text="Sample text",
            score=0.85,
            metadata={"source": "test"},
            original_index=0,
        )

        assert doc.document_id == "doc1"
        assert doc.text == "Sample text"
        assert doc.score == 0.85
        assert doc.metadata == {"source": "test"}
        assert doc.original_index == 0

    def test_scored_document_default_metadata(self):
        """ScoredDocument uses empty dict as default metadata."""
        from rerank_engine.core.ranker import ScoredDocument

        doc = ScoredDocument(document_id="doc1", text="text", score=0.5)

        assert doc.metadata == {}
        assert doc.original_index == 0

    def test_scored_document_comparison_descending(self):
        """ScoredDocument sorts by score descending (higher score first)."""
        from rerank_engine.core.ranker import ScoredDocument

        doc_high = ScoredDocument("d1", "text", 0.9, {}, 0)
        doc_low = ScoredDocument("d2", "text", 0.5, {}, 1)

        # Higher score should be "less than" for descending sort
        assert doc_high < doc_low
        assert doc_low > doc_high

    def test_scored_document_sorting(self):
        """ScoredDocument can be sorted by score."""
        from rerank_engine.core.ranker import ScoredDocument

        docs = [
            ScoredDocument("d1", "", 0.3, {}, 0),
            ScoredDocument("d2", "", 0.9, {}, 1),
            ScoredDocument("d3", "", 0.5, {}, 2),
        ]

        sorted_docs = sorted(docs)
        assert sorted_docs[0].score == 0.9
        assert sorted_docs[1].score == 0.5
        assert sorted_docs[2].score == 0.3


# =============================================================================
# TC-1.1.2: BaseRankStrategy Tests
# =============================================================================


class TestBaseRankStrategy:
    """Tests for BaseRankStrategy abstract interface (TC-1.1.2)."""

    def test_base_strategy_is_abstract(self):
        """TC-1.1.2: BaseRankStrategy cannot be instantiated directly."""
        from rerank_engine.core.ranker import BaseRankStrategy

        with pytest.raises(TypeError):
            BaseRankStrategy()

    def test_base_strategy_requires_name_property(self):
        """TC-1.1.2: Concrete strategy must implement name property."""
        from rerank_engine.core.ranker import BaseRankStrategy, ScoredDocument

        with pytest.raises(TypeError):

            class IncompleteStrategy(BaseRankStrategy):
                def rank(
                    self,
                    scored_docs: list[ScoredDocument],
                    top_k: int | None = None,
                    **kwargs,
                ) -> list[ScoredDocument]:
                    return scored_docs

            IncompleteStrategy()

    def test_base_strategy_requires_rank_method(self):
        """TC-1.1.2: Concrete strategy must implement rank method."""
        from rerank_engine.core.ranker import BaseRankStrategy

        with pytest.raises(TypeError):

            class IncompleteStrategy(BaseRankStrategy):
                @property
                def name(self) -> str:
                    return "test"

            IncompleteStrategy()

    def test_concrete_strategy_implementation(self):
        """TC-1.1.2: A properly implemented strategy works correctly."""
        from rerank_engine.core.ranker import BaseRankStrategy, ScoredDocument

        class MockStrategy(BaseRankStrategy):
            @property
            def name(self) -> str:
                return "mock"

            def rank(
                self,
                scored_docs: list[ScoredDocument],
                top_k: int | None = None,
                **kwargs,
            ) -> list[ScoredDocument]:
                sorted_docs = sorted(scored_docs, key=lambda x: x.score, reverse=True)
                if top_k:
                    return sorted_docs[:top_k]
                return sorted_docs

        strategy = MockStrategy()
        assert strategy.name == "mock"

        docs = [
            ScoredDocument("d1", "text1", 0.3, {}, 0),
            ScoredDocument("d2", "text2", 0.9, {}, 1),
            ScoredDocument("d3", "text3", 0.5, {}, 2),
        ]

        ranked = strategy.rank(docs, top_k=2)
        assert len(ranked) == 2
        assert ranked[0].score == 0.9
        assert ranked[1].score == 0.5

    def test_strategy_get_config(self):
        """TC-1.1.2: Strategy provides configuration info."""
        from rerank_engine.core.ranker import BaseRankStrategy, ScoredDocument

        class MockStrategy(BaseRankStrategy):
            @property
            def name(self) -> str:
                return "mock"

            def rank(
                self,
                scored_docs: list[ScoredDocument],
                top_k: int | None = None,
                **kwargs,
            ) -> list[ScoredDocument]:
                return sorted(scored_docs)[: (top_k if top_k else len(scored_docs))]

        strategy = MockStrategy()
        config = strategy.get_config()

        assert config["name"] == "mock"


# =============================================================================
# TC-1.1.3: BasePostProcessor Tests
# =============================================================================


class TestBasePostProcessor:
    """Tests for BasePostProcessor abstract interface (TC-1.1.3)."""

    def test_base_processor_is_abstract(self):
        """TC-1.1.3: BasePostProcessor cannot be instantiated directly."""
        from rerank_engine.core.processor import BasePostProcessor

        with pytest.raises(TypeError):
            BasePostProcessor()

    def test_base_processor_requires_name_property(self):
        """TC-1.1.3: Concrete processor must implement name property."""
        from rerank_engine.core.processor import BasePostProcessor

        with pytest.raises(TypeError):

            class IncompleteProcessor(BasePostProcessor):
                def process(
                    self, scores: np.ndarray, documents: list[str], **kwargs
                ) -> np.ndarray:
                    return scores

            IncompleteProcessor()

    def test_base_processor_requires_process_method(self):
        """TC-1.1.3: Concrete processor must implement process method."""
        from rerank_engine.core.processor import BasePostProcessor

        with pytest.raises(TypeError):

            class IncompleteProcessor(BasePostProcessor):
                @property
                def name(self) -> str:
                    return "test"

            IncompleteProcessor()

    def test_concrete_processor_implementation(self):
        """TC-1.1.3: A properly implemented processor works correctly."""
        from rerank_engine.core.processor import BasePostProcessor

        class MockProcessor(BasePostProcessor):
            @property
            def name(self) -> str:
                return "mock"

            def process(
                self, scores: np.ndarray, documents: list[str], **kwargs
            ) -> np.ndarray:
                return scores * 2

        processor = MockProcessor()
        assert processor.name == "mock"

        scores = np.array([0.1, 0.5, 0.9])
        processed = processor.process(scores, ["d1", "d2", "d3"])

        assert np.allclose(processed, [0.2, 1.0, 1.8])

    def test_processor_preserves_shape(self):
        """TC-1.1.3: Processor should preserve array shape."""
        from rerank_engine.core.processor import BasePostProcessor

        class IdentityProcessor(BasePostProcessor):
            @property
            def name(self) -> str:
                return "identity"

            def process(
                self, scores: np.ndarray, documents: list[str], **kwargs
            ) -> np.ndarray:
                return scores

        processor = IdentityProcessor()
        scores = np.array([0.1, 0.5, 0.9])
        processed = processor.process(scores, ["d1", "d2", "d3"])

        assert processed.shape == scores.shape

    def test_processor_get_config(self):
        """TC-1.1.3: Processor provides configuration info."""
        from rerank_engine.core.processor import BasePostProcessor

        class MockProcessor(BasePostProcessor):
            @property
            def name(self) -> str:
                return "mock"

            def process(
                self, scores: np.ndarray, documents: list[str], **kwargs
            ) -> np.ndarray:
                return scores

        processor = MockProcessor()
        config = processor.get_config()

        assert config["name"] == "mock"


# =============================================================================
# Data Models Tests
# =============================================================================


class TestRerankModels:
    """Tests for RerankRequest, RerankResult, and RerankContext models."""

    def test_rerank_request_creation(self):
        """RerankRequest can be created with required fields."""
        from rerank_engine.models import RerankRequest

        request = RerankRequest(
            query="test query",
            documents=[{"id": "1", "text": "doc1"}, {"id": "2", "text": "doc2"}],
        )

        assert request.query == "test query"
        assert len(request.documents) == 2
        assert request.top_k is None

    def test_rerank_request_with_options(self):
        """RerankRequest accepts optional configuration."""
        from rerank_engine.models import RerankRequest

        request = RerankRequest(
            query="test",
            documents=[{"id": "1", "text": "doc"}],
            top_k=5,
            scorer_config={"batch_size": 32},
        )

        assert request.top_k == 5
        assert request.scorer_config == {"batch_size": 32}

    def test_rerank_result_creation(self):
        """RerankResult can be created with all fields."""
        from rerank_engine.models import RerankResult

        result = RerankResult(
            document_id="doc1",
            text="Sample text",
            score=0.85,
            rank=1,
            metadata={"source": "test"},
            original_index=0,
        )

        assert result.document_id == "doc1"
        assert result.rank == 1
        assert result.processing_info == {}

    def test_rerank_result_to_dict(self):
        """RerankResult can be converted to dictionary."""
        from rerank_engine.models import RerankResult

        result = RerankResult(
            document_id="doc1",
            text="Sample text",
            score=0.85,
            rank=1,
            metadata={"source": "test"},
            original_index=0,
        )

        d = result.to_dict()
        assert d["document_id"] == "doc1"
        assert d["score"] == 0.85
        assert d["rank"] == 1

    def test_rerank_context_creation(self):
        """RerankContext can be created and tracks processing."""
        from rerank_engine.models import RerankContext, RerankRequest

        request = RerankRequest(query="test", documents=[])
        context = RerankContext(request=request)

        assert context.request == request
        assert context.intermediate_scores == {}
        assert context.processing_steps == []
        assert context.latency_ms == 0.0

    def test_rerank_context_add_step(self):
        """RerankContext can record processing steps."""
        from rerank_engine.models import RerankContext, RerankRequest

        request = RerankRequest(query="test", documents=[])
        context = RerankContext(request=request)

        context.add_step("scoring", {"model": "test"})
        context.add_step("ranking", {})

        assert len(context.processing_steps) == 2
        assert context.processing_steps[0]["name"] == "scoring"

    def test_rerank_context_to_dict(self):
        """RerankContext can be converted to dictionary."""
        from rerank_engine.models import RerankContext, RerankRequest

        request = RerankRequest(query="test", documents=[])
        context = RerankContext(
            request=request,
            latency_ms=42.5,
            scorer_name="onnx",
            rank_strategy_name="standard",
        )

        d = context.to_dict()
        assert d["latency_ms"] == 42.5
        assert d["scorer_name"] == "onnx"