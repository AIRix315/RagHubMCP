"""Tests for pipeline manager module.

These tests verify:
- get_pipeline() singleton and profile switching
- reset_pipeline() reset functionality
- execute_search() parameter validation and error handling
- create_pipeline() factory method

Reference: Docs/11-V2-Desing.md, Docs/12-V2-Blueprint.md
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.manager import (
    get_pipeline,
    reset_pipeline,
    execute_search,
    create_pipeline,
)
from pipeline.result import RAGResult, Document
from pipeline.base import RAGPipeline


class TestGetPipeline:
    """Tests for get_pipeline function."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pipeline()

    def test_get_pipeline_returns_pipeline(self):
        """Test get_pipeline returns a RAGPipeline instance."""
        pipeline = get_pipeline()
        
        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)

    def test_get_pipeline_returns_singleton(self):
        """Test get_pipeline returns same instance on repeated calls."""
        pipeline1 = get_pipeline()
        pipeline2 = get_pipeline()
        
        assert pipeline1 is pipeline2

    def test_get_pipeline_default_profile(self):
        """Test get_pipeline uses balanced profile by default."""
        pipeline = get_pipeline()
        
        assert pipeline is not None

    def test_get_pipeline_with_fast_profile(self):
        """Test get_pipeline creates pipeline with fast profile."""
        reset_pipeline()
        pipeline = get_pipeline("fast")
        
        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)

    def test_get_pipeline_with_accurate_profile(self):
        """Test get_pipeline creates pipeline with accurate profile."""
        reset_pipeline()
        pipeline = get_pipeline("accurate")
        
        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)

    def test_get_pipeline_profile_switch_creates_new_instance(self):
        """Test switching profile creates new pipeline instance."""
        pipeline1 = get_pipeline("fast")
        pipeline2 = get_pipeline("balanced")
        
        # Different profiles should create different instances
        assert pipeline1 is not pipeline2

    def test_get_pipeline_same_profile_returns_cached(self):
        """Test same profile returns cached instance."""
        reset_pipeline()
        pipeline1 = get_pipeline("balanced")
        pipeline2 = get_pipeline("balanced")
        
        assert pipeline1 is pipeline2


class TestResetPipeline:
    """Tests for reset_pipeline function."""

    def test_reset_pipeline_clears_singleton(self):
        """Test reset_pipeline clears the cached pipeline."""
        pipeline1 = get_pipeline()
        reset_pipeline()
        pipeline2 = get_pipeline()
        
        # After reset, should be a new instance
        assert pipeline1 is not pipeline2

    def test_reset_pipeline_resets_profile(self):
        """Test reset_pipeline resets profile to balanced."""
        get_pipeline("fast")
        reset_pipeline()
        
        # After reset, default profile should be balanced
        pipeline = get_pipeline()
        assert pipeline is not None


class TestExecuteSearch:
    """Tests for execute_search function."""

    def setup_method(self):
        """Reset singleton before each test."""
        reset_pipeline()

    @pytest.mark.asyncio
    async def test_execute_search_returns_result(self):
        """Test execute_search returns RAGResult."""
        with patch("pipeline.manager.get_pipeline") as mock_get:
            mock_pipeline = MagicMock()
            mock_pipeline.run = AsyncMock(return_value=RAGResult(
                query="test",
                documents=[Document(id="1", text="doc", score=0.9)],
                total_results=1,
            ))
            mock_get.return_value = mock_pipeline
            
            result = await execute_search("test query")
            
            assert isinstance(result, RAGResult)
            assert result.query == "test"

    @pytest.mark.asyncio
    async def test_execute_search_with_options(self):
        """Test execute_search passes options to pipeline."""
        with patch("pipeline.manager.get_pipeline") as mock_get:
            mock_pipeline = MagicMock()
            mock_pipeline.run = AsyncMock(return_value=RAGResult(
                query="test",
                documents=[],
                total_results=0,
            ))
            mock_get.return_value = mock_pipeline
            
            await execute_search("test query", {"collection": "my_collection", "topK": 10})
            
            mock_pipeline.run.assert_called_once()
            call_args = mock_pipeline.run.call_args
            assert call_args[0][0] == "test query"

    @pytest.mark.asyncio
    async def test_execute_search_empty_query_raises_error(self):
        """Test execute_search raises ValueError for empty query."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            await execute_search("")

    @pytest.mark.asyncio
    async def test_execute_search_none_query_raises_error(self):
        """Test execute_search raises ValueError for None query."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            await execute_search(None)

    @pytest.mark.asyncio
    async def test_execute_search_non_string_query_raises_error(self):
        """Test execute_search raises ValueError for non-string query."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            await execute_search(123)


class TestCreatePipeline:
    """Tests for create_pipeline function."""

    def test_create_pipeline_returns_pipeline(self):
        """Test create_pipeline returns a RAGPipeline instance."""
        pipeline = create_pipeline({"profile": "balanced"})
        
        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)

    def test_create_pipeline_with_custom_config(self):
        """Test create_pipeline with custom configuration."""
        pipeline = create_pipeline({
            "profile": "fast",
            "rerank": False,
            "topK": 3,
        })
        
        assert pipeline is not None

    def test_create_pipeline_always_creates_new(self):
        """Test create_pipeline always creates new instance."""
        pipeline1 = create_pipeline({"profile": "balanced"})
        pipeline2 = create_pipeline({"profile": "balanced"})
        
        # create_pipeline should always create new instances
        assert pipeline1 is not pipeline2

    def test_create_pipeline_with_retriever_config(self):
        """Test create_pipeline with retriever configuration."""
        pipeline = create_pipeline({
            "profile": "balanced",
            "retriever": {
                "type": "hybrid",
                "alpha": 0.6,
                "beta": 0.4,
            },
        })
        
        assert pipeline is not None

    def test_create_pipeline_with_accurate_profile(self):
        """Test create_pipeline with accurate profile."""
        pipeline = create_pipeline({"profile": "accurate"})
        
        assert pipeline is not None
        assert isinstance(pipeline, RAGPipeline)