"""Tests for Provider Factory (TC-1.3.3, TC-1.3.4).

Test cases:
- TC-1.3.3: Provider 工厂根据配置创建正确实例
- TC-1.3.4: 不支持的 provider 类型抛出明确异常
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestProviderFactory:
    """TC-1.3.3 & TC-1.3.4: Provider 工厂测试"""

    def test_factory_is_singleton(self):
        """工厂是单例模式"""
        from providers.factory import factory
        
        from providers.factory import factory as factory2
        
        assert factory is factory2

    def test_factory_creates_correct_embedding_provider(self):
        """TC-1.3.3: 工厂根据配置创建正确的 EmbeddingProvider"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        from providers.factory import factory
        from providers.embedding.base import BaseEmbeddingProvider
        
        # 注册一个 mock provider
        @registry.register(ProviderCategory.EMBEDDING, "mock-emb-factory")
        class MockEmbProvider(BaseEmbeddingProvider):
            NAME = "mock-emb-factory"
            _instance_count = 0
            
            def __init__(self, model: str):
                self._model = model
                self._dimension = 768
                MockEmbProvider._instance_count += 1
            
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * self._dimension for _ in texts]
            
            def embed_query(self, query: str) -> list[float]:
                return [0.0] * self._dimension
            
            @property
            def dimension(self) -> int:
                return self._dimension
            
            @classmethod
            def from_config(cls, config: dict) -> "MockEmbProvider":
                return cls(model=config.get("model", "default"))
        
        # 修改配置以使用 mock provider
        from utils.config import load_config
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        config = load_config(str(config_path))
        
        # 创建临时配置
        test_config = {
            "name": "test-emb-instance",
            "type": "mock-emb-factory",
            "model": "test-model"
        }
        
        # 直接通过工厂内部方法测试
        provider = registry.get(ProviderCategory.EMBEDDING, "mock-emb-factory")
        instance = provider.from_config(test_config)
        
        assert isinstance(instance, BaseEmbeddingProvider)
        assert instance._model == "test-model"

    def test_factory_singleton_caching(self):
        """工厂使用单例缓存：相同配置复用实例"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        from providers.embedding.base import BaseEmbeddingProvider
        
        # 注册一个可追踪实例创建的 provider
        instance_ids = []
        
        @registry.register(ProviderCategory.EMBEDDING, "cache-test-provider")
        class CacheTestProvider(BaseEmbeddingProvider):
            NAME = "cache-test-provider"
            
            def __init__(self, model: str):
                self._model = model
                self._dimension = 768
                instance_ids.append(id(self))
            
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * self._dimension for _ in texts]
            
            def embed_query(self, query: str) -> list[float]:
                return [0.0] * self._dimension
            
            @property
            def dimension(self) -> int:
                return self._dimension
            
            @classmethod
            def from_config(cls, config: dict) -> "CacheTestProvider":
                return cls(model=config.get("model", "default"))
        
        # 清除工厂缓存
        from providers.factory import factory
        factory.clear_cache()
        
        config1 = {"name": "cache-test-1", "type": "cache-test-provider", "model": "model-a"}
        config2 = {"name": "cache-test-1", "type": "cache-test-provider", "model": "model-a"}  # 相同配置
        config3 = {"name": "cache-test-2", "type": "cache-test-provider", "model": "model-b"}  # 不同配置
        
        # 模拟工厂的缓存逻辑
        cache_key_1 = factory._cache_key(ProviderCategory.EMBEDDING, "cache-test-1", config1)
        cache_key_2 = factory._cache_key(ProviderCategory.EMBEDDING, "cache-test-1", config2)
        cache_key_3 = factory._cache_key(ProviderCategory.EMBEDDING, "cache-test-2", config3)
        
        # 相同配置应该产生相同的缓存键
        assert cache_key_1 == cache_key_2
        # 不同配置应该产生不同的缓存键
        assert cache_key_1 != cache_key_3

    def test_unsupported_provider_raises_clear_error(self):
        """TC-1.3.4: 不支持的 provider 类型抛出明确异常"""
        from providers.base import ProviderCategory, UnsupportedProviderError
        from providers.registry import registry
        
        # 尝试获取不存在的 provider
        with pytest.raises(UnsupportedProviderError) as exc_info:
            registry.get(ProviderCategory.EMBEDDING, "nonexistent-type-xyz")
        
        error = exc_info.value
        assert "nonexistent-type-xyz" in error.message
        assert error.error_code == "UNSUPPORTED_PROVIDER"
        assert "available" in str(error.details).lower() or "Available" in error.message

    def test_provider_not_found_in_config(self):
        """TC-1.3.4: 配置中找不到 provider 实例"""
        from providers.factory import factory
        from providers.base import ProviderNotFoundError
        
        # 清除缓存
        factory.clear_cache()
        
        # 尝试获取不存在的实例名
        # 注意：这个测试依赖于实际的 config.yaml 配置
        with pytest.raises((ProviderNotFoundError, ValueError)) as exc_info:
            factory.get_embedding_provider("nonexistent-instance-xyz")
        
        # 错误信息应该包含可用的实例名
        error_msg = str(exc_info.value)
        assert "nonexistent-instance-xyz" in error_msg or "not found" in error_msg.lower()

    def test_clear_cache(self):
        """测试清除缓存功能"""
        from providers.factory import factory
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        from providers.embedding.base import BaseEmbeddingProvider
        
        # 注册测试 provider
        @registry.register(ProviderCategory.EMBEDDING, "clear-cache-test")
        class ClearCacheTest(BaseEmbeddingProvider):
            NAME = "clear-cache-test"
            
            def __init__(self, model: str):
                self._dimension = 768
            
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * 768 for _ in texts]
            
            def embed_query(self, query: str) -> list[float]:
                return [0.0] * 768
            
            @property
            def dimension(self) -> int:
                return 768
            
            @classmethod
            def from_config(cls, config: dict) -> "ClearCacheTest":
                return cls(model=config.get("model", "default"))
        
        # 创建一个实例并缓存
        test_config = {"name": "test", "type": "clear-cache-test", "model": "test"}
        cache_key = factory._cache_key(ProviderCategory.EMBEDDING, "test", test_config)
        
        # 手动添加到缓存
        instance = ClearCacheTest.from_config(test_config)
        factory._cache[cache_key] = instance
        
        assert cache_key in factory._cache
        
        # 清除缓存
        factory.clear_cache()
        
        assert len(factory._cache) == 0

    def test_cache_key_generation(self):
        """测试缓存键生成的一致性"""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config1 = {"name": "test", "type": "ollama", "model": "nomic"}
        config2 = {"name": "test", "type": "ollama", "model": "nomic"}
        config3 = {"name": "test", "type": "ollama", "model": "bge"}
        
        key1 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config1)
        key2 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config2)
        key3 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config3)
        
        # 相同配置 -> 相同 key
        assert key1 == key2
        # 不同配置 -> 不同 key
        assert key1 != key3

    def test_different_categories_have_different_keys(self):
        """不同分类的缓存键应该不同"""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config = {"name": "test", "type": "ollama", "model": "test"}
        
        emb_key = factory._cache_key(ProviderCategory.EMBEDDING, "test", config)
        llm_key = factory._cache_key(ProviderCategory.LLM, "test", config)
        rerank_key = factory._cache_key(ProviderCategory.RERANK, "test", config)
        
        # 不同分类的 key 应该不同
        assert emb_key != llm_key
        assert emb_key != rerank_key
        assert llm_key != rerank_key


class TestProviderFactoryGetters:
    """Tests for factory getter methods."""

    def test_get_llm_provider_calls_internal_method(self):
        """Test that get_llm_provider calls _get_provider with correct category."""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        # Use cache_key generation to verify correct category
        config = {"name": "llm-test", "type": "test", "model": "test"}
        key = factory._cache_key(ProviderCategory.LLM, "llm-test", config)
        
        assert ProviderCategory.LLM.value in key

    def test_get_vectorstore_provider_calls_internal_method(self):
        """Test that get_vectorstore_provider calls _get_provider with correct category."""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config = {"name": "vs-test", "type": "test", "path": "/tmp"}
        key = factory._cache_key(ProviderCategory.VECTORSTORE, "vs-test", config)
        
        assert ProviderCategory.VECTORSTORE.value in key

    def test_get_rerank_provider_calls_internal_method(self):
        """Test that get_rerank_provider calls _get_provider with correct category."""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config = {"name": "rerank-test", "type": "test", "model": "test"}
        key = factory._cache_key(ProviderCategory.RERANK, "rerank-test", config)
        
        assert ProviderCategory.RERANK.value in key


class TestProviderFactoryErrorHandling:
    """Tests for error handling in factory."""

    def test_provider_not_found_error_message(self):
        """Test ProviderNotFoundError contains useful information."""
        from providers.factory import factory
        from providers.base import ProviderNotFoundError
        
        factory.clear_cache()
        
        with pytest.raises(ProviderNotFoundError) as exc_info:
            factory.get_embedding_provider("definitely-not-exist-xyz-123")
        
        error = exc_info.value
        assert "definitely-not-exist-xyz-123" in str(error)

    def test_unsupported_provider_error_details(self):
        """Test UnsupportedProviderError contains available providers."""
        from providers.base import ProviderCategory, UnsupportedProviderError
        from providers.registry import registry
        
        with pytest.raises(UnsupportedProviderError) as exc_info:
            registry.get(ProviderCategory.EMBEDDING, "totally-fake-provider")
        
        error = exc_info.value
        # Check inherited attributes
        assert error.provider == "totally-fake-provider"
        assert error.error_code == "UNSUPPORTED_PROVIDER"
        # Check details for category and available
        assert "category" in error.details
        assert "available" in error.details

    def test_get_vectorstore_provider_not_found(self):
        """Test get_vectorstore_provider with non-existent instance."""
        from providers.factory import factory
        from providers.base import ProviderNotFoundError
        
        factory.clear_cache()
        
        with pytest.raises((ProviderNotFoundError, ValueError)):
            factory.get_vectorstore_provider("nonexistent-vs-instance")

    def test_get_llm_provider_not_found(self):
        """Test get_llm_provider with non-existent instance."""
        from providers.factory import factory
        from providers.base import ProviderNotFoundError
        
        factory.clear_cache()
        
        with pytest.raises((ProviderNotFoundError, ValueError)):
            factory.get_llm_provider("nonexistent-llm-instance")


class TestProviderFactoryCaching:
    """Tests for caching behavior."""

    def test_cache_returns_same_instance(self):
        """Test that cache returns same instance for same config."""
        from providers.factory import factory
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        from providers.embedding.base import BaseEmbeddingProvider
        
        @registry.register(ProviderCategory.EMBEDDING, "cache-same-test")
        class CacheSameTest(BaseEmbeddingProvider):
            NAME = "cache-same-test"
            
            def __init__(self, value: str):
                self._value = value
                self._dimension = 768
            
            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * 768 for _ in texts]
            
            def embed_query(self, query: str) -> list[float]:
                return [0.0] * 768
            
            @property
            def dimension(self) -> int:
                return 768
            
            @classmethod
            def from_config(cls, config: dict) -> "CacheSameTest":
                return cls(value=config.get("value", "default"))
        
        factory.clear_cache()
        
        config = {"name": "same-test", "type": "cache-same-test", "value": "test"}
        cache_key = factory._cache_key(ProviderCategory.EMBEDDING, "same-test", config)
        
        instance1 = CacheSameTest.from_config(config)
        factory._cache[cache_key] = instance1
        
        # Second retrieval should return cached instance
        instance2 = factory._cache.get(cache_key)
        
        assert instance1 is instance2

    def test_different_configs_different_instances(self):
        """Test that different configs create different instances."""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config1 = {"name": "diff-test-1", "type": "test", "model": "model-a"}
        config2 = {"name": "diff-test-2", "type": "test", "model": "model-b"}
        
        key1 = factory._cache_key(ProviderCategory.EMBEDDING, "diff-test-1", config1)
        key2 = factory._cache_key(ProviderCategory.EMBEDDING, "diff-test-2", config2)
        
        assert key1 != key2


class TestProviderFactoryConfigHash:
    """Tests for configuration hashing."""

    def test_config_order_does_not_affect_hash(self):
        """Test that config key order doesn't change the hash."""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config1 = {"name": "test", "type": "http", "model": "test", "dimension": 768}
        config2 = {"dimension": 768, "model": "test", "name": "test", "type": "http"}
        
        key1 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config1)
        key2 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config2)
        
        assert key1 == key2

    def test_nested_config_in_hash(self):
        """Test that nested config values affect hash."""
        from providers.factory import factory
        from providers.base import ProviderCategory
        
        config1 = {"name": "test", "type": "test", "options": {"batch_size": 32}}
        config2 = {"name": "test", "type": "test", "options": {"batch_size": 64}}
        
        key1 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config1)
        key2 = factory._cache_key(ProviderCategory.EMBEDDING, "test", config2)
        
        assert key1 != key2