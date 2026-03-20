"""Tests for pipeline context_builder module.

These tests verify:
- ContextBuilder abstract base class interface
- DefaultContextBuilder implementation
- MultiQueryContextBuilder implementation
- Deduplication and sorting functionality

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

import pytest
from unittest.mock import MagicMock

from pipeline.context_builder import (
    ContextBuilder,
    DefaultContextBuilder,
    MultiQueryContextBuilder,
)
from pipeline.result import Document


class TestContextBuilderABC:
    """Tests for ContextBuilder abstract base class."""

    def test_context_builder_is_abstract(self):
        """Test ContextBuilder cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ContextBuilder()

    def test_context_builder_requires_build_method(self):
        """Test ContextBuilder subclass must implement build method."""
        
        class IncompleteBuilder(ContextBuilder):
            pass
        
        with pytest.raises(TypeError):
            IncompleteBuilder()

    def test_context_builder_name_property(self):
        """Test ContextBuilder has name property."""
        
        class TestBuilder(ContextBuilder):
            def build(self, documents, limit, options=None):
                return documents[:limit]
        
        builder = TestBuilder()
        assert builder.name == "TestBuilder"


class TestDefaultContextBuilder:
    """Tests for DefaultContextBuilder implementation."""

    def test_init(self):
        """Test DefaultContextBuilder can be initialized."""
        builder = DefaultContextBuilder()
        assert builder is not None

    def test_name_property(self):
        """Test DefaultContextBuilder name property."""
        builder = DefaultContextBuilder()
        assert builder.name == "DefaultContextBuilder"

    def test_build_returns_documents(self):
        """Test build returns list of documents."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ]
        
        result = builder.build(docs, limit=5)
        
        assert isinstance(result, list)
        assert len(result) == 2

    def test_build_respects_limit(self):
        """Test build truncates to limit."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id=str(i), text=f"doc {i}", score=0.9 - i * 0.1)
            for i in range(10)
        ]
        
        result = builder.build(docs, limit=3)
        
        assert len(result) == 3

    def test_build_sorts_by_score_descending(self):
        """Test build sorts documents by score in descending order."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="low", score=0.5),
            Document(id="2", text="high", score=0.9),
            Document(id="3", text="medium", score=0.7),
        ]
        
        result = builder.build(docs, limit=10)
        
        assert result[0].score == 0.9
        assert result[1].score == 0.7
        assert result[2].score == 0.5

    def test_build_empty_documents(self):
        """Test build with empty documents returns empty list."""
        builder = DefaultContextBuilder()
        
        result = builder.build([], limit=5)
        
        assert result == []

    def test_build_deduplicates_by_content(self):
        """Test build removes duplicate documents by content hash."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="same content", score=0.9),
            Document(id="2", text="same content", score=0.8),  # duplicate
            Document(id="3", text="different", score=0.7),
        ]
        
        result = builder.build(docs, limit=10, options={"remove_duplicates": True})
        
        assert len(result) == 2

    def test_build_keeps_first_occurrence_on_duplicate(self):
        """Test build keeps first occurrence when deduplicating."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="first", text="same", score=0.9),
            Document(id="second", text="same", score=0.99),  # higher score but duplicate
        ]
        
        result = builder.build(docs, limit=10, options={"remove_duplicates": True})
        
        assert len(result) == 1
        assert result[0].id == "first"

    def test_build_without_deduplication(self):
        """Test build with remove_duplicates=False keeps all docs."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="same", score=0.9),
            Document(id="2", text="same", score=0.8),
        ]
        
        result = builder.build(docs, limit=10, options={"remove_duplicates": False})
        
        assert len(result) == 2

    def test_build_default_remove_duplicates(self):
        """Test build defaults to removing duplicates."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="same", score=0.9),
            Document(id="2", text="same", score=0.8),
        ]
        
        result = builder.build(docs, limit=10)  # no options
        
        assert len(result) == 1

    def test_build_with_none_options(self):
        """Test build handles None options."""
        builder = DefaultContextBuilder()
        docs = [Document(id="1", text="doc", score=0.9)]
        
        result = builder.build(docs, limit=5, options=None)
        
        assert len(result) == 1


class TestMultiQueryContextBuilder:
    """Tests for MultiQueryContextBuilder implementation."""

    def test_init_default(self):
        """Test MultiQueryContextBuilder can be initialized."""
        builder = MultiQueryContextBuilder()
        assert builder is not None

    def test_init_with_inner_builder(self):
        """Test MultiQueryContextBuilder with custom inner builder."""
        inner = DefaultContextBuilder()
        builder = MultiQueryContextBuilder(inner_builder=inner)
        
        assert builder._inner is inner

    def test_init_creates_default_inner(self):
        """Test MultiQueryContextBuilder creates DefaultContextBuilder by default."""
        builder = MultiQueryContextBuilder()
        
        assert isinstance(builder._inner, DefaultContextBuilder)

    def test_name_property(self):
        """Test MultiQueryContextBuilder name property."""
        builder = MultiQueryContextBuilder()
        assert builder.name == "MultiQueryContextBuilder"

    def test_build_returns_documents(self):
        """Test build returns list of documents."""
        builder = MultiQueryContextBuilder()
        docs = [
            Document(id="1", text="doc 1", score=0.9),
            Document(id="2", text="doc 2", score=0.8),
        ]
        
        result = builder.build(docs, limit=5)
        
        assert isinstance(result, list)

    def test_build_deduplicates_by_id(self):
        """Test build deduplicates documents by ID."""
        builder = MultiQueryContextBuilder()
        docs = [
            Document(id="same_id", text="doc 1", score=0.9),
            Document(id="same_id", text="doc 2", score=0.8),  # same ID
            Document(id="different", text="doc 3", score=0.7),
        ]
        
        result = builder.build(docs, limit=10)
        
        assert len(result) == 2

    def test_build_keeps_higher_score_on_duplicate_id(self):
        """Test build keeps document with higher score when ID duplicates."""
        builder = MultiQueryContextBuilder()
        docs = [
            Document(id="same_id", text="version 1", score=0.7),
            Document(id="same_id", text="version 2", score=0.9),  # higher score
        ]
        
        result = builder.build(docs, limit=10)
        
        assert len(result) == 1
        assert result[0].score == 0.9

    def test_build_respects_limit(self):
        """Test build respects limit parameter."""
        builder = MultiQueryContextBuilder()
        docs = [
            Document(id=str(i), text=f"doc {i}", score=0.9 - i * 0.05)
            for i in range(10)
        ]
        
        result = builder.build(docs, limit=3)
        
        assert len(result) <= 3

    def test_build_uses_inner_builder(self):
        """Test build delegates to inner builder."""
        mock_inner = MagicMock()
        mock_inner.build.return_value = [Document(id="1", text="test", score=0.9)]
        
        builder = MultiQueryContextBuilder(inner_builder=mock_inner)
        docs = [Document(id="1", text="doc", score=0.9)]
        
        builder.build(docs, limit=5)
        
        mock_inner.build.assert_called_once()

    def test_build_with_options(self):
        """Test build passes options to inner builder."""
        mock_inner = MagicMock()
        mock_inner.build.return_value = []
        
        builder = MultiQueryContextBuilder(inner_builder=mock_inner)
        docs = [Document(id="1", text="doc", score=0.9)]
        
        builder.build(docs, limit=5, options={"custom": "value"})
        
        # Inner builder should be called with deduped docs
        call_args = mock_inner.build.call_args
        assert call_args[0][1] == 5  # limit


class TestContextBuilderEdgeCases:
    """Tests for edge cases in context builders."""

    def test_default_builder_with_zero_limit(self):
        """Test DefaultContextBuilder with zero limit."""
        builder = DefaultContextBuilder()
        docs = [Document(id="1", text="doc", score=0.9)]
        
        result = builder.build(docs, limit=0)
        
        assert len(result) == 0

    def test_default_builder_with_negative_scores(self):
        """Test DefaultContextBuilder handles negative scores."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="neg", score=-0.5),
            Document(id="2", text="pos", score=0.5),
        ]
        
        result = builder.build(docs, limit=10)
        
        # Positive score should come first (descending order)
        assert result[0].score == 0.5
        assert result[1].score == -0.5

    def test_default_builder_with_same_scores(self):
        """Test DefaultContextBuilder with equal scores."""
        builder = DefaultContextBuilder()
        docs = [
            Document(id="1", text="a", score=0.5),
            Document(id="2", text="b", score=0.5),
            Document(id="3", text="c", score=0.5),
        ]
        
        result = builder.build(docs, limit=10)
        
        assert len(result) == 3

    def test_multiquery_builder_empty_documents(self):
        """Test MultiQueryContextBuilder with empty documents."""
        builder = MultiQueryContextBuilder()
        
        result = builder.build([], limit=5)
        
        assert result == []

    def test_multiquery_builder_single_document(self):
        """Test MultiQueryContextBuilder with single document."""
        builder = MultiQueryContextBuilder()
        docs = [Document(id="only", text="single", score=0.9)]
        
        result = builder.build(docs, limit=5)
        
        assert len(result) == 1
        assert result[0].id == "only"