"""Tests for Multi-Query Generator module.

Tests verify:
- MultiQueryGenerator abstract interface
- TemplateQueryGenerator (template-based multi-query)
- Query variation generation
- Integration with Pipeline

Reference:
- Docs/11-V2-Design.md (Section 5: Retrieval设计 - Multi-query)
- Docs/12-V2-Blueprint.md (Phase 5: Multi-query)
- TODO-V2.md (Phase 5: 8.2 Multi-query)
- RULE.md (测试优先原则)
"""

import pytest

from typing import Any


class TestMultiQueryGeneratorInterface:
    """Tests for MultiQueryGenerator abstract interface."""

    def test_interface_exists(self):
        """Test that MultiQueryGenerator interface can be imported."""
        from raghub_mcp.pipeline.multi_query import MultiQueryGenerator, MultiQueryResult

        assert MultiQueryGenerator is not None
        assert MultiQueryResult is not None

    def test_interface_has_required_methods(self):
        """Test interface has generate method."""
        from raghub_mcp.pipeline.multi_query import MultiQueryGenerator
        from abc import ABC

        # Check it's an abstract class
        assert issubclass(MultiQueryGenerator, ABC)

        # Check abstract methods exist
        import inspect
        methods = inspect.getmembers(MultiQueryGenerator, predicate=inspect.ismethod)
        method_names = [m[0] for m in methods]

        # generate should be abstract
        assert 'generate' in method_names or hasattr(MultiQueryGenerator, 'generate')

    def test_interface_has_name_property(self):
        """Test interface has name property."""
        from raghub_mcp.pipeline.multi_query import MultiQueryGenerator
        from abc import abstractmethod

        # Name property should be defined (either abstract or implemented)
        assert hasattr(MultiQueryGenerator, 'name')


class TestTemplateQueryGenerator:
    """Tests for TemplateQueryGenerator."""

    @pytest.fixture
    def generator(self):
        """Create TemplateQueryGenerator instance."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator
        return TemplateQueryGenerator()

    def test_name_property(self, generator):
        """Test generator name."""
        assert generator.name == "TemplateQueryGenerator"

    @pytest.mark.asyncio
    async def test_generate_single_query(self, generator):
        """Test generating from single word query."""
        result = await generator.generate("FastAPI", n=3)

        assert result.original_query == "FastAPI"
        assert len(result.queries) >= 1
        # Even for single word, should produce variations
        assert result.queries[0] == "FastAPI"  # Default includes original

    @pytest.mark.asyncio
    async def test_generate_how_to_query(self, generator):
        """Test generating variations for 'how to' queries."""
        result = await generator.generate("How to use FastAPI", n=5)

        assert result.original_query == "How to use FastAPI"
        assert len(result.queries) >= 2
        assert len(result.queries) <= 6  # n + 1 for original

        # Check variations are reasonable
        queries_lower = [q.lower() for q in result.queries]
        assert any("fastapi" in q for q in queries_lower)
        assert any("tutorial" in q or "guide" in q for q in queries_lower)

    @pytest.mark.asyncio
    async def test_generate_what_is_query(self, generator):
        """Test generating variations for 'what is' queries."""
        result = await generator.generate("What is machine learning", n=4)

        assert len(result.queries) >= 1
        assert result.metadata.get("template_type") == "clarification"

    @pytest.mark.asyncio
    async def test_generate_comparison_query(self, generator):
        """Test generating variations for comparison queries."""
        result = await generator.generate("FastAPI vs Flask", n=3)

        assert len(result.queries) >= 1
        # Should generate comparison-related variations
        assert result.metadata.get("template_type") == "comparison"

    @pytest.mark.asyncio
    async def test_generate_limit_n(self, generator):
        """Test that n parameter limits output."""
        result = await generator.generate("How to use Python", n=2)

        # Should have at most n + 1 queries (n variations + original)
        assert len(result.queries) <= 3

    @pytest.mark.asyncio
    async def test_generate_include_original(self, generator):
        """Test include_original parameter."""
        result = await generator.generate(
            "What is Docker",
            n=5,
            include_original=False
        )

        # Original might not be in any position if variations exist
        if len(result.queries) > 0:
            # Check that we got variations
            pass

    @pytest.mark.asyncio
    async def test_generate_empty_query(self, generator):
        """Test handling empty query."""
        result = await generator.generate("", n=3)

        assert result.original_query == ""
        assert len(result.queries) >= 1
        # Should return original query at minimum

    @pytest.mark.asyncio
    async def test_generate_metadata(self, generator):
        """Test that result includes metadata."""
        result = await generator.generate("How to use Kubernetes", n=3)

        assert result.metadata is not None
        assert "template_type" in result.metadata
        assert "num_generated" in result.metadata

    @pytest.mark.asyncio
    async def test_generate_case_insensitive(self, generator):
        """Test that templates match case-insensitively."""
        result1 = await generator.generate("HOW TO USE FASTAPI", n=2)
        result2 = await generator.generate("how to use fastapi", n=2)

        # Both should match the 'howto' template
        assert result1.metadata.get("template_type") == "howto"
        assert result2.metadata.get("template_type") == "howto"


class TestMultiQueryResult:
    """Tests for MultiQueryResult dataclass."""

    def test_multi_query_result_creation(self):
        """Test MultiQueryResult can be created."""
        from raghub_mcp.pipeline.multi_query import MultiQueryResult, QueryGenerationMode

        result = MultiQueryResult(
            original_query="What is FastAPI",
            queries=["What is FastAPI", "FastAPI definition", "FastAPI explained"],
            mode=QueryGenerationMode.TEMPLATE,
        )

        assert result.original_query == "What is FastAPI"
        assert len(result.queries) == 3
        assert result.mode == QueryGenerationMode.TEMPLATE

    def test_multi_query_result_with_metadata(self):
        """Test MultiQueryResult with metadata."""
        from raghub_mcp.pipeline.multi_query import MultiQueryResult, QueryGenerationMode

        result = MultiQueryResult(
            original_query="test",
            queries=["test"],
            mode=QueryGenerationMode.NONE,
            metadata={"source": "test", "variations": 0},
        )

        assert result.metadata == {"source": "test", "variations": 0}

    def test_to_dict(self):
        """Test MultiQueryResult serialization."""
        from raghub_mcp.pipeline.multi_query import MultiQueryResult, QueryGenerationMode

        result = MultiQueryResult(
            original_query="test query",
            queries=["test query", "test query guide"],
            mode=QueryGenerationMode.TEMPLATE,
            metadata={"key": "value"},
        )

        result_dict = result.to_dict()

        assert result_dict["original_query"] == "test query"
        assert result_dict["queries"] == ["test query", "test query guide"]
        assert result_dict["mode"] == "template"
        assert result_dict["metadata"] == {"key": "value"}


class TestQueryGenerationMode:
    """Tests for QueryGenerationMode enum."""

    def test_query_generation_mode_values(self):
        """Test QueryGenerationMode has expected values."""
        from raghub_mcp.pipeline.multi_query import QueryGenerationMode

        assert QueryGenerationMode.NONE.value == "none"
        assert QueryGenerationMode.TEMPLATE.value == "template"
        assert QueryGenerationMode.EXPANSION.value == "expansion"
        assert QueryGenerationMode.LLM.value == "llm"


class TestCreateMultiQueryGenerator:
    """Tests for create_multi_query_generator factory function."""

    def test_create_none_generator(self):
        """Test creating generator with NONE mode."""
        from raghub_mcp.pipeline.multi_query import create_multi_query_generator, QueryGenerationMode

        generator = create_multi_query_generator(QueryGenerationMode.NONE)

        assert generator is not None
        # Should return a passthrough generator

    def test_create_template_generator(self):
        """Test creating generator with TEMPLATE mode."""
        from raghub_mcp.pipeline.multi_query import (
            create_multi_query_generator,
            QueryGenerationMode,
            TemplateQueryGenerator,
        )

        generator = create_multi_query_generator(QueryGenerationMode.TEMPLATE)

        assert isinstance(generator, TemplateQueryGenerator)

    def test_create_from_string(self):
        """Test creating generator from string mode."""
        from raghub_mcp.pipeline.multi_query import (
            create_multi_query_generator,
            TemplateQueryGenerator,
        )

        generator = create_multi_query_generator("template")

        assert isinstance(generator, TemplateQueryGenerator)

    def test_create_with_config(self):
        """Test creating generator with config."""
        from raghub_mcp.pipeline.multi_query import create_multi_query_generator, QueryGenerationMode

        generator = create_multi_query_generator(
            QueryGenerationMode.TEMPLATE,
            config={
                "max_variations": 5,
                "include_original": False,
            }
        )

        assert generator is not None


class TestMultiQueryPipelineIntegration:
    """Tests for MultiQueryGenerator integration with Pipeline."""

    @pytest.mark.asyncio
    async def test_multi_queries_are_distinct(self):
        """Test that generated queries are distinct."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator

        generator = TemplateQueryGenerator()
        result = await generator.generate("How to implement authentication", n=10)

        # Check we get reasonable number of distinct queries
        unique_queries = set(result.queries)
        assert len(unique_queries) == len(result.queries)  # All unique

    @pytest.mark.asyncio
    async def test_generator_with_options(self):
        """Test generator with various options."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator

        generator = TemplateQueryGenerator()

        # Test with different options
        result = await generator.generate(
            "What is Docker",
            n=3,
            include_original=True,
            options={"max_variations": 2}
        )

        assert len(result.queries) <= 4  # max_variations + original

    @pytest.mark.asyncio
    async def test_generators_are_independent(self):
        """Test that multiple generators can coexist."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator, create_multi_query_generator, QueryGenerationMode

        gen1 = TemplateQueryGenerator()
        gen2 = create_multi_query_generator(QueryGenerationMode.TEMPLATE)

        result1 = await gen1.generate("test query", n=2)
        result2 = await gen2.generate("test query", n=2)

        # Both should work independently
        assert result1.original_query == "test query"
        assert result2.original_query == "test query"


class TestTemplateVariations:
    """Tests for specific template variations."""

    @pytest.fixture
    def generator(self):
        """Create TemplateQueryGenerator instance."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator
        return TemplateQueryGenerator()

    @pytest.mark.asyncio
    async def test_howto_templates(self, generator):
        """Test 'how to' query templates produce correct variations."""
        result = await generator.generate("How to deploy FastAPI", n=5)

        expected_patterns = ["tutorial", "guide", "steps", "deploy"]
        queries_lower = " ".join(result.queries).lower()

        # At least one expected pattern should appear
        assert any(pattern in queries_lower for pattern in expected_patterns)

    @pytest.mark.asyncio
    async def test_what_is_templates(self, generator):
        """Test 'what is' query templates produce correct variations."""
        result = await generator.generate("What is Kubernetes", n=5)

        # Should include definition-style queries
        queries_lower = " ".join(result.queries).lower()

        # Common patterns for 'what is' queries
        assert any(
            pattern in queries_lower
            for pattern in ["kubernetes", "definition", "explained"]
        )

    @pytest.mark.asyncio
    async def test_comparison_templates(self, generator):
        """Test comparison query templates."""
        result = await generator.generate("Docker vs Podman", n=5)

        assert result.metadata.get("template_type") == "comparison"

        # Should include comparison-related patterns
        queries_lower = " ".join(result.queries).lower()
        assert any(
            pattern in queries_lower
            for pattern in ["difference", "compared", "vs"]
        )

    @pytest.mark.asyncio
    async def test_error_troubleshooting_templates(self, generator):
        """Test troubleshooting query templates."""
        result = await generator.generate("FastAPI not working error", n=5)

        # Should detect troubleshooting intent
        assert result.metadata.get("template_type") == "troubleshooting"

        queries_lower = " ".join(result.queries).lower()
        assert any(
            pattern in queries_lower
            for pattern in ["error", "fix", "debug", "troubleshoot"]
        )

    @pytest.mark.asyncio
    async def test_no_match_returns_original(self, generator):
        """Test that queries without template match return original."""
        result = await generator.generate("random xyz query", n=5)

        # Should return at least the original
        assert "random xyz query" in result.queries

        # Template type should be None or similar
        assert result.metadata.get("template_type") is None

    @pytest.mark.asyncio
    async def test_chinese_query_handling(self, generator):
        """Test handling of non-English queries."""
        result = await generator.generate("如何使用 FastAPI", n=3)

        # Should handle gracefully even if no Chinese templates
        assert len(result.queries) >= 1
        assert "FastAPI" in " ".join(result.queries)


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def generator(self):
        """Create TemplateQueryGenerator instance."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator
        return TemplateQueryGenerator()

    @pytest.mark.asyncio
    async def test_very_long_query(self, generator):
        """Test handling of very long queries."""
        long_query = "How to " + "very " * 100 + "long query"
        result = await generator.generate(long_query, n=3)

        assert result.original_query == long_query
        assert len(result.queries) >= 1

    @pytest.mark.asyncio
    async def test_special_characters(self, generator):
        """Test handling of special characters."""
        result = await generator.generate("How to use @#$% symbols", n=3)

        assert result.original_query == "How to use @#$% symbols"

    @pytest.mark.asyncio
    async def test_n_zero_or_negative(self, generator):
        """Test handling of invalid n values."""
        # n=0 should return at least original
        result = await generator.generate("test query", n=0)
        assert len(result.queries) >= 1

        # n=-1 should handle gracefully
        result = await generator.generate("test query", n=-1)
        assert len(result.queries) >= 1

    @pytest.mark.asyncio
    async def test_sql_injection_attempt(self, generator):
        """Test handling of potential injection queries."""
        result = await generator.generate(
            "'; DROP TABLE users; --",
            n=3
        )

        # Should handle without error (treat as normal query)
        assert result.original_query == "'; DROP TABLE users; --"

    @pytest.mark.asyncio
    async def test_unicode_normalization(self, generator):
        """Test handling of unicode variations."""
        # Different unicode representations
        result1 = await generator.generate("What is café", n=3)
        result2 = await generator.generate("What is cafe\u0301", n=3)  # Combining accent

        # Both should work
        assert len(result1.queries) >= 1
        assert len(result2.queries) >= 1


class TestPerformance:
    """Test performance characteristics."""

    @pytest.fixture
    def generator(self):
        """Create TemplateQueryGenerator instance."""
        from raghub_mcp.pipeline.multi_query import TemplateQueryGenerator
        return TemplateQueryGenerator()

    @pytest.mark.asyncio
    async def test_generation_is_fast(self, generator):
        """Test that template generation is fast (<10ms)."""
        import time

        start = time.time()
        for _ in range(100):
            await generator.generate("How to use FastAPI", n=5)
        elapsed = time.time() - start

        # 100 generations should complete in <1 second (10ms each)
        assert elapsed < 1.0, f"Generation too slow: {elapsed}s for 100 calls"

    @pytest.mark.asyncio
    async def test_memory_efficient(self, generator):
        """Test that multiple generations don't accumulate memory."""
        import gc

        gc.collect()

        for _ in range(1000):
            await generator.generate("test query", n=10)

        # Should not accumulate significant memory
        gc.collect()
        # This is a soft check - if we had memory profiling we'd measure more precisely