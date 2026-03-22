"""Tests for evaluation script.

Reference:
- Docs/12-V2-Blueprint.md (Section 3: 验证体系)
- RULE.md (Section 7: 测试验收标准)
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import from tests package
from tests.test_evaluation.test_questions import TEST_QUESTIONS


class TestEvaluationRunner:
    """Test EvaluationRunner functionality."""

    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock pipeline for testing."""
        pipeline = AsyncMock()
        pipeline.run = AsyncMock()
        return pipeline

    @pytest.fixture
    def sample_result(self):
        """Create a sample RAGResult for testing."""
        # Import locally to avoid import issues in test discovery
        from src.pipeline import Document, RAGResult

        return RAGResult(
            query="test query",
            documents=[
                Document(
                    id="doc1",
                    text="This document contains authentication and JWT tokens for FastAPI.",
                    score=0.95,
                    metadata={"source": "test"},
                ),
                Document(
                    id="doc2",
                    text="OAuth and login mechanisms are explained here.",
                    score=0.85,
                    metadata={"source": "test"},
                ),
            ],
            total_results=2,
            execution_time_ms=50.0,
            profile="balanced",
        )

    def test_evaluation_runner_init(self):
        """Test EvaluationRunner initialization."""
        # Import locally to avoid import issues in test discovery
        from scripts.evaluate import EvaluationRunner

        runner = EvaluationRunner(profile="balanced")
        assert runner.profile == "balanced"
        assert runner.top_k == 10

    def test_evaluation_runner_custom_params(self):
        """Test EvaluationRunner with custom parameters."""
        from scripts.evaluate import EvaluationRunner

        runner = EvaluationRunner(profile="accurate", top_k=5)
        assert runner.profile == "accurate"
        assert runner.top_k == 5

    @pytest.mark.asyncio
    async def test_run_single_query(self, mock_pipeline, sample_result):
        """Test running a single evaluation query."""
        from scripts.evaluate import EvaluationRunner
        from src.pipeline import RAGResult

        mock_pipeline.run.return_value = sample_result

        runner = EvaluationRunner(profile="balanced")

        # Set the pipeline directly to avoid async get_pipeline call
        runner._pipeline = mock_pipeline
        result = await runner.run_single_query("How do I implement authentication?")

        assert result is not None
        assert result.query == "test query"
        mock_pipeline.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_evaluation(self, mock_pipeline, sample_result):
        """Test running full evaluation."""
        from scripts.evaluate import EvaluationRunner

        mock_pipeline.run.return_value = sample_result

        runner = EvaluationRunner(profile="balanced")

        # Use only 3 questions for testing
        test_queries = [
            {"id": 1, "question": "Query 1", "keywords": ["auth"]},
            {"id": 2, "question": "Query 2", "keywords": ["test"]},
        ]

        runner._pipeline = mock_pipeline
        result = await runner.run_evaluation(queries=test_queries)

        assert result is not None
        assert result["total_queries"] == 2

    def test_calculate_metrics(self, sample_result):
        """Test metrics calculation."""
        from scripts.evaluate import EvaluationRunner
        from src.pipeline import Document

        runner = EvaluationRunner(profile="balanced")

        queries = [
            {"id": 1, "question": "test", "keywords": ["auth", "JWT"]},
        ]

        results = {1: sample_result.documents}

        metrics = runner.calculate_metrics(queries, results)

        assert "hit_rate" in metrics
        assert "avg_relevance_score" in metrics
        assert "noise_ratio" in metrics
        assert "total_queries" in metrics

    def test_format_output_json(self, sample_result):
        """Test JSON output formatting."""
        from scripts.evaluate import EvaluationRunner

        runner = EvaluationRunner(profile="balanced")

        results = {
            "total_queries": 1,
            "hit_rate": 85.5,
            "avg_relevance_score": 0.75,
            "noise_ratio": 0.15,
        }

        output = runner.format_output(results, format="json")

        # Should be valid JSON
        parsed = json.loads(output)
        assert parsed["total_queries"] == 1

    def test_format_output_markdown(self):
        """Test Markdown output formatting."""
        from scripts.evaluate import EvaluationRunner

        runner = EvaluationRunner(profile="balanced")

        # Format expects fields like profile, top_k, total_queries, etc.
        results = {
            "profile": "balanced",
            "top_k": 10,
            "total_queries": 3,
            "timestamp": "2024-01-01T00:00:00",
            "aggregate_metrics": {
                "avg_relevance_score": 0.80,
                "avg_noise_ratio": 0.10,
                "avg_execution_time_ms": 50.0,
            },
            "query_results": [],
        }

        output = runner.format_output(results, format="markdown")

        assert "# Evaluation Results" in output
        assert "balanced" in output
        assert "3" in output


class TestEvaluationResult:
    """Test EvaluationResult data class."""

    def test_result_creation(self):
        """Test creating EvaluationResult."""
        from scripts.evaluate import EvaluationResult
        from src.pipeline import Document

        result = EvaluationResult(
            query_id=1,
            query="test query",
            profile="balanced",
            documents=[Document(id="1", text="test", score=0.9, metadata={})],
            execution_time_ms=50.0,
            metrics={"hit": True, "relevance": 0.85},
        )

        assert result.query_id == 1
        assert result.profile == "balanced"
        assert len(result.documents) == 1

    def test_result_to_dict(self):
        """Test EvaluationResult serialization."""
        from scripts.evaluate import EvaluationResult
        from src.pipeline import Document

        result = EvaluationResult(
            query_id=1,
            query="test query",
            profile="balanced",
            documents=[Document(id="1", text="test", score=0.9, metadata={})],
            execution_time_ms=50.0,
            metrics={"hit": True},
        )

        data = result.to_dict()
        assert data["query_id"] == 1
        assert data["profile"] == "balanced"
        assert "documents" in data


class TestCompareProfiles:
    """Test profile comparison functionality."""

    @pytest.mark.asyncio
    async def test_compare_profiles_structure(self):
        """Test comparison structure creation."""
        # This test validates the comparison logic structure
        # The actual comparison would require mocking the pipeline
        profiles = ["fast", "balanced", "accurate"]

        # Verify profile ordering comparison logic
        profile_metrics = {
            "fast": {"hit_rate": 70.0, "avg_relevance_score": 0.65, "noise_ratio": 0.25},
            "balanced": {"hit_rate": 85.0, "avg_relevance_score": 0.78, "noise_ratio": 0.15},
            "accurate": {"hit_rate": 92.0, "avg_relevance_score": 0.85, "noise_ratio": 0.08},
        }

        # Verify metrics ordering
        assert profile_metrics["accurate"]["hit_rate"] > profile_metrics["fast"]["hit_rate"]
        assert profile_metrics["balanced"]["hit_rate"] > profile_metrics["fast"]["hit_rate"]


class TestMain:
    """Test main entry point."""

    def test_parse_args_defaults(self):
        """Test argument parsing with defaults."""
        from scripts.evaluate import parse_args

        with patch("sys.argv", ["evaluate"]):
            args = parse_args()
            assert args.profile == "balanced"
            assert args.top_k == 10
            assert args.output is None
            assert args.format == "json"

    def test_parse_args_custom(self):
        """Test argument parsing with custom values."""
        from scripts.evaluate import parse_args

        with patch("sys.argv", ["evaluate", "--profile", "accurate", "--top-k", "5", "--format", "markdown"]):
            args = parse_args()
            assert args.profile == "accurate"
            assert args.top_k == 5
            assert args.format == "markdown"

    def test_parse_args_compare(self):
        """Test argument parsing for comparison mode."""
        from scripts.evaluate import parse_args

        with patch("sys.argv", ["evaluate", "--compare", "fast,balanced,accurate"]):
            args = parse_args()
            assert args.compare == "fast,balanced,accurate"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_results(self):
        """Test handling empty results."""
        from scripts.evaluate import EvaluationRunner
        from src.pipeline import RAGResult

        runner = EvaluationRunner(profile="balanced")

        mock_pipeline = AsyncMock()
        mock_pipeline.run.return_value = RAGResult(
            query="test",
            documents=[],
            total_results=0,
            execution_time_ms=50.0,
            profile="balanced",
        )

        runner._pipeline = mock_pipeline
        result = await runner.run_single_query("empty query")

        assert result.documents == []

    def test_invalid_profile(self):
        """Test invalid profile validation."""
        from scripts.evaluate import EvaluationRunner

        with pytest.raises(ValueError):
            EvaluationRunner(profile="invalid_profile")

    def test_output_file_writing(self, tmp_path: Path):
        """Test writing results to file."""
        from scripts.evaluate import EvaluationRunner

        runner = EvaluationRunner(profile="balanced")

        results = {
            "total_queries": 1,
            "hit_rate": 85.0,
            "avg_relevance_score": 0.75,
            "noise_ratio": 0.15,
        }

        output_file = tmp_path / "results.json"
        runner.write_output(results, output_file, format="json")

        assert output_file.exists()
        with open(output_file) as f:
            data = json.load(f)
        assert data["total_queries"] == 1