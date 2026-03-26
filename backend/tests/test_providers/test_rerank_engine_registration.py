"""Test RerankEngineAdapter registration in provider registry."""

import pytest
from unittest.mock import MagicMock, patch

from raghub_mcp.providers.base import ProviderCategory
from raghub_mcp.providers.registry import registry

# Import the adapters module to trigger registration decorator
from raghub_mcp.providers.rerank import adapters  # noqa: F401


def test_rerank_engine_adapter_registered():
    """Verify RerankEngineAdapter is registered in registry."""
    assert registry.is_registered(ProviderCategory.RERANK, "rerank-engine")


def test_rerank_engine_adapter_can_be_created():
    """Verify RerankEngineAdapter can be retrieved from registry."""
    adapter_class = registry.get(ProviderCategory.RERANK, "rerank-engine")
    assert adapter_class is not None
    assert adapter_class.NAME == "rerank-engine"


def test_api_backend_registered():
    """Verify APIBackendAdapter is registered in registry."""
    from raghub_mcp.providers.rerank import api_backend  # noqa: F401

    assert registry.is_registered(ProviderCategory.RERANK, "api-backend")


def test_rerank_engine_adapter_from_config_onnx():
    """Verify RerankEngineAdapter.from_config works with ONNX backend."""
    from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter
    from raghub_mcp.rerank_engine.models import BackendType

    config = {
        "backend": "onnx",
        "scorer_type": "onnx",
        "scorer_config": {
            "model_path": "./data/models/test.onnx",
        },
    }

    adapter = RerankEngineAdapter.from_config(config)
    assert adapter is not None
    assert isinstance(adapter, RerankEngineAdapter)


def test_rerank_engine_adapter_from_config_with_embedding():
    """Verify RerankEngineAdapter.from_config passes embedding_provider."""
    from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter

    config = {
        "backend": "onnx",
        "scorer_type": "bm25",  # Use BM25 which doesn't need embedding for basic test
    }

    # Without embedding_provider_name, should still work
    adapter = RerankEngineAdapter.from_config(config)
    assert adapter is not None
    assert adapter._engine.config.embedding_provider is None


def test_rerank_engine_adapter_from_config_with_embedding_name():
    """Verify RerankEngineAdapter.from_config handles embedding_provider_name."""
    from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter
    from raghub_mcp.providers.factory import factory

    # Mock factory to return a mock embedding provider
    mock_provider = MagicMock()
    mock_provider.embed = lambda texts: [[0.1] * 768 for _ in texts]

    with patch.object(factory, "get_embedding_provider", return_value=mock_provider):
        config = {
            "backend": "onnx",
            "scorer_type": "bm25",
            "embedding_provider_name": "mock-provider",
        }

        adapter = RerankEngineAdapter.from_config(config)
        assert adapter is not None
        assert adapter._engine.config.embedding_provider is mock_provider
