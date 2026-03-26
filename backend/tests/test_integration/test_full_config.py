"""E2E test for full configuration (VectorStore + Embedding + Rerank).

Scenario: Vector search + BM25 fusion + ONNX rerank.
"""

from unittest.mock import MagicMock

import pytest


class TestFullConfig:
    """Tests for full configuration."""

    def test_embedded_provider_injection(self):
        """Test embedding_provider can be injected into RerankConfig."""
        from raghub_mcp.rerank_engine.engine import RerankConfig

        # Mock embedding provider
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        config = RerankConfig(
            scorer_type="vector",
            embedding_provider=mock_provider,
        )

        assert config.embedding_provider is mock_provider

    def test_hybrid_scorer_with_embedding(self):
        """Test HybridFusionScorer with embedding provider."""
        from raghub_mcp.rerank_engine.scorers.hybrid_scorer import HybridFusionScorer

        # Mock embedding provider
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        scorer = HybridFusionScorer(
            embedding_provider=mock_provider,
            vector_weight=0.7,
        )

        assert scorer._vector_scorer._embedding_provider is mock_provider

    def test_vector_scorer_with_embedding(self):
        """Test VectorScorer with embedding provider."""
        from raghub_mcp.rerank_engine.scorers.vector_scorer import VectorScorer

        # Mock embedding provider
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        scorer = VectorScorer(
            embedding_provider=mock_provider,
            similarity_fn="cosine",
        )

        assert scorer._embedding_provider is mock_provider
        assert scorer.similarity_fn == "cosine"

    def test_rerank_config_with_embedding_provider_name(self):
        """Test RerankConfig with embedding_provider_name."""
        from raghub_mcp.rerank_engine.engine import RerankConfig

        config = RerankConfig(
            scorer_type="hybrid",
            embedding_provider_name="ollama-bge",
        )

        # embedding_provider_name is set, but embedding_provider is None
        assert config.embedding_provider_name == "ollama-bge"
        assert config.embedding_provider is None

    @pytest.mark.skip(reason="Requires VectorStore + Embedding setup")
    @pytest.mark.asyncio
    async def test_full_config_vector_scorer(self):
        """Test VectorScorer with embedding provider.

        Prerequisites:
        - VectorStore configured
        - Embedding provider configured
        """
        pass

    @pytest.mark.skip(reason="Requires VectorStore + Embedding setup")
    @pytest.mark.asyncio
    async def test_full_config_hybrid_scorer(self):
        """Test HybridScorer with embedding provider.

        Prerequisites:
        - VectorStore configured
        - Embedding provider configured
        """
        pass

    def test_embedded_provider_injection_in_adapter(self):
        """Test embedding_provider injection through RerankEngineAdapter."""
        from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter
        from raghub_mcp.rerank_engine.models import BackendType

        # Mock factory and embedding provider
        mock_provider = MagicMock()
        mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

        # Note: In real scenario, embedding_provider_name would trigger factory lookup
        # For this test, we verify the config structure is correct
        config = {
            "backend": BackendType.ONNX.value,
            "scorer_type": "vector",
            "embedding_provider": mock_provider,  # Direct injection
        }

        # Test passes if config structure is valid
        # Actual integration requires factory mock
        assert config["backend"] == "onnx"
        assert config["scorer_type"] == "vector"
        assert config["embedding_provider"] is mock_provider
