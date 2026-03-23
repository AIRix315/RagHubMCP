"""Test RerankEngineAdapter registration in provider registry."""

import pytest

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
