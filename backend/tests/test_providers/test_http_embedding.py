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
from unittest.mock import MagicMock, patch

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