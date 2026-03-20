"""Tests for HTTP Embedding Provider.

Tests the generic HTTP embedding provider that supports all OpenAI-compatible APIs.

TC-1.18.1: HTTPEmbeddingProvider 可实例化
TC-1.18.2: embed_documents 返回正确维度
TC-1.18.3: embed_query 返回正确维度
TC-1.18.4: 配置驱动实例化成功
"""

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestHTTPEmbeddingProvider:
    """Tests for HTTPEmbeddingProvider - Generic HTTP Embedding Provider."""

    def test_tc_1_18_1_provider_instantiable(self):
        """TC-1.18.1: HTTPEmbeddingProvider 可实例化.
        
        Verify that the provider can be instantiated with required parameters.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        assert provider is not None
        assert provider.model == "nomic-embed-text"
        assert provider.base_url == "http://localhost:1234/v1"
        assert provider.dimension == 768

    def test_tc_1_18_1_provider_with_api_key(self):
        """TC-1.18.1: HTTPEmbeddingProvider 支持 API Key.
        
        Verify that the provider can be instantiated with optional API key.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            dimension=1536,
            api_key="sk-test-key",
        )
        
        assert provider is not None

    def test_tc_1_18_1_provider_with_custom_headers(self):
        """TC-1.18.1: HTTPEmbeddingProvider 支持自定义请求头.
        
        Verify that the provider can be instantiated with custom headers.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://your-resource.openai.azure.com/openai/deployments/your-deployment",
            model="text-embedding-ada-002",
            dimension=1536,
            api_key="azure-key",
            headers={"api-key": "azure-key"},
        )
        
        assert provider is not None

    def test_tc_1_18_2_embed_documents_returns_correct_dimension(self):
        """TC-1.18.2: embed_documents 返回正确维度.
        
        Verify that embed_documents returns vectors with correct dimension.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        # Mock the HTTP response
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.1] * 768, "index": 0},
                    {"embedding": [0.2] * 768, "index": 1},
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            embeddings = provider.embed_documents(["text1", "text2"])
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 768
            assert len(embeddings[1]) == 768

    def test_tc_1_18_3_embed_query_returns_correct_dimension(self):
        """TC-1.18.3: embed_query 返回正确维度.
        
        Verify that embed_query returns a vector with correct dimension.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        # Mock the HTTP response
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.5] * 768, "index": 0},
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            embedding = provider.embed_query("test query")
            
            assert len(embedding) == 768

    def test_tc_1_18_4_config_driven_instantiation(self):
        """TC-1.18.4: 配置驱动实例化成功.
        
        Verify that the provider can be created from config dict.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        config: dict[str, Any] = {
            "name": "lmstudio-local",
            "type": "http",
            "base_url": "http://localhost:1234/v1",
            "model": "nomic-embed-text",
            "dimension": 768,
        }
        
        provider = HTTPEmbeddingProvider.from_config(config)
        
        assert provider.model == "nomic-embed-text"
        assert provider.base_url == "http://localhost:1234/v1"
        assert provider.dimension == 768

    def test_tc_1_18_4_config_with_api_key(self):
        """TC-1.18.4: 配置驱动实例化支持 API Key.
        
        Verify that from_config handles API key correctly.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        config: dict[str, Any] = {
            "name": "openai-via-http",
            "type": "http",
            "base_url": "https://api.openai.com/v1",
            "model": "text-embedding-3-small",
            "dimension": 1536,
            "api_key": "sk-test-key",
        }
        
        provider = HTTPEmbeddingProvider.from_config(config)
        
        assert provider.model == "text-embedding-3-small"
        assert provider.dimension == 1536

    def test_embed_batch_processes_in_batches(self):
        """Test that embed_batch processes texts in batches.
        
        Verify that large lists are processed in sub-batches.
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        # Mock the HTTP response
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            
            # Return different embeddings for each call
            call_count = [0]
            
            def side_effect(*args, **kwargs):
                call_count[0] += 1
                batch_size = len(kwargs.get('json', {}).get('input', []))
                mock_response.json.return_value = {
                    "data": [
                        {"embedding": [0.1 * (call_count[0] + i)] * 768, "index": i}
                        for i in range(batch_size)
                    ]
                }
                return mock_response
            
            mock_post.side_effect = side_effect
            
            # Request 50 embeddings with batch_size=20
            texts = [f"text{i}" for i in range(50)]
            embeddings = provider.embed_batch(texts, batch_size=20)
            
            assert len(embeddings) == 50
            assert all(len(e) == 768 for e in embeddings)

    def test_openai_compatible_api_format(self):
        """Test that requests use OpenAI-compatible API format.
        
        Verify that the provider sends requests in the correct format:
        POST {base_url}/embeddings
        Body: {"input": [...], "model": "..."}
        Headers: Authorization: Bearer {api_key}
        """
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            dimension=1536,
            api_key="sk-test-key",
        )
        
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [{"embedding": [0.1] * 1536, "index": 0}]
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            provider.embed_query("test query")
            
            # Verify request format
            call_args = mock_post.call_args
            assert call_args is not None
            
            # Check URL ends with /embeddings
            url = call_args[0][0] if call_args[0] else call_args.kwargs.get('url')
            assert url.endswith('/embeddings')
            
            # Check body format
            body = call_args[1].get('json', {})
            assert 'input' in body
            assert body['model'] == "text-embedding-3-small"
            
            # Check headers
            headers = call_args[1].get('headers', {})
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer sk-test-key'

    def test_empty_documents_returns_empty_list(self):
        """Test that empty document list returns empty list."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        result = provider.embed_documents([])
        assert result == []

    def test_provider_registered_in_registry(self):
        """Test that HTTPEmbeddingProvider is registered in registry.
        
        Verify that the provider can be retrieved from the registry.
        """
        from providers.registry import registry
        from providers.base import ProviderCategory
        
        # Check if http embedding provider is registered
        http_provider_class = registry.get(
            ProviderCategory.EMBEDDING,
            "http"
        )
        
        assert http_provider_class is not None
        assert http_provider_class.NAME == "http"


class TestHTTPEmbeddingProviderAsync:
    """Tests for async embedding methods."""

    @pytest.mark.asyncio
    async def test_aembed_documents_returns_correct_dimension(self):
        """Test that aembed_documents returns vectors with correct dimension."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.1] * 768, "index": 0},
                {"embedding": [0.2] * 768, "index": 1},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client) as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            embeddings = await provider.aembed_documents(["text1", "text2"])
            
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 768
            assert len(embeddings[1]) == 768

    @pytest.mark.asyncio
    async def test_aembed_documents_empty_list(self):
        """Test that aembed_documents with empty list returns empty list."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        result = await provider.aembed_documents([])
        assert result == []

    @pytest.mark.asyncio
    async def test_aembed_query_returns_correct_dimension(self):
        """Test that aembed_query returns vector with correct dimension."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [0.5] * 768, "index": 0},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client) as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            embedding = await provider.aembed_query("test query")
            
            assert len(embedding) == 768

    @pytest.mark.asyncio
    async def test_aembed_query_with_api_key(self):
        """Test that aembed_query sends correct headers with API key."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            dimension=1536,
            api_key="sk-test-key",
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1536, "index": 0}]
        }
        mock_response.raise_for_status = MagicMock()
        
        captured_kwargs = {}
        
        async def capture_post(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return mock_response
        
        mock_client = MagicMock()
        mock_client.post = capture_post
        
        with patch('httpx.AsyncClient', return_value=mock_client) as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            await provider.aembed_query("test")
            
            headers = captured_kwargs.get('headers', {})
            assert 'Authorization' in headers
            assert headers['Authorization'] == 'Bearer sk-test-key'

    @pytest.mark.asyncio
    async def test_aembed_documents_with_custom_headers(self):
        """Test that aembed_documents uses custom headers."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://azure.example.com",
            model="text-embedding-ada-002",
            dimension=1536,
            api_key="azure-key",
            headers={"api-key": "azure-key"},
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"embedding": [0.1] * 1536, "index": 0}]
        }
        mock_response.raise_for_status = MagicMock()
        
        captured_kwargs = {}
        
        async def capture_post(*args, **kwargs):
            captured_kwargs.update(kwargs)
            return mock_response
        
        mock_client = MagicMock()
        mock_client.post = capture_post
        
        with patch('httpx.AsyncClient', return_value=mock_client) as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            await provider.aembed_documents(["test"])
            
            headers = captured_kwargs.get('headers', {})
            assert headers.get('api-key') == 'azure-key'

    @pytest.mark.asyncio
    async def test_aembed_documents_sorted_by_index(self):
        """Test that aembed_documents sorts results by index."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="test-model",
            dimension=4,
        )
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"embedding": [2, 2, 2, 2], "index": 1},
                {"embedding": [1, 1, 1, 1], "index": 0},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        
        with patch('httpx.AsyncClient', return_value=mock_client) as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            embeddings = await provider.aembed_documents(["text1", "text2"])
            
            assert embeddings[0] == [1, 1, 1, 1]
            assert embeddings[1] == [2, 2, 2, 2]


class TestHTTPEmbeddingProviderBatch:
    """Tests for batch embedding operations."""

    def test_embed_batch_empty_list(self):
        """Test that embed_batch with empty list returns empty list."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        result = provider.embed_batch([])
        assert result == []

    def test_embed_batch_single_batch(self):
        """Test embed_batch with texts that fit in single batch."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [
                    {"embedding": [0.1] * 768, "index": 0},
                    {"embedding": [0.2] * 768, "index": 1},
                ]
            }
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            embeddings = provider.embed_batch(["text1", "text2"], batch_size=10)
            
            assert len(embeddings) == 2
            assert mock_post.call_count == 1

    def test_embed_batch_respects_batch_size(self):
        """Test that embed_batch makes multiple calls for large lists."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="nomic-embed-text",
            dimension=768,
        )
        
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            
            call_count = [0]
            
            def side_effect(*args, **kwargs):
                call_count[0] += 1
                batch_size = len(kwargs.get('json', {}).get('input', []))
                mock_response.json.return_value = {
                    "data": [
                        {"embedding": [call_count[0] * 0.1] * 768, "index": i}
                        for i in range(batch_size)
                    ]
                }
                return mock_response
            
            mock_post.side_effect = side_effect
            
            # 10 texts with batch_size=3 should make 4 calls
            texts = [f"text{i}" for i in range(10)]
            embeddings = provider.embed_batch(texts, batch_size=3)
            
            assert len(embeddings) == 10
            assert call_count[0] == 4  # 3+3+3+1


class TestHTTPEmbeddingProviderHeaders:
    """Tests for header handling."""

    def test_get_headers_with_api_key(self):
        """Test that _get_headers includes Authorization with API key."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://api.openai.com/v1",
            model="text-embedding-3-small",
            dimension=1536,
            api_key="sk-test",
        )
        
        headers = provider._get_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer sk-test"

    def test_get_headers_with_custom_headers(self):
        """Test that _get_headers includes custom headers."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://azure.example.com",
            model="test",
            dimension=768,
            headers={"api-key": "azure-key", "X-Custom": "value"},
        )
        
        headers = provider._get_headers()
        
        assert headers["api-key"] == "azure-key"
        assert headers["X-Custom"] == "value"

    def test_get_headers_custom_auth_takes_precedence(self):
        """Test that custom Authorization header takes precedence over api_key."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="https://api.example.com",
            model="test",
            dimension=768,
            api_key="default-key",
            headers={"Authorization": "Custom custom-key"},
        )
        
        headers = provider._get_headers()
        
        # Custom header should take precedence
        assert headers["Authorization"] == "Custom custom-key"

    def test_get_embeddings_url(self):
        """Test that _get_embeddings_url constructs correct URL."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1",
            model="test",
            dimension=768,
        )
        
        url = provider._get_embeddings_url()
        
        assert url == "http://localhost:1234/v1/embeddings"

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        from providers.embedding.http import HTTPEmbeddingProvider
        
        provider = HTTPEmbeddingProvider(
            base_url="http://localhost:1234/v1/",
            model="test",
            dimension=768,
        )
        
        assert provider.base_url == "http://localhost:1234/v1"