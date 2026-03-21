"""Tests for pipeline module - RAGResult and RAGPipeline.

These tests verify:
- RAGResult dataclass creation and attributes
- RAGPipeline abstract base class interface
- DefaultRAGPipeline implementation
- PipelineFactory configuration-driven creation

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pipeline.base import RAGPipeline
from pipeline.default import DefaultRAGPipeline
from pipeline.result import Document, RAGResult


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
        retriever.retrieve = AsyncMock(
            return_value=[
                Document(id="1", text="doc 1", score=0.9),
                Document(id="2", text="doc 2", score=0.8),
            ]
        )
        return retriever

    @pytest.fixture
    def mock_reranker(self):
        """Create a mock reranker."""
        reranker = MagicMock()
        reranker.rerank = AsyncMock(
            return_value=[
                Document(id="2", text="doc 2", score=0.95),
                Document(id="1", text="doc 1", score=0.9),
            ]
        )
        return reranker

    @pytest.mark.asyncio
    async def test_run_returns_rag_result(self):
        """Test run method returns RAGResult."""
        # Use mock retriever to avoid dependency on actual Chroma service
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(
            return_value=[
                Document(id="1", text="doc 1", score=0.9),
            ]
        )

        pipeline = DefaultRAGPipeline(retriever=mock_retriever, reranker=None)

        result = await pipeline.run("test query", {"topK": 5, "rerank": False})

        assert isinstance(result, RAGResult)
        assert result.query == "test query"

    @pytest.mark.asyncio
    async def test_run_with_retriever(self):
        """Test run method uses retriever."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(
            return_value=[
                Document(id="1", text="doc 1", score=0.9),
            ]
        )

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
        mock_retriever.retrieve = AsyncMock(
            return_value=[
                Document(id="1", text="doc 1", score=0.9),
                Document(id="2", text="doc 2", score=0.8),
            ]
        )

        mock_reranker = MagicMock()
        mock_reranker.rerank = AsyncMock(
            return_value=[
                Document(id="2", text="doc 2", score=0.95),
                Document(id="1", text="doc 1", score=0.9),
            ]
        )

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
        mock_retriever.retrieve = AsyncMock(
            return_value=[
                Document(id=str(i), text=f"doc {i}", score=1.0 - i * 0.1) for i in range(10)
            ]
        )

        pipeline = DefaultRAGPipeline(retriever=mock_retriever)
        result = await pipeline.run("test query", {"topK": 3})

        assert len(result.documents) <= 3

    @pytest.mark.asyncio
    async def test_run_without_reranker(self):
        """Test run method works without reranker."""
        mock_retriever = MagicMock()
        mock_retriever.retrieve = AsyncMock(
            return_value=[
                Document(id="1", text="doc 1", score=0.9),
            ]
        )

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

    def test_create_pipeline_unknown_type_raises_error(self):
        """Test factory raises ValueError for unknown pipeline type."""
        from pipeline.factory import PipelineFactory

        with pytest.raises(ValueError, match="Unknown pipeline type"):
            PipelineFactory.create({"type": "unknown_type"})

    def test_get_profile(self):
        """Test factory get_profile method."""
        from pipeline.factory import PipelineFactory

        profile = PipelineFactory.get_profile("fast")

        assert isinstance(profile, dict)
        assert "rerank" in profile
        assert profile["rerank"] is False

    def test_get_profile_unknown_returns_default(self):
        """Test factory get_profile returns balanced for unknown profile."""
        from pipeline.factory import PipelineFactory

        profile = PipelineFactory.get_profile("unknown_profile")

        assert profile == PipelineFactory.get_profile("balanced")

    def test_list_profiles(self):
        """Test factory list_profiles method."""
        from pipeline.factory import PipelineFactory

        profiles = PipelineFactory.list_profiles()

        assert isinstance(profiles, list)
        assert "fast" in profiles
        assert "balanced" in profiles
        assert "accurate" in profiles

    def test_create_pipeline_with_vector_retriever(self):
        """Test factory can create pipeline with vector retriever."""
        from pipeline.factory import PipelineFactory

        config = {
            "type": "default",
            "retriever": {"type": "vector", "collection": "test_collection"},
        }

        pipeline = PipelineFactory.create(config)

        assert pipeline is not None

    def test_create_pipeline_unknown_retriever_raises_error(self):
        """Test factory raises ValueError for unknown retriever type."""
        from pipeline.factory import PipelineFactory

        config = {
            "type": "default",
            "retriever": {"type": "unknown_retriever"},
        }

        with pytest.raises(ValueError, match="Unknown retriever type"):
            PipelineFactory.create(config)

    def test_create_pipeline_with_noop_reranker(self):
        """Test factory can create pipeline with NoOp reranker."""
        from pipeline.factory import PipelineFactory

        config = {
            "type": "default",
            "rerank_config": {"type": "none"},
        }

        pipeline = PipelineFactory.create(config)

        assert pipeline is not None

    def test_create_pipeline_unknown_reranker_raises_error(self):
        """Test factory raises ValueError for unknown reranker type."""
        from pipeline.factory import PipelineFactory

        config = {
            "type": "default",
            "rerank_config": {"type": "unknown_reranker"},
        }

        # Need rerank=True to trigger reranker creation
        config["rerank"] = True

        with pytest.raises(ValueError, match="Unknown reranker type"):
            PipelineFactory.create(config)

    def test_create_pipeline_unknown_context_builder_raises_error(self):
        """Test factory raises ValueError for unknown context builder type."""
        from pipeline.factory import PipelineFactory

        config = {
            "type": "default",
            "context_builder": {"type": "unknown_builder"},
        }

        with pytest.raises(ValueError, match="Unknown context builder type"):
            PipelineFactory.create(config)

    def test_factory_get_pipeline_convenience_function(self):
        """Test factory get_pipeline convenience function."""
        from pipeline.factory import get_pipeline as factory_get_pipeline

        pipeline = factory_get_pipeline("fast")

        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)


class TestDocumentExtended:
    """Extended tests for Document dataclass."""

    def test_document_from_dict(self):
        """Test Document.from_dict creates Document from dictionary."""
        data = {
            "id": "test-id",
            "text": "test content",
            "score": 0.95,
            "metadata": {"source": "test"},
            "vector_score": 0.9,
            "bm25_score": 0.8,
            "rerank_score": 0.95,
        }

        doc = Document.from_dict(data)

        assert doc.id == "test-id"
        assert doc.text == "test content"
        assert doc.score == 0.95
        assert doc.metadata == {"source": "test"}
        assert doc.vector_score == 0.9
        assert doc.bm25_score == 0.8
        assert doc.rerank_score == 0.95

    def test_document_from_dict_partial(self):
        """Test Document.from_dict with partial data uses defaults."""
        data = {"id": "partial"}

        doc = Document.from_dict(data)

        assert doc.id == "partial"
        assert doc.text == ""
        assert doc.score == 0.0
        assert doc.metadata == {}

    def test_document_from_dict_empty(self):
        """Test Document.from_dict with empty dict."""
        doc = Document.from_dict({})

        assert doc.id == ""
        assert doc.text == ""

    def test_document_to_dict_includes_all_fields(self):
        """Test Document.to_dict includes all fields."""
        doc = Document(
            id="1",
            text="content",
            score=0.9,
            metadata={"key": "value"},
            vector_score=0.85,
            bm25_score=0.75,
            rerank_score=0.95,
        )

        result = doc.to_dict()

        assert result["id"] == "1"
        assert result["text"] == "content"
        assert result["score"] == 0.9
        assert result["metadata"] == {"key": "value"}
        assert result["vector_score"] == 0.85
        assert result["bm25_score"] == 0.75
        assert result["rerank_score"] == 0.95


class TestRAGResultExtended:
    """Extended tests for RAGResult dataclass."""

    def test_rag_result_from_dict(self):
        """Test RAGResult.from_dict creates result from dictionary."""
        data = {
            "query": "test query",
            "documents": [
                {"id": "1", "text": "doc 1", "score": 0.9},
                {"id": "2", "text": "doc 2", "score": 0.8},
            ],
            "total_results": 2,
            "execution_time_ms": 100.5,
            "profile": "balanced",
            "metadata": {"source": "test"},
        }

        result = RAGResult.from_dict(data)

        assert result.query == "test query"
        assert len(result.documents) == 2
        assert result.total_results == 2
        assert result.execution_time_ms == 100.5
        assert result.profile == "balanced"
        assert result.metadata == {"source": "test"}

    def test_rag_result_from_dict_with_document_objects(self):
        """Test RAGResult.from_dict handles Document objects."""
        docs = [Document(id="1", text="doc", score=0.9)]
        data = {
            "query": "test",
            "documents": docs,
        }

        result = RAGResult.from_dict(data)

        assert len(result.documents) == 1
        assert result.documents[0].id == "1"

    def test_rag_result_from_dict_empty_documents(self):
        """Test RAGResult.from_dict with empty documents."""
        data = {"query": "test", "documents": []}

        result = RAGResult.from_dict(data)

        assert result.documents == []
        assert result.total_results == 0

    def test_rag_result_len(self):
        """Test RAGResult __len__ method."""
        docs = [
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ]
        result = RAGResult(query="test", documents=docs)

        assert len(result) == 2

    def test_rag_result_iter(self):
        """Test RAGResult __iter__ method."""
        docs = [
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ]
        result = RAGResult(query="test", documents=docs)

        ids = [doc.id for doc in result]

        assert ids == ["1", "2"]

    def test_rag_result_getitem(self):
        """Test RAGResult __getitem__ method."""
        docs = [
            Document(id="first", text="doc 1", score=0.9),
            Document(id="second", text="doc 2", score=0.8),
        ]
        result = RAGResult(query="test", documents=docs)

        assert result[0].id == "first"
        assert result[1].id == "second"

    def test_rag_result_getitem_negative_index(self):
        """Test RAGResult __getitem__ with negative index."""
        docs = [
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ]
        result = RAGResult(query="test", documents=docs)

        assert result[-1].id == "2"


class TestDefaultRAGPipelineExtended:
    """Extended tests for DefaultRAGPipeline."""

    @pytest.fixture
    def mock_retriever(self):
        """Create a mock retriever."""
        retriever = MagicMock()
        retriever.retrieve = AsyncMock(
            return_value=[
                Document(id="1", text="doc 1", score=0.9),
                Document(id="2", text="doc 2", score=0.8),
            ]
        )
        retriever.name = "MockRetriever"
        return retriever

    @pytest.fixture
    def mock_reranker(self):
        """Create a mock reranker."""
        reranker = MagicMock()
        reranker.rerank = AsyncMock(
            return_value=[
                Document(id="2", text="doc 2", score=0.95),
                Document(id="1", text="doc 1", score=0.9),
            ]
        )
        reranker.name = "MockReranker"
        return reranker

    @pytest.fixture
    def mock_context_builder(self):
        """Create a mock context builder."""
        builder = MagicMock()
        builder.build.return_value = [
            Document(id="1", text="doc 1", score=0.9),
        ]
        builder.name = "MockBuilder"
        return builder

    def test_retriever_property(self, mock_retriever):
        """Test retriever property returns retriever."""
        pipeline = DefaultRAGPipeline(retriever=mock_retriever)

        assert pipeline.retriever is mock_retriever

    def test_reranker_property(self, mock_retriever, mock_reranker):
        """Test reranker property returns reranker."""
        pipeline = DefaultRAGPipeline(
            retriever=mock_retriever,
            reranker=mock_reranker,
        )

        assert pipeline.reranker is mock_reranker

    def test_reranker_property_none(self, mock_retriever):
        """Test reranker property returns None when not set."""
        pipeline = DefaultRAGPipeline(retriever=mock_retriever, reranker=None)

        assert pipeline.reranker is None

    def test_context_builder_property(self, mock_retriever, mock_context_builder):
        """Test context_builder property returns builder."""
        pipeline = DefaultRAGPipeline(
            retriever=mock_retriever,
            context_builder=mock_context_builder,
        )

        assert pipeline.context_builder is mock_context_builder

    def test_enable_reranking(self, mock_retriever, mock_reranker):
        """Test enable_reranking method."""
        pipeline = DefaultRAGPipeline(retriever=mock_retriever, reranker=None)

        pipeline.enable_reranking(mock_reranker)

        assert pipeline.reranker is mock_reranker

    def test_disable_reranking(self, mock_retriever, mock_reranker):
        """Test disable_reranking method."""
        pipeline = DefaultRAGPipeline(
            retriever=mock_retriever,
            reranker=mock_reranker,
        )

        pipeline.disable_reranking()

        assert pipeline.reranker is not None
        assert pipeline.reranker.name == "NoOpReranker"

    def test_repr(self, mock_retriever, mock_reranker, mock_context_builder):
        """Test __repr__ method."""
        pipeline = DefaultRAGPipeline(
            retriever=mock_retriever,
            reranker=mock_reranker,
            context_builder=mock_context_builder,
        )

        repr_str = repr(pipeline)

        assert "DefaultRAGPipeline" in repr_str
        assert "MockRetriever" in repr_str
        assert "MockReranker" in repr_str
        assert "MockBuilder" in repr_str

    def test_repr_without_reranker(self, mock_retriever):
        """Test __repr__ without reranker."""
        pipeline = DefaultRAGPipeline(retriever=mock_retriever, reranker=None)

        repr_str = repr(pipeline)

        assert "None" in repr_str


class TestRAGPipelineBaseExtended:
    """Extended tests for RAGPipeline base class."""

    def test_pipeline_name_property(self):
        """Test pipeline name property returns class name."""

        class TestPipeline(RAGPipeline):
            async def run(self, query: str, options: dict) -> RAGResult:
                return RAGResult(query=query, documents=[], total_results=0)

        pipeline = TestPipeline()

        assert pipeline.name == "TestPipeline"

    def test_pipeline_repr(self):
        """Test pipeline __repr__ method."""

        class TestPipeline(RAGPipeline):
            async def run(self, query: str, options: dict) -> RAGResult:
                return RAGResult(query=query, documents=[], total_results=0)

        pipeline = TestPipeline()

        assert repr(pipeline) == "TestPipeline()"
