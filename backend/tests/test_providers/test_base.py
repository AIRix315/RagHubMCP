"""Tests for Provider base classes (TC-1.3.1, TC-1.3.2).

Test cases:
- TC-1.3.1: 抽象类实例化报错（抽象方法未实现）
- TC-1.3.2: 具体实现类实例化成功
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestProviderBaseClasses:
    """TC-1.3.1: 抽象类实例化报错测试"""

    def test_base_provider_cannot_instantiate(self):
        """TC-1.3.1: BaseProvider 不能直接实例化"""
        from providers.base import BaseProvider

        with pytest.raises(TypeError) as exc_info:
            BaseProvider()

        assert (
            "abstract" in str(exc_info.value).lower()
            or "instantiate" in str(exc_info.value).lower()
        )

    def test_base_embedding_provider_cannot_instantiate(self):
        """TC-1.3.1: BaseEmbeddingProvider 不能直接实例化"""
        from providers.embedding.base import BaseEmbeddingProvider

        with pytest.raises(TypeError) as exc_info:
            BaseEmbeddingProvider()

        assert (
            "abstract" in str(exc_info.value).lower()
            or "instantiate" in str(exc_info.value).lower()
        )

    def test_base_rerank_provider_cannot_instantiate(self):
        """TC-1.3.1: BaseRerankProvider 不能直接实例化"""
        from providers.rerank.base import BaseRerankProvider

        with pytest.raises(TypeError) as exc_info:
            BaseRerankProvider()

        assert (
            "abstract" in str(exc_info.value).lower()
            or "instantiate" in str(exc_info.value).lower()
        )

    def test_base_llm_provider_cannot_instantiate(self):
        """TC-1.3.1: BaseLLMProvider 不能直接实例化"""
        from providers.llm.base import BaseLLMProvider

        with pytest.raises(TypeError) as exc_info:
            BaseLLMProvider()

        assert (
            "abstract" in str(exc_info.value).lower()
            or "instantiate" in str(exc_info.value).lower()
        )

    def test_incomplete_implementation_fails(self):
        """TC-1.3.1: 未实现所有抽象方法的子类无法实例化"""
        from providers.base import BaseProvider

        # 定义一个不完整的实现
        class IncompleteProvider(BaseProvider):
            NAME = "incomplete"
            # 缺少 from_config 实现

        with pytest.raises(TypeError):
            IncompleteProvider()

    def test_missing_name_attribute_fails(self):
        """TC-1.3.1: 未定义 NAME 属性的子类初始化失败"""
        from providers.base import BaseProvider

        with pytest.raises(TypeError) as exc_info:

            class NoNameProvider(BaseProvider):
                # 没有 NAME 属性
                @classmethod
                def from_config(cls, config):
                    pass

        assert "NAME" in str(exc_info.value)


class TestConcreteImplementation:
    """TC-1.3.2: 具体实现类实例化成功测试"""

    def test_complete_embedding_provider_instantiation(self):
        """TC-1.3.2: 完整的 EmbeddingProvider 可以实例化"""
        from providers.embedding.base import BaseEmbeddingProvider

        class MockEmbeddingProvider(BaseEmbeddingProvider):
            NAME = "mock-embedding"

            def __init__(self, model: str = "mock-model"):
                self._model = model
                self._dimension = 768

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.1] * self._dimension for _ in texts]

            def embed_query(self, query: str) -> list[float]:
                return [0.1] * self._dimension

            @property
            def dimension(self) -> int:
                return self._dimension

            @classmethod
            def from_config(cls, config: dict) -> "MockEmbeddingProvider":
                return cls(model=config.get("model", "mock-model"))

        # 实例化应该成功
        provider = MockEmbeddingProvider()
        assert provider.NAME == "mock-embedding"
        assert provider.dimension == 768
        assert len(provider.embed_query("test")) == 768
        assert len(provider.embed_documents(["a", "b"])) == 2

    def test_complete_rerank_provider_instantiation(self):
        """TC-1.3.2: 完整的 RerankProvider 可以实例化"""
        from providers.rerank.base import BaseRerankProvider, RerankResult

        class MockRerankProvider(BaseRerankProvider):
            NAME = "mock-rerank"

            def rerank(
                self, query: str, documents: list[str], top_k: int = 5
            ) -> list[RerankResult]:
                # 简单的 mock 实现：返回前 top_k 个文档
                results = []
                for i, doc in enumerate(documents[:top_k]):
                    results.append(RerankResult(index=i, score=1.0 - i * 0.1, text=doc))
                return results

            @classmethod
            def from_config(cls, config: dict) -> "MockRerankProvider":
                return cls()

        provider = MockRerankProvider()
        assert provider.NAME == "mock-rerank"

        results = provider.rerank("query", ["doc1", "doc2"], top_k=2)
        assert len(results) == 2
        assert results[0].score >= results[1].score

    def test_complete_llm_provider_instantiation(self):
        """TC-1.3.2: 完整的 LLMProvider 可以实例化"""
        from providers.llm.base import BaseLLMProvider

        class MockLLMProvider(BaseLLMProvider):
            NAME = "mock-llm"

            def __init__(self, model: str = "mock-model"):
                self._model = model

            def generate(
                self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs
            ) -> str:
                return f"Response to: {prompt}"

            @classmethod
            def from_config(cls, config: dict) -> "MockLLMProvider":
                return cls(model=config.get("model", "mock-model"))

        provider = MockLLMProvider()
        assert provider.NAME == "mock-llm"
        assert "Response to:" in provider.generate("test")

    def test_from_config_factory_method(self):
        """TC-1.3.2: from_config 方法正确创建实例"""
        from providers.embedding.base import BaseEmbeddingProvider

        class ConfigurableProvider(BaseEmbeddingProvider):
            NAME = "configurable"

            def __init__(self, model: str, dimension: int):
                self._model = model
                self._dimension = dimension

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.0] * self._dimension for _ in texts]

            def embed_query(self, query: str) -> list[float]:
                return [0.0] * self._dimension

            @property
            def dimension(self) -> int:
                return self._dimension

            @classmethod
            def from_config(cls, config: dict) -> "ConfigurableProvider":
                return cls(model=config["model"], dimension=config.get("dimension", 768))

        config = {"model": "test-model", "dimension": 1024}
        provider = ConfigurableProvider.from_config(config)

        assert provider._model == "test-model"
        assert provider.dimension == 1024


class TestAsyncMethods:
    """测试异步方法的默认实现"""

    @pytest.mark.anyio
    async def test_async_embed_documents_default_implementation(self):
        """异步 embed_documents 默认包装同步方法"""
        from providers.embedding.base import BaseEmbeddingProvider

        class AsyncTestProvider(BaseEmbeddingProvider):
            NAME = "async-test"

            def __init__(self):
                self._call_count = 0

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                self._call_count += 1
                return [[0.1] * 768 for _ in texts]

            def embed_query(self, query: str) -> list[float]:
                return [0.1] * 768

            @property
            def dimension(self) -> int:
                return 768

            @classmethod
            def from_config(cls, config: dict) -> "AsyncTestProvider":
                return cls()

        provider = AsyncTestProvider()

        # 异步方法应该调用同步方法
        result = await provider.aembed_documents(["test"])
        assert len(result) == 1
        assert provider._call_count == 1

    @pytest.mark.anyio
    async def test_async_embed_query_default_implementation(self):
        """异步 embed_query 默认包装同步方法"""
        from providers.embedding.base import BaseEmbeddingProvider

        class AsyncQueryProvider(BaseEmbeddingProvider):
            NAME = "async-query"

            def embed_documents(self, texts: list[str]) -> list[list[float]]:
                return [[0.1] * 768 for _ in texts]

            def embed_query(self, query: str) -> list[float]:
                return [0.5] * 768

            @property
            def dimension(self) -> int:
                return 768

            @classmethod
            def from_config(cls, config: dict) -> "AsyncQueryProvider":
                return cls()

        provider = AsyncQueryProvider()
        result = await provider.aembed_query("test query")

        assert len(result) == 768
        assert result[0] == 0.5

    @pytest.mark.anyio
    async def test_async_rerank_default_implementation(self):
        """异步 rerank 默认包装同步方法"""
        from providers.rerank.base import BaseRerankProvider, RerankResult

        class AsyncRerankProvider(BaseRerankProvider):
            NAME = "async-rerank"

            def rerank(
                self, query: str, documents: list[str], top_k: int = 5
            ) -> list[RerankResult]:
                return [RerankResult(index=0, score=0.9, text=documents[0])]

            @classmethod
            def from_config(cls, config: dict) -> "AsyncRerankProvider":
                return cls()

        provider = AsyncRerankProvider()
        results = await provider.arerank("query", ["doc1"], top_k=1)

        assert len(results) == 1
        assert results[0].score == 0.9

    @pytest.mark.anyio
    async def test_async_generate_default_implementation(self):
        """异步 generate 默认包装同步方法"""
        from providers.llm.base import BaseLLMProvider

        class AsyncLLMProvider(BaseLLMProvider):
            NAME = "async-llm"

            def generate(
                self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs
            ) -> str:
                return f"Generated: {prompt}"

            @classmethod
            def from_config(cls, config: dict) -> "AsyncLLMProvider":
                return cls()

        provider = AsyncLLMProvider()
        result = await provider.agenerate("test prompt")

        assert "Generated:" in result
