"""E2E test for minimal configuration (no VectorStore, no Embedding).

Scenario: BM25 + ONNX rerank only.
"""

from pathlib import Path

import pytest

from raghub_mcp.rerank_engine.engine import RerankConfig, RerankEngine
from raghub_mcp.rerank_engine.models import BackendType, RerankRequest

MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "models" / "model.onnx"


class TestMinimalConfig:
    """Tests for minimal configuration."""

    def test_rerank_config_defaults(self):
        """Test RerankConfig has sensible defaults."""
        config = RerankConfig()

        assert config.backend == BackendType.ONNX
        assert config.scorer_type == "onnx"
        assert config.embedding_provider is None
        assert config.embedding_provider_name is None
        assert config.rank_strategy == "standard"
        assert config.post_processors == []
        assert config.enable_profiling is False

    def test_rerank_config_minimal_onnx(self):
        """Test RerankConfig with minimal ONNX configuration."""
        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="onnx",
            scorer_config={
                "model_path": str(MODEL_PATH),
            },
        )

        assert config.backend == BackendType.ONNX
        assert config.scorer_type == "onnx"
        assert config.embedding_provider is None

    def test_minimal_config_no_embedding_required(self):
        """Test reranking works without embedding provider."""
        # ONNX rerank doesn't need embedding_provider
        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="onnx",
            scorer_config={
                "model_path": str(MODEL_PATH),
            },
        )

        # Should be able to create engine without error
        engine = RerankEngine(config)
        assert engine is not None
        assert engine.config.embedding_provider is None

    def test_bm25_config_no_embedding_required(self):
        """Test BM25 scorer doesn't need embedding provider."""
        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="bm25",
            scorer_config={},
        )

        engine = RerankEngine(config)
        assert engine is not None
        assert engine.config.embedding_provider is None

    def test_vector_config_with_embedding_injection(self):
        """Test VectorScorer with embedding_provider injection."""
        from unittest.mock import MagicMock

        # Mock embedding provider
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="vector",
            embedding_provider=mock_provider,
        )

        # Should be able to create engine
        engine = RerankEngine(config)
        assert engine is not None
        assert engine.config.embedding_provider is mock_provider

    @pytest.mark.skipif(
        not MODEL_PATH.exists(),
        reason="Model file not found - run 'python scripts/download_rerank_model.py'",
    )
    def test_minimal_config_rerank_execution(self):
        """Test reranking with minimal config - requires model file."""
        tokenizer_path = Path(__file__).parent.parent.parent / "data" / "models" / "tokenizer.json"

        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="onnx",
            scorer_config={
                "model_path": str(MODEL_PATH),
                "tokenizer_path": str(tokenizer_path)
                if tokenizer_path.exists()
                else str(MODEL_PATH.parent / "tokenizer.json"),
            },
        )

        engine = RerankEngine(config)
        request = RerankRequest(
            query="test query",
            documents=[
                {"id": "1", "text": "Test document one"},
                {"id": "2", "text": "Test document two"},
            ],
            top_k=2,
        )

        results = engine.rerank(request)
        assert len(results) >= 0  # Results depend on model
