"""Tests for pipeline reranker module.

These tests verify:
- Reranker abstract base class interface
- PipelineReranker implementation
- NoOpReranker implementation
- FallbackReranker implementation

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipeline.reranker import FallbackReranker, NoOpReranker, PipelineReranker, Reranker
from pipeline.result import Document


class TestRerankerABC:
    """Tests for Reranker abstract base class."""

    def test_reranker_is_abstract(self):
        """Test Reranker cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Reranker()

    def test_reranker_requires_rerank_method(self):
        """Test Reranker subclass must implement rerank method."""

        class IncompleteReranker(Reranker):
            pass

        with pytest.raises(TypeError):
            IncompleteReranker()

    def test_reranker_name_property(self):
        """Test reranker name property returns class name."""

        class TestReranker(Reranker):
            async def rerank(
                self, query: str, documents: list[Document], options: dict = None
            ) -> list[Document]:
                return documents

        reranker = TestReranker()
        assert reranker.name == "TestReranker"


class TestPipelineReranker:
    """Tests for PipelineReranker implementation."""

    def test_init_default_params(self):
        """Test PipelineReranker initializes with default parameters."""
        reranker = PipelineReranker()

        assert reranker.model == "ms-marco-TinyBERT-L-2-v2"
        assert reranker.top_k == 5

    def test_init_custom_params(self):
        """Test PipelineReranker initializes with custom parameters."""
        reranker = PipelineReranker(model="custom-model", top_k=10)

        assert reranker.model == "custom-model"
        assert reranker.top_k == 10

    def test_name_property(self):
        """Test PipelineReranker name property."""
        reranker = PipelineReranker()
        assert reranker.name == "PipelineReranker"

    @pytest.mark.asyncio
    async def test_rerank_returns_documents(self):
        """Test rerank returns list of Document objects."""
        # Create test documents
        docs = [
            Document(id="1", text="First document", score=0.9),
            Document(id="2", text="Second document", score=0.8),
        ]

        # Mock the rerank provider
        mock_result = MagicMock()
        mock_result.index = 1
        mock_result.text = "Second document"
        mock_result.score = 0.95

        mock_provider = MagicMock()
        mock_provider.arerank = AsyncMock(return_value=[mock_result])

        mock_factory = MagicMock()
        mock_factory.get_rerank_provider.return_value = mock_provider

        with patch("src.providers.factory.factory", mock_factory):
            reranker = PipelineReranker()
            reranked = await reranker.rerank("test query", docs)

            assert isinstance(reranked, list)
            assert len(reranked) == 1
            assert isinstance(reranked[0], Document)
            assert reranked[0].id == "2"
            assert reranked[0].rerank_score == 0.95

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self):
        """Test rerank handles empty documents list."""
        reranker = PipelineReranker()
        reranked = await reranker.rerank("test query", [])

        assert isinstance(reranked, list)
        assert len(reranked) == 0

    @pytest.mark.asyncio
    async def test_rerank_no_provider_returns_original(self):
        """Test rerank returns original documents when no provider available."""
        docs = [
            Document(id="1", text="First document", score=0.9),
            Document(id="2", text="Second document", score=0.8),
        ]

        mock_factory = MagicMock()
        mock_factory.get_rerank_provider.return_value = None

        with patch("src.providers.factory.factory", mock_factory):
            reranker = PipelineReranker()
            reranked = await reranker.rerank("test query", docs)

            # Should return truncated original documents
            assert len(reranked) <= 5  # default top_k

    @pytest.mark.asyncio
    async def test_rerank_respects_top_k_option(self):
        """Test rerank respects top_k option."""
        docs = [Document(id=str(i), text=f"Document {i}", score=0.9 - i * 0.1) for i in range(10)]

        mock_results = []
        for i in range(3):
            result = MagicMock()
            result.index = i
            result.text = f"Document {i}"
            result.score = 0.9 - i * 0.1
            mock_results.append(result)

        mock_provider = MagicMock()
        mock_provider.arerank = AsyncMock(return_value=mock_results)

        mock_factory = MagicMock()
        mock_factory.get_rerank_provider.return_value = mock_provider

        with patch("src.providers.factory.factory", mock_factory):
            reranker = PipelineReranker()
            reranked = await reranker.rerank("test query", docs, {"top_k": 3})

            mock_provider.arerank.assert_called_once()
            call_kwargs = mock_provider.arerank.call_args[1]
            assert call_kwargs["top_k"] == 3

    @pytest.mark.asyncio
    async def test_rerank_preserves_metadata(self):
        """Test rerank preserves original document metadata."""
        docs = [
            Document(
                id="1", text="Document", score=0.9, metadata={"source": "test", "author": "user"}
            ),
        ]

        mock_result = MagicMock()
        mock_result.index = 0
        mock_result.text = "Document"
        mock_result.score = 0.95

        mock_provider = MagicMock()
        mock_provider.arerank = AsyncMock(return_value=[mock_result])

        mock_factory = MagicMock()
        mock_factory.get_rerank_provider.return_value = mock_provider

        with patch("src.providers.factory.factory", mock_factory):
            reranker = PipelineReranker()
            reranked = await reranker.rerank("test query", docs)

            assert reranked[0].metadata == {"source": "test", "author": "user"}


class TestNoOpReranker:
    """Tests for NoOpReranker implementation."""

    def test_init(self):
        """Test NoOpReranker initializes."""
        reranker = NoOpReranker()
        assert reranker is not None

    def test_name_property(self):
        """Test NoOpReranker name property."""
        reranker = NoOpReranker()
        assert reranker.name == "NoOpReranker"

    @pytest.mark.asyncio
    async def test_rerank_returns_original_documents(self):
        """Test rerank returns original documents unchanged."""
        docs = [
            Document(id="1", text="First", score=0.9),
            Document(id="2", text="Second", score=0.8),
        ]

        reranker = NoOpReranker()
        reranked = await reranker.rerank("test query", docs)

        assert len(reranked) == 2
        assert reranked[0].id == "1"
        assert reranked[1].id == "2"

    @pytest.mark.asyncio
    async def test_rerank_respects_topk_option(self):
        """Test rerank respects topK option."""
        docs = [Document(id=str(i), text=f"Doc {i}", score=0.9) for i in range(10)]

        reranker = NoOpReranker()
        reranked = await reranker.rerank("test query", docs, {"topK": 3})

        assert len(reranked) == 3

    @pytest.mark.asyncio
    async def test_rerank_empty_documents(self):
        """Test rerank handles empty documents list."""
        reranker = NoOpReranker()
        reranked = await reranker.rerank("test query", [])

        assert isinstance(reranked, list)
        assert len(reranked) == 0


class TestFallbackReranker:
    """Tests for FallbackReranker implementation."""

    def test_init_with_primary_and_fallback(self):
        """Test FallbackReranker initializes with primary and fallback."""
        primary = NoOpReranker()
        fallback = NoOpReranker()

        reranker = FallbackReranker(primary=primary, fallback=fallback)
        assert reranker is not None

    def test_init_with_primary_only(self):
        """Test FallbackReranker initializes with primary only."""
        primary = NoOpReranker()

        reranker = FallbackReranker(primary=primary)
        assert reranker is not None

    def test_name_property(self):
        """Test FallbackReranker name property."""
        primary = NoOpReranker()
        reranker = FallbackReranker(primary=primary)
        assert reranker.name == "FallbackReranker"

    @pytest.mark.asyncio
    async def test_rerank_uses_primary_on_success(self):
        """Test rerank uses primary reranker on success."""
        docs = [
            Document(id="1", text="Document", score=0.9),
        ]

        mock_primary = MagicMock()
        mock_primary.rerank = AsyncMock(
            return_value=[
                Document(id="1", text="Document", score=0.95, rerank_score=0.95),
            ]
        )

        reranker = FallbackReranker(primary=mock_primary)
        reranked = await reranker.rerank("test query", docs)

        mock_primary.rerank.assert_called_once()
        assert len(reranked) == 1
        assert reranked[0].rerank_score == 0.95

    @pytest.mark.asyncio
    async def test_rerank_uses_fallback_on_primary_failure(self):
        """Test rerank uses fallback reranker on primary failure."""
        docs = [
            Document(id="1", text="Document", score=0.9),
        ]

        mock_primary = MagicMock()
        mock_primary.rerank = AsyncMock(side_effect=Exception("Primary failed"))

        mock_fallback = MagicMock()
        mock_fallback.rerank = AsyncMock(return_value=docs)

        reranker = FallbackReranker(primary=mock_primary, fallback=mock_fallback)
        reranked = await reranker.rerank("test query", docs)

        mock_primary.rerank.assert_called_once()
        mock_fallback.rerank.assert_called_once()
        assert len(reranked) == 1

    @pytest.mark.asyncio
    async def test_rerank_uses_noop_as_default_fallback(self):
        """Test rerank uses NoOpReranker as default fallback."""
        docs = [
            Document(id="1", text="Document", score=0.9),
        ]

        mock_primary = MagicMock()
        mock_primary.rerank = AsyncMock(side_effect=Exception("Primary failed"))

        reranker = FallbackReranker(primary=mock_primary)
        reranked = await reranker.rerank("test query", docs)

        # Should use NoOpReranker which returns original docs
        assert len(reranked) == 1
        assert reranked[0].id == "1"
