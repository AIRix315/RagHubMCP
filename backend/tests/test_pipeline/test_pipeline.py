"""Tests for pipeline module - RAGResult and RAGPipeline.

These tests verify:
- RAGResult dataclass creation and attributes
- RAGPipeline abstract base class interface
- DefaultRAGPipeline implementation
- PipelineFactory configuration-driven creation

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

import pytest
from dataclasses import asdict
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.result import RAGResult, Document
from pipeline.base import RAGPipeline
from pipeline.default import DefaultRAGPipeline


class TestRAGResult:
    """Tests for RAGResult dataclass."""

    def test_rag_result_creation(self):
        """Test RAGResult can be created with required fields."""
        docs = [
            Document(id="1", text="test doc 1", score=0.9),
            Document(id="2", text="test doc 2", score=0.8),
        ]
        result = RAGResult(
            query="test query",
            documents=docs,
            total_results=2,
        )

        assert result.query == "test query"
        assert len(result.documents) == 2
        assert result.total_results == 2

    def test_rag_result_to_dict(self):
        """Test RAGResult can be serialized to dict."""
        docs = [
            Document(id="1", text="test doc", score=0.9, metadata={"source": "test"}),
        ]
        result = RAGResult(
            query="test query",
            documents=docs,
            total_results=1,
        )

        result_dict = result.to_dict()

        assert "query" in result_dict
        assert "documents" in result_dict
        assert result_dict["query"] == "test query"
        assert len(result_dict["documents"]) == 1

    def test_document_creation(self):
        """Test Document dataclass."""
        doc = Document(
            id="test-id",
            text="test content",
            score=0.95,
            metadata={"author": "test"},
        )

        assert doc.id == "test-id"
        assert doc.text == "test content"
        assert doc.score == 0.95
        assert doc.metadata["author"] == "test"


class TestRAGPipeline:
    """Tests for RAGPipeline abstract base class."""

    def test_pipeline_is_abstract(self):
        """Test RAGPipeline cannot be instantiated directly."""
        with pytest.raises(TypeError):
            RAGPipeline()

    def test_pipeline_requires_run_method(self):
        """Test RAGPipeline subclass must implement run method."""
        
        class IncompletePipeline(RAGPipeline):
            pass
        
        with pytest.raises(TypeError):
            IncompletePipeline()

    def test_pipeline_run_method_signature(self):
        """Test complete pipeline can be instantiated."""
        
        class CompletePipeline(RAGPipeline):
            async def run(self, query: str, options: dict) -> RAGResult:
                return RAGResult(query=query, documents=[], total_results=0)
        
        pipeline = CompletePipeline()
        assert hasattr(pipeline, "run")


class TestDefaultRAGPipeline:
    """Tests for DefaultRAGPipeline implementation."""

    @pytest.fixture
    def mock_retriever(self):
        """Create a mock retriever."""
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(return_value=[
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ])
        return retriever

    @pytest.fixture
    def mock_reranker(self):
        """Create a mock reranker."""
        reranker = MagicMock()
        reranker.rerank = AsyncMock(return_value=[
            Document(id="2", text="doc 2", score=0.95),
            Document(id="1", text="doc 1", score=0.9),
        ])
        return reranker

    @pytest.mark.asyncio
    async def test_run_returns_rag_result(self):
        """Test run method returns RAGResult."""
        pipeline = DefaultRAGPipeline()
        
        result = await pipeline.run("test query", {"topK": 5})
        
        assert isinstance(result, RAGResult)
        assert result.query == "test query"

    @pytest.mark.asyncio
    async def test_run_with_retriever(self):
        """Test run method uses retriever."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(return_value=[
            Document(id="1", text="doc 1", score=0.9),
        ])
        
        pipeline = DefaultRAGPipeline(retriever=mock_retriever)
        result = await pipeline.run("test query", {"topK": 5})
        
        mock_retriever.retrieve.assert_called_once()
        # Check the call includes the query
        call_args = mock_retriever.retrieve.call_args
        assert call_args[0][0] == "test query"

    @pytest.mark.asyncio
    async def test_run_with_reranker(self):
        """Test run method applies reranking."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(return_value=[
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ])
        
        mock_reranker = MagicMock()
        mock_reranker.rerank = AsyncMock(return_value=[
            Document(id="2", text="doc 2", score=0.95),
            Document(id="1", text="doc 1", score=0.9),
        ])
        
        pipeline = DefaultRAGPipeline(
            retriever=mock_retriever,
            reranker=mock_reranker,
        )
        
        result = await pipeline.run("test query", {"topK": 5, "rerank": True})
        
        mock_reranker.rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_respects_topk(self):
        """Test run method respects topK option."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(return_value=[
            Document(id=str(i), text=f"doc {i}", score=1.0 - i * 0.1)
            for i in range(10)
        ])
        
        pipeline = DefaultRAGPipeline(retriever=mock_retriever)
        result = await pipeline.run("test query", {"topK": 3})
        
        assert len(result.documents) <= 3

    @pytest.mark.asyncio
    async def test_run_without_reranker(self):
        """Test run method works without reranker."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(return_value=[
            Document(id="1", text="doc 1", score=0.9),
        ])
        
        pipeline = DefaultRAGPipeline(
            retriever=mock_retriever,
            reranker=None,
        )
        
        result = await pipeline.run("test query", {"topK": 5, "rerank": False})
        
        assert isinstance(result, RAGResult)


class TestPipelineFactory:
    """Tests for PipelineFactory."""

    def test_create_default_pipeline(self):
        """Test factory can create default pipeline."""
        from pipeline.factory import PipelineFactory
        
        config = {
            "type": "default",
            "retriever": {"type": "hybrid"},
            "rerank": {"enabled": True},
        }
        
        pipeline = PipelineFactory.create(config)
        
        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)

    def test_create_pipeline_with_profile(self):
        """Test factory can create pipeline with profile."""
        from pipeline.factory import PipelineFactory
        
        config = {
            "type": "default",
            "profile": "balanced",
        }
        
        pipeline = PipelineFactory.create(config)
        
        assert pipeline is not None