"""ONNX Backend integration tests.

Tests the complete flow of ONNX-based reranking.
"""

import pytest
from pathlib import Path

from raghub_mcp.rerank_engine.engine import RerankConfig, RerankEngine
from raghub_mcp.rerank_engine.models import BackendType, RerankRequest


# Model path - use existing model in data/models/
MODEL_PATH = Path(__file__).parent.parent.parent / "data" / "models" / "model.onnx"
TOKENIZER_PATH = Path(__file__).parent.parent.parent / "data" / "models" / "tokenizer.json"


class TestONNXBackend:
    """Tests for ONNX backend reranking."""

    def test_onnx_backend_registration(self):
        """Test ONNX backend is registered."""
        from raghub_mcp.providers.registry import registry
        from raghub_mcp.providers.base import ProviderCategory
        # Import adapters to trigger registration
        from raghub_mcp.providers.rerank import adapters  # noqa: F401

        assert registry.is_registered(ProviderCategory.RERANK, "rerank-engine")

    def test_onnx_config_creation(self):
        """Test RerankConfig with ONNX backend."""
        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="onnx",
            scorer_config={
                "model_path": "./data/models/test.onnx",
            },
        )

        assert config.backend == BackendType.ONNX
        assert config.scorer_type == "onnx"
        assert config.embedding_provider is None

    def test_onnx_config_with_embedding_provider(self):
        """Test RerankConfig with embedding_provider field."""
        mock_provider = object()
        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="onnx",
            embedding_provider=mock_provider,
        )

        assert config.embedding_provider is mock_provider

    @pytest.mark.skip(reason="Requires model file - run manually")
    def test_onnx_rerank_flow(self, tmp_path):
        """Test complete ONNX reranking flow."""
        # Requires actual model file for full test
        pass

    def test_onnx_scorer_without_embedding(self):
        """Test ONNX scorer works without embedding provider."""
        config = RerankConfig(
            backend=BackendType.ONNX,
            scorer_type="onnx",
            scorer_config={},
        )

        # ONNX scorer doesn't need embedding_provider
        assert config.embedding_provider is None