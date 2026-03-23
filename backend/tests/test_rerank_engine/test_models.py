"""Tests for rerank_engine models.

Test cases:
- RerankRequest creation and validation
- RerankResult serialization
- RerankContext tracking
- ScorerType and RankStrategyType enums
"""

from __future__ import annotations

import numpy as np
import pytest

from raghub_mcp.rerank_engine import (
    RankStrategyType,
    RerankContext,
    RerankRequest,
    RerankResult,
    ScorerType,
)


class TestScorerTypeEnum:
    """Tests for ScorerType enum."""

    def test_scorer_types_exist(self):
        """Test all scorer types exist."""
        assert ScorerType.ONNX == "onnx"
        assert ScorerType.API == "api"
        assert ScorerType.VECTOR == "vector"
        assert ScorerType.HYBRID == "hybrid"
        assert ScorerType.CUSTOM == "custom"

    def test_scorer_type_from_string(self):
        """Test creating ScorerType from string."""
        assert ScorerType("onnx") == ScorerType.ONNX
        assert ScorerType("api") == ScorerType.API


class TestRankStrategyTypeEnum:
    """Tests for RankStrategyType enum."""

    def test_strategy_types_exist(self):
        """Test all strategy types exist."""
        assert RankStrategyType.STANDARD == "standard"
        assert RankStrategyType.DIVERSITY == "diversity"
        assert RankStrategyType.WEIGHTED == "weighted"
        assert RankStrategyType.POSITION_AWARE == "position_aware"


class TestRerankRequest:
    """Tests for RerankRequest."""

    def test_request_creation_minimal(self):
        """Test creating request with minimal fields."""
        request = RerankRequest(
            query="test query",
            documents=[{"id": "1", "text": "doc1"}],
        )

        assert request.query == "test query"
        assert len(request.documents) == 1
        assert request.top_k is None
        assert request.scorer_config == {}

    def test_request_creation_full(self):
        """Test creating request with all fields."""
        request = RerankRequest(
            query="test query",
            documents=[
                {"id": "1", "text": "doc1"},
                {"id": "2", "text": "doc2"},
            ],
            top_k=5,
            scorer_config={"batch_size": 32},
            rank_strategy_config={"diversity_threshold": 0.5},
            post_processors=[{"type": "threshold", "value": 0.1}],
        )

        assert request.top_k == 5
        assert request.scorer_config["batch_size"] == 32
        assert len(request.post_processors) == 1


class TestRerankResult:
    """Tests for RerankResult."""

    def test_result_creation(self):
        """Test creating rerank result."""
        result = RerankResult(
            document_id="doc-1",
            text="Document text",
            score=0.85,
            rank=1,
        )

        assert result.document_id == "doc-1"
        assert result.score == 0.85
        assert result.rank == 1
        assert result.metadata == {}
        assert result.original_index == 0

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = RerankResult(
            document_id="doc-1",
            text="Document text",
            score=0.85,
            rank=1,
            metadata={"source": "test"},
            original_index=2,
        )

        d = result.to_dict()

        assert d["document_id"] == "doc-1"
        assert d["score"] == 0.85
        assert d["metadata"]["source"] == "test"
        assert "processing_info" in d


class TestRerankContext:
    """Tests for RerankContext."""

    def test_context_creation(self):
        """Test creating rerank context."""
        request = RerankRequest(
            query="test",
            documents=[{"id": "1", "text": "doc"}],
        )
        context = RerankContext(request=request)

        assert context.request == request
        assert context.intermediate_scores == {}
        assert context.processing_steps == []
        assert context.latency_ms == 0.0

    def test_context_add_step(self):
        """Test adding processing steps."""
        request = RerankRequest(
            query="test",
            documents=[{"id": "1", "text": "doc"}],
        )
        context = RerankContext(request=request)

        context.add_step("scoring", {"model": "test"})
        context.add_step("threshold")

        assert len(context.processing_steps) == 2
        assert context.processing_steps[0]["name"] == "scoring"
        assert context.processing_steps[0]["details"]["model"] == "test"

    def test_context_intermediate_scores(self):
        """Test storing intermediate scores."""
        request = RerankRequest(
            query="test",
            documents=[{"id": "1", "text": "doc"}],
        )
        context = RerankContext(request=request)

        context.intermediate_scores["raw"] = np.array([0.1, 0.2, 0.3])
        context.intermediate_scores["normalized"] = np.array([0.0, 0.5, 1.0])

        assert "raw" in context.intermediate_scores
        assert len(context.intermediate_scores["raw"]) == 3

    def test_context_to_dict(self):
        """Test converting context to dictionary."""
        request = RerankRequest(
            query="test",
            documents=[{"id": "1", "text": "doc"}],
        )
        context = RerankContext(
            request=request,
            latency_ms=42.5,
            scorer_name="onnx",
            rank_strategy_name="standard",
        )

        d = context.to_dict()

        assert d["latency_ms"] == 42.5
        assert d["scorer_name"] == "onnx"
        assert d["rank_strategy_name"] == "standard"
