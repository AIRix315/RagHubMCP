"""Tests for OllamaEmbeddingProvider.

Test cases for Task 1.5a:
- Ollama embedding provider implementation
- Mock-based testing (no real Ollama service required)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestOllamaEmbeddingProviderRegistration:
    """Test provider registration."""

    def test_provider_is_registered(self):
        """Ollama embedding provider is registered in registry."""
        from providers.registry import registry
        from providers.base import ProviderCategory

        assert registry.is_registered(ProviderCategory.EMBEDDING, "ollama")


class TestOllamaEmbeddingProviderInit:
    """Test provider initialization."""

    def test_init_with_defaults(self):
        """Initialize with default values."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        provider = OllamaEmbeddingProvider(model="nomic-embed-text")

        assert provider.NAME == "ollama"
        assert provider.model == "nomic-embed-text"
        assert provider.base_url == "http://localhost:11434"

    def test_init_with_custom_base_url(self):
        """Initialize with custom base URL."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        provider = OllamaEmbeddingProvider(
            model="bge-m3",
            base_url="http://custom-host:11434"
        )

        assert provider.base_url == "http://custom-host:11434"

    def test_from_config_factory(self):
        """Create instance from config dict."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        config = {
            "name": "ollama-bge",
            "type": "ollama",
            "model": "bge-m3",
            "base_url": "http://localhost:11434",
            "dimension": 1024
        }

        provider = OllamaEmbeddingProvider.from_config(config)

        assert provider.model == "bge-m3"
        assert provider.base_url == "http://localhost:11434"


class TestOllamaEmbeddingProviderEmbed:
    """Test embedding methods."""

    @pytest.fixture
    def mock_ollama_response(self):
        """Mock Ollama API response."""
        return {
            "embeddings": [
                [0.1] * 768,
                [0.2] * 768,
            ]
        }

    @patch("providers.embedding.ollama.httpx.post")
    def test_embed_documents_success(self, mock_post):
        """Embed multiple documents successfully."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.1] * 768, [0.2] * 768]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimension=768)
        texts = ["Hello world", "Test document"]
        result = provider.embed_documents(texts)

        assert len(result) == 2
        assert len(result[0]) == 768
        mock_post.assert_called_once()

    @patch("providers.embedding.ollama.httpx.post")
    def test_embed_query_success(self, mock_post):
        """Embed a single query successfully."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        # Setup mock - single query returns "embedding" not "embeddings"
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embedding": [0.5] * 768  # Single query returns "embedding"
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimension=768)
        result = provider.embed_query("What is machine learning?")

        assert len(result) == 768
        assert result[0] == 0.5

    def test_dimension_property(self):
        """Dimension property returns correct value."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        provider = OllamaEmbeddingProvider(model="bge-m3", dimension=1024)

        assert provider.dimension == 1024

    def test_dimension_default(self):
        """Default dimension is 768."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        provider = OllamaEmbeddingProvider(model="nomic-embed-text")

        assert provider.dimension == 768


class TestOllamaEmbeddingProviderAsync:
    """Test async methods."""

    @pytest.mark.asyncio
    async def test_aembed_documents_success(self):
        """Async embed documents successfully."""
        from unittest.mock import AsyncMock
        from providers.embedding.ollama import OllamaEmbeddingProvider

        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.1] * 768]
        }
        mock_response.raise_for_status = MagicMock()

        provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimension=768)

        # Patch httpx.AsyncClient context manager
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await provider.aembed_documents(["test"])

            assert len(result) == 1
            assert len(result[0]) == 768

    @pytest.mark.asyncio
    async def test_aembed_query_success(self):
        """Async embed query successfully."""
        from unittest.mock import AsyncMock
        from providers.embedding.ollama import OllamaEmbeddingProvider

        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embedding": [0.5] * 768
        }
        mock_response.raise_for_status = MagicMock()

        provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimension=768)

        # Patch httpx.AsyncClient context manager
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await provider.aembed_query("test query")

            assert len(result) == 768


class TestOllamaEmbeddingProviderBatch:
    """Test batch processing."""

    @patch("providers.embedding.ollama.httpx.post")
    def test_embed_batch_small_list(self, mock_post):
        """Batch embed small list (single request)."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "embeddings": [[0.1] * 768, [0.2] * 768]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimension=768)
        result = provider.embed_batch(["a", "b"], batch_size=10)

        assert len(result) == 2
        # Should be called once (all texts fit in one batch)
        assert mock_post.call_count == 1

    @patch("providers.embedding.ollama.httpx.post")
    def test_embed_batch_large_list(self, mock_post):
        """Batch embed large list (multiple requests)."""
        from providers.embedding.ollama import OllamaEmbeddingProvider

        # First batch
        mock_response1 = MagicMock()
        mock_response1.json.return_value = {
            "embeddings": [[0.1] * 768, [0.2] * 768]
        }
        mock_response1.raise_for_status.return_value = None

        # Second batch
        mock_response2 = MagicMock()
        mock_response2.json.return_value = {
            "embeddings": [[0.3] * 768]
        }
        mock_response2.raise_for_status.return_value = None

        mock_post.side_effect = [mock_response1, mock_response2]

        provider = OllamaEmbeddingProvider(model="nomic-embed-text", dimension=768)
        result = provider.embed_batch(["a", "b", "c"], batch_size=2)

        assert len(result) == 3
        # Should be called twice (2 + 1 texts)
        assert mock_post.call_count == 2