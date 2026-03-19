"""Tests for Provider Registry.

Tests cover:
- Provider registration
- Provider lookup
- Error handling for unregistered providers
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestProviderRegistry:
    """Provider 注册表测试"""

    def test_registry_is_singleton(self):
        """注册表是单例模式"""
        from providers.registry import registry
        
        # 获取另一个实例应该是同一个对象
        from providers.registry import registry as registry2
        
        assert registry is registry2

    def test_register_provider_success(self):
        """成功注册 Provider"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        
        @registry.register(ProviderCategory.EMBEDDING, "test-provider-1")
        class TestProvider1(BaseProvider):
            NAME = "test-provider-1"
            
            @classmethod
            def from_config(cls, config):
                return cls()
        
        # 应该能获取到
        provider_cls = registry.get(ProviderCategory.EMBEDDING, "test-provider-1")
        assert provider_cls is TestProvider1

    def test_register_duplicate_provider_fails(self):
        """重复注册同名 Provider 应该失败"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        
        @registry.register(ProviderCategory.EMBEDDING, "test-duplicate")
        class DuplicateProvider(BaseProvider):
            NAME = "test-duplicate"
            
            @classmethod
            def from_config(cls, config):
                return cls()
        
        # 再次注册同名 provider 应该报错
        with pytest.raises(ValueError) as exc_info:
            @registry.register(ProviderCategory.EMBEDDING, "test-duplicate")
            class AnotherProvider(BaseProvider):
                NAME = "test-duplicate"
                
                @classmethod
                def from_config(cls, config):
                    return cls()
        
        assert "already registered" in str(exc_info.value).lower()

    def test_get_unregistered_provider_fails(self):
        """获取未注册的 Provider 应该抛出明确异常"""
        from providers.base import ProviderCategory, UnsupportedProviderError
        from providers.registry import registry
        
        with pytest.raises(UnsupportedProviderError) as exc_info:
            registry.get(ProviderCategory.EMBEDDING, "nonexistent-provider-xyz")
        
        error = exc_info.value
        assert "nonexistent-provider-xyz" in str(error)
        assert error.error_code == "UNSUPPORTED_PROVIDER"
        assert "available" in error.details

    def test_list_providers_by_category(self):
        """列出某分类下的所有 Provider"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        
        # 注册几个测试 provider
        @registry.register(ProviderCategory.RERANK, "list-test-1")
        class ListTest1(BaseProvider):
            NAME = "list-test-1"
            @classmethod
            def from_config(cls, config): return cls()
        
        @registry.register(ProviderCategory.RERANK, "list-test-2")
        class ListTest2(BaseProvider):
            NAME = "list-test-2"
            @classmethod
            def from_config(cls, config): return cls()
        
        providers = registry.list_providers(ProviderCategory.RERANK)
        
        assert "list-test-1" in providers
        assert "list-test-2" in providers

    def test_is_registered_check(self):
        """检查 Provider 是否已注册"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        
        @registry.register(ProviderCategory.LLM, "check-test")
        class CheckTest(BaseProvider):
            NAME = "check-test"
            @classmethod
            def from_config(cls, config): return cls()
        
        assert registry.is_registered(ProviderCategory.LLM, "check-test") is True
        assert registry.is_registered(ProviderCategory.LLM, "not-registered") is False

    def test_register_different_categories_same_name(self):
        """不同分类可以有同名 Provider"""
        from providers.base import ProviderCategory, BaseProvider
        from providers.registry import registry
        
        # Embedding 分类
        @registry.register(ProviderCategory.EMBEDDING, "same-name-test")
        class EmbeddingSameName(BaseProvider):
            NAME = "same-name-test"
            @classmethod
            def from_config(cls, config): return cls()
        
        # LLM 分类（同名）
        @registry.register(ProviderCategory.LLM, "same-name-test")
        class LLMSameName(BaseProvider):
            NAME = "same-name-test"
            @classmethod
            def from_config(cls, config): return cls()
        
        # 两个都应该能获取到，且是不同的类
        emb_cls = registry.get(ProviderCategory.EMBEDDING, "same-name-test")
        llm_cls = registry.get(ProviderCategory.LLM, "same-name-test")
        
        assert emb_cls is EmbeddingSameName
        assert llm_cls is LLMSameName
        assert emb_cls is not llm_cls