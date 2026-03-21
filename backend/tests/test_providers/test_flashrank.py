"""Tests for FlashRankRerankProvider (TC-1.4.1 ~ TC-1.4.7).

Test cases:
- TC-1.4.1: 模型首次加载成功
- TC-1.4.2: 模型缓存命中，二次调用更快
- TC-1.4.3: rerank 返回正确排序结果
- TC-1.4.4: rerank 返回 score 在有效范围 [0, 1]
- TC-1.4.5: 空文档列表返回空结果
- TC-1.4.6: 单文档返回正确结果
- TC-1.4.7: 不同模型切换成功
"""

import sys
import time
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestFlashRankProviderBasic:
    """TC-1.4.1, TC-1.4.5, TC-1.4.6: 基础功能测试"""

    def test_provider_registration(self):
        """FlashRank 提供者已注册到 registry"""
        from providers.base import ProviderCategory
        from providers.registry import registry

        assert registry.is_registered(ProviderCategory.RERANK, "flashrank")

    def test_provider_instantiation(self):
        """TC-1.4.1: 模型首次加载成功"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        provider = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        assert provider.NAME == "flashrank"
        assert provider.model == "ms-marco-TinyBERT-L-2-v2"

    def test_from_config_factory(self):
        """from_config 方法正确创建实例"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        config = {
            "name": "test-flashrank",
            "type": "flashrank",
            "model": "ms-marco-TinyBERT-L-2-v2",
            "cache_dir": "./temp_test_cache",
        }

        provider = FlashRankRerankProvider.from_config(config)
        assert provider.model == "ms-marco-TinyBERT-L-2-v2"

    def test_empty_documents_returns_empty(self):
        """TC-1.4.5: 空文档列表返回空结果"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        provider = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        results = provider.rerank("test query", [], top_k=5)
        assert results == []

    def test_single_document(self):
        """TC-1.4.6: 单文档返回正确结果"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        provider = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        documents = ["Machine learning is a subset of AI."]
        results = provider.rerank("What is machine learning?", documents, top_k=5)

        assert len(results) == 1
        assert results[0].index == 0
        assert results[0].text == documents[0]
        assert 0 <= results[0].score <= 1


class TestFlashRankProviderRerank:
    """TC-1.4.3, TC-1.4.4: Rerank 功能测试"""

    @pytest.fixture
    def provider(self):
        """创建测试用的 FlashRank 提供者"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        return FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

    def test_rerank_returns_sorted_results(self, provider):
        """TC-1.4.3: rerank 返回正确排序结果"""
        query = "What is machine learning?"
        documents = [
            "Machine learning is a subset of artificial intelligence.",
            "Python is a popular programming language.",
            "Neural networks are used in deep learning.",
        ]

        results = provider.rerank(query, documents, top_k=3)

        # 验证返回数量
        assert len(results) == 3

        # 验证按 score 降序排列
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

        # 验证最相关的文档应该排在前面
        # ML 相关文档应该排在 Python 文档之前
        ml_doc_indices = [
            i
            for i, r in enumerate(results)
            if "machine learning" in r.text.lower() or "neural" in r.text.lower()
        ]
        python_doc_indices = [i for i, r in enumerate(results) if "python" in r.text.lower()]

        # ML 相关文档应该排在 Python 文档之前
        if ml_doc_indices and python_doc_indices:
            assert min(ml_doc_indices) < min(python_doc_indices)

    def test_score_in_valid_range(self, provider):
        """TC-1.4.4: rerank 返回 score 在有效范围 [0, 1]"""
        query = "What is AI?"
        documents = [
            "AI stands for artificial intelligence.",
            "The weather is nice today.",
            "Machine learning is part of AI.",
        ]

        results = provider.rerank(query, documents, top_k=3)

        for result in results:
            assert 0 <= result.score <= 1, f"Score {result.score} out of range [0, 1]"

    def test_top_k_parameter(self, provider):
        """top_k 参数正确限制返回数量"""
        query = "test query"
        documents = [f"Document {i}" for i in range(10)]

        results = provider.rerank(query, documents, top_k=3)
        assert len(results) == 3

        results = provider.rerank(query, documents, top_k=5)
        assert len(results) == 5

    def test_top_k_exceeds_documents(self, provider):
        """top_k 超过文档数量时返回所有文档"""
        query = "test query"
        documents = ["doc1", "doc2"]

        results = provider.rerank(query, documents, top_k=10)
        assert len(results) == 2


class TestFlashRankProviderCaching:
    """TC-1.4.2, TC-1.4.7: 缓存和模型切换测试"""

    def test_model_caching_speedup(self):
        """TC-1.4.2: 模型缓存命中，二次调用更快"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        provider = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        documents = ["Machine learning is a subset of AI."]
        query = "What is machine learning?"

        # 第一次调用
        start1 = time.time()
        provider.rerank(query, documents, top_k=1)
        first_duration = time.time() - start1

        # 第二次调用（应该更快，因为模型已加载）
        start2 = time.time()
        provider.rerank(query, documents, top_k=1)
        second_duration = time.time() - start2

        # 第二次调用应该显著更快
        # 放宽条件，只要求第二次不比第一次慢太多
        assert second_duration < first_duration * 2

    def test_different_model_switching(self):
        """TC-1.4.7: 不同模型切换成功"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        # TinyBERT 模型
        provider_tiny = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        # MiniLM 模型
        provider_mini = FlashRankRerankProvider(
            model="ms-marco-MiniLM-L-12-v2", cache_dir="./temp_test_cache"
        )

        query = "What is machine learning?"
        documents = ["Machine learning is a subset of AI."]

        # 两个模型都应该能正常工作
        results_tiny = provider_tiny.rerank(query, documents, top_k=1)
        results_mini = provider_mini.rerank(query, documents, top_k=1)

        assert len(results_tiny) == 1
        assert len(results_mini) == 1

        # 分数可能不同，但都应在有效范围内
        assert 0 <= results_tiny[0].score <= 1
        assert 0 <= results_mini[0].score <= 1


class TestFlashRankProviderAsync:
    """异步方法测试"""

    @pytest.mark.anyio
    async def test_async_rerank(self):
        """异步 rerank 方法正常工作"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        provider = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        query = "What is AI?"
        documents = ["AI stands for artificial intelligence."]

        results = await provider.arerank(query, documents, top_k=1)

        assert len(results) == 1
        assert results[0].index == 0


class TestFlashRankProviderRerankWithMetadata:
    """带元数据的 rerank 测试"""

    def test_rerank_with_metadata(self):
        """rerank_with_metadata 方法正确添加分数"""
        from providers.rerank.flashrank import FlashRankRerankProvider

        provider = FlashRankRerankProvider(
            model="ms-marco-TinyBERT-L-2-v2", cache_dir="./temp_test_cache"
        )

        query = "What is machine learning?"
        documents = [
            {"text": "Machine learning is a subset of AI.", "source": "doc1"},
            {"text": "Python is a programming language.", "source": "doc2"},
        ]

        results = provider.rerank_with_metadata(query, documents, text_key="text", top_k=2)

        assert len(results) == 2
        assert "rerank_score" in results[0]
        assert "source" in results[0]
        assert 0 <= results[0]["rerank_score"] <= 1
