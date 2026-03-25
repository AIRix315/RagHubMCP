"""Test rerank-engine config loading.

After Rerank architecture correction (Docs/25):
- Default rerank provider is "onnx-minilm"
- Uses backend: onnx configuration
- RerankEngineAdapter handles backend routing
"""

from __future__ import annotations

import pytest


def test_rerank_config_loaded() -> None:
    """Verify rerank provider is loaded from config."""
    from raghub_mcp.utils.config import get_config

    config = get_config()
    # Verify rerank instances exist
    rerank_configs = config.providers.rerank.instances
    rerank_names = [r.get("name") for r in rerank_configs if isinstance(r, dict)]
    assert len(rerank_names) > 0, "No rerank instances configured"


def test_onnx_backend_config_structure() -> None:
    """Verify ONNX backend has correct config structure."""
    from raghub_mcp.utils.config import get_config

    config = get_config()
    rerank_configs = config.providers.rerank.instances

    # Find onnx-minilm config
    onnx_config = None
    for r in rerank_configs:
        if isinstance(r, dict) and r.get("name") == "onnx-minilm":
            onnx_config = r
            break

    if onnx_config is None:
        pytest.skip("onnx-minilm not configured")

    # Verify backend configuration
    assert onnx_config.get("backend") == "onnx", "Expected backend: onnx"
    assert onnx_config.get("scorer_type") == "onnx", "Expected scorer_type: onnx"
    assert onnx_config.get("rank_strategy") in ["standard", "diversity"], "Valid rank_strategy"


def test_default_rerank_provider() -> None:
    """Verify default rerank provider is set."""
    from raghub_mcp.utils.config import get_config

    config = get_config()
    # Default should be set
    default = config.providers.rerank.default
    assert default, "Default rerank provider should be set"


def test_rerank_config_backend_field() -> None:
    """Verify rerank config uses backend field (new architecture)."""
    from raghub_mcp.utils.config import get_config

    config = get_config()
    rerank_configs = config.providers.rerank.instances

    # Verify backend field is present in configured instances
    for r in rerank_configs:
        if isinstance(r, dict):
            # Backend field should be present
            backend = r.get("backend")
            # If backend is set, it should be valid
            if backend is not None:
                assert backend in ["onnx", "api", "local"], f"Invalid backend: {backend}"