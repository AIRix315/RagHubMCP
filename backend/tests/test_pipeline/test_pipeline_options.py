"""Tests for pipeline options module.

These tests verify:
- PipelineOptions dataclass creation and defaults
- to_dict() serialization
- from_dict() deserialization
- from_request() creation from request objects

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

import pytest
from dataclasses import asdict
from unittest.mock import MagicMock

from pipeline.options import PipelineOptions


class TestPipelineOptions:
    """Tests for PipelineOptions dataclass."""

    def test_default_values(self):
        """Test PipelineOptions has correct default values."""
        options = PipelineOptions()
        
        assert options.collection == "default"
        assert options.topK == 5
        assert options.rerank is True
        assert options.rerank_provider is None
        assert options.embedding_provider is None
        assert options.where is None
        assert options.where_document is None
        assert options.profile == "balanced"
        assert options.alpha == 0.5
        assert options.beta == 0.5

    def test_custom_values(self):
        """Test PipelineOptions with custom values."""
        options = PipelineOptions(
            collection="my_collection",
            topK=10,
            rerank=False,
            rerank_provider="flashrank",
            embedding_provider="openai",
            where={"category": "tech"},
            where_document={"$contains": "python"},
            profile="accurate",
            alpha=0.6,
            beta=0.4,
        )
        
        assert options.collection == "my_collection"
        assert options.topK == 10
        assert options.rerank is False
        assert options.rerank_provider == "flashrank"
        assert options.embedding_provider == "openai"
        assert options.where == {"category": "tech"}
        assert options.where_document == {"$contains": "python"}
        assert options.profile == "accurate"
        assert options.alpha == 0.6
        assert options.beta == 0.4


class TestPipelineOptionsToDict:
    """Tests for PipelineOptions.to_dict method."""

    def test_to_dict_returns_all_fields(self):
        """Test to_dict returns all fields."""
        options = PipelineOptions(
            collection="test_collection",
            topK=7,
            rerank=True,
            rerank_provider="cohere",
        )
        
        result = options.to_dict()
        
        assert isinstance(result, dict)
        assert result["collection"] == "test_collection"
        assert result["topK"] == 7
        assert result["rerank"] is True
        assert result["rerank_provider"] == "cohere"

    def test_to_dict_includes_none_values(self):
        """Test to_dict includes None values."""
        options = PipelineOptions()
        
        result = options.to_dict()
        
        assert "rerank_provider" in result
        assert result["rerank_provider"] is None
        assert "embedding_provider" in result
        assert result["embedding_provider"] is None

    def test_to_dict_includes_where_filters(self):
        """Test to_dict includes where filters."""
        options = PipelineOptions(
            where={"status": "active"},
            where_document={"$contains": "test"},
        )
        
        result = options.to_dict()
        
        assert result["where"] == {"status": "active"}
        assert result["where_document"] == {"$contains": "test"}

    def test_to_dict_includes_alpha_beta(self):
        """Test to_dict includes alpha and beta."""
        options = PipelineOptions(alpha=0.7, beta=0.3)
        
        result = options.to_dict()
        
        assert result["alpha"] == 0.7
        assert result["beta"] == 0.3


class TestPipelineOptionsFromDict:
    """Tests for PipelineOptions.from_dict class method."""

    def test_from_dict_with_all_fields(self):
        """Test from_dict with all fields."""
        data = {
            "collection": "custom_collection",
            "topK": 15,
            "rerank": False,
            "rerank_provider": "test_provider",
            "embedding_provider": "test_embedding",
            "where": {"type": "doc"},
            "where_document": {"$regex": ".*test.*"},
            "profile": "fast",
            "alpha": 0.8,
            "beta": 0.2,
        }
        
        options = PipelineOptions.from_dict(data)
        
        assert options.collection == "custom_collection"
        assert options.topK == 15
        assert options.rerank is False
        assert options.rerank_provider == "test_provider"
        assert options.embedding_provider == "test_embedding"
        assert options.where == {"type": "doc"}
        assert options.where_document == {"$regex": ".*test.*"}
        assert options.profile == "fast"
        assert options.alpha == 0.8
        assert options.beta == 0.2

    def test_from_dict_with_partial_fields(self):
        """Test from_dict with partial fields uses defaults."""
        data = {
            "collection": "my_collection",
            "topK": 8,
        }
        
        options = PipelineOptions.from_dict(data)
        
        assert options.collection == "my_collection"
        assert options.topK == 8
        assert options.rerank is True  # default
        assert options.profile == "balanced"  # default

    def test_from_dict_with_empty_dict(self):
        """Test from_dict with empty dict uses all defaults."""
        options = PipelineOptions.from_dict({})
        
        assert options.collection == "default"
        assert options.topK == 5
        assert options.rerank is True
        assert options.profile == "balanced"

    def test_from_dict_with_none_values(self):
        """Test from_dict handles None values."""
        data = {
            "collection": "test",
            "rerank_provider": None,
            "where": None,
        }
        
        options = PipelineOptions.from_dict(data)
        
        assert options.collection == "test"
        assert options.rerank_provider is None
        assert options.where is None


class TestPipelineOptionsFromRequest:
    """Tests for PipelineOptions.from_request class method."""

    def test_from_request_with_all_attributes(self):
        """Test from_request extracts all attributes."""
        request = MagicMock()
        request.collection_name = "request_collection"
        request.top_k = 20
        request.use_rerank = False
        request.rerank_provider = "flashrank"
        request.embedding_provider = "openai"
        request.where = {"category": "ai"}
        request.where_document = {"$contains": "data"}
        
        options = PipelineOptions.from_request(request)
        
        assert options.collection == "request_collection"
        assert options.topK == 20
        assert options.rerank is False
        assert options.rerank_provider == "flashrank"
        assert options.embedding_provider == "openai"
        assert options.where == {"category": "ai"}
        assert options.where_document == {"$contains": "data"}

    def test_from_request_with_missing_attributes(self):
        """Test from_request handles missing attributes with defaults."""
        request = MagicMock(spec=[])  # Empty spec, no attributes
        
        options = PipelineOptions.from_request(request)
        
        # Should use defaults from getattr
        assert options.collection == "default"
        assert options.topK == 5
        assert options.rerank is True

    def test_from_request_partial_attributes(self):
        """Test from_request with partial attributes."""
        request = MagicMock()
        request.collection_name = "partial_collection"
        request.top_k = 5  # Use default value
        request.use_rerank = True
        request.rerank_provider = None
        request.embedding_provider = None
        request.where = None
        request.where_document = None
        
        options = PipelineOptions.from_request(request)
        
        assert options.collection == "partial_collection"
        assert options.topK == 5

    def test_from_request_profile_defaults_to_balanced(self):
        """Test from_request always uses balanced profile."""
        request = MagicMock()
        request.collection_name = "test"
        
        options = PipelineOptions.from_request(request)
        
        assert options.profile == "balanced"
        assert options.alpha == 0.5
        assert options.beta == 0.5


class TestPipelineOptionsRoundTrip:
    """Tests for serialization round-trip."""

    def test_to_dict_from_dict_roundtrip(self):
        """Test to_dict -> from_dict roundtrip preserves data."""
        original = PipelineOptions(
            collection="roundtrip",
            topK=12,
            rerank=True,
            rerank_provider="test",
            where={"key": "value"},
            profile="accurate",
            alpha=0.6,
            beta=0.4,
        )
        
        data = original.to_dict()
        restored = PipelineOptions.from_dict(data)
        
        assert restored.collection == original.collection
        assert restored.topK == original.topK
        assert restored.rerank == original.rerank
        assert restored.rerank_provider == original.rerank_provider
        assert restored.where == original.where
        assert restored.profile == original.profile
        assert restored.alpha == original.alpha
        assert restored.beta == original.beta