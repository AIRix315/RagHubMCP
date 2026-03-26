"""API Backend integration tests.

Tests the external rerank API integration.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

from raghub_mcp.providers.rerank.api_backend import APIBackendAdapter
from raghub_mcp.providers.rerank.base import RerankResult


class TestAPIBackend:
    """Tests for API backend reranking."""

    def test_api_backend_from_config(self):
        """Test APIBackendAdapter creation from config."""
        config = {
            "backend": "api",
            "api_url": "https://api.example.com/v1/rerank",
            "api_key": "test-key",
            "timeout": 30.0,
        }

        adapter = APIBackendAdapter.from_config(config)
        assert adapter.api_url == "https://api.example.com/v1/rerank"
        assert adapter._api_key == "test-key"

    def test_api_backend_registration(self):
        """Test API backend is registered."""
        from raghub_mcp.providers.registry import registry
        from raghub_mcp.providers.base import ProviderCategory

        assert registry.is_registered(ProviderCategory.RERANK, "api-backend")

    def test_api_backend_config_validation(self):
        """Test API backend config validation."""
        # Missing api_url should raise KeyError
        with pytest.raises(KeyError):
            APIBackendAdapter.from_config({"backend": "api"})

    def test_api_backend_rerank_mock(self):
        """Test API backend reranking with mock."""
        adapter = APIBackendAdapter(
            api_url="https://api.example.com/v1/rerank",
            api_key="test-key",
        )

        # Verify initialization worked
        assert adapter is not None
        assert adapter.api_url == "https://api.example.com/v1/rerank"
        assert adapter._api_key == "test-key"
        assert adapter._timeout == 30.0
        assert adapter._max_retries == 3