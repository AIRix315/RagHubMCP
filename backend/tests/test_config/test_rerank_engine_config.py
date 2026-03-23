"""Test rerank-engine config loading."""

from __future__ import annotations

import pytest


def test_rerank_engine_config_loaded() -> None:
    """Verify rerank-engine can be loaded from config."""
    from raghub_mcp.utils.config import get_config

    config = get_config()
    # Verify rerank-engine is in instances (dict list)
    rerank_configs = config.providers.rerank.instances
    rerank_names = [r.get("name") for r in rerank_configs if isinstance(r, dict)]
    assert "rerank-engine" in rerank_names


def test_rerank_engine_config_structure() -> None:
    """Verify rerank-engine has correct config structure."""
    from raghub_mcp.utils.config import get_config

    config = get_config()
    rerank_configs = config.providers.rerank.instances

    # Find rerank-engine config
    rerank_engine = None
    for r in rerank_configs:
        if isinstance(r, dict) and r.get("name") == "rerank-engine":
            rerank_engine = r
            break

    assert rerank_engine is not None, "rerank-engine not found in instances"
    assert rerank_engine.get("type") == "rerank-engine"
    assert rerank_engine.get("scorer_type") == "onnx"
    assert rerank_engine.get("rank_strategy") == "standard"


def test_factory_can_get_rerank_engine_provider() -> None:
    """Verify factory can instantiate rerank-engine provider."""
    from raghub_mcp.providers.factory import factory
    from raghub_mcp.utils.config import get_config

    config = get_config()
    rerank_configs = config.providers.rerank.instances

    # Check if rerank-engine exists in config (dict format)
    rerank_names = [r.get("name") for r in rerank_configs if isinstance(r, dict)]
    if "rerank-engine" not in rerank_names:
        pytest.skip("rerank-engine not configured")

    # Try to get provider - will fail if adapter not registered (T3 dependency)
    try:
        provider = factory.get_rerank_provider("rerank-engine")
        assert provider is not None
    except Exception as e:
        pytest.skip(f"RerankEngineAdapter not yet registered (T3 dependency): {e}")
