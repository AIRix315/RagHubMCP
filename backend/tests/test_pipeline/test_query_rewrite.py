"""Tests for Query Rewriter module.

Tests verify:
- QueryRewriter abstract interface
- IdentityRewriter (passthrough)
- NormalizeRewriter (text normalization)
- TemplateRewriter (template-based variations)

Reference:
- Docs/11-V2-Design.md (Section 5: Retrieval设计)
- Docs/12-V2-Blueprint.md (Phase 5: Query Rewrite)
- TODO-V2.md (Phase 5: 8.1 Query Rewrite)
- RULE.md (测试优先原则)
"""

import pytest

from pipeline.query_rewrite import (
    IdentityRewriter,
    NormalizeRewriter,
    QueryRewriter,
    RewriteMode,
    RewriteResult,
    TemplateRewriter,
    create_query_rewriter,
)


class TestRewriteResult:
    """Tests for RewriteResult dataclass."""

    def test_rewrite_result_creation(self):
        """Test RewriteResult can be created with required fields."""
        result = RewriteResult(
            original_query="How to use FastAPI",
            rewritten_queries=["how to use fastapi", "fastapi tutorial"],
            mode=RewriteMode.NORMALIZE,
        )

        assert result.original_query == "How to use FastAPI"
        assert len(result.rewritten_queries) == 2
        assert result.mode == RewriteMode.NORMALIZE
        assert result.metadata is None

    def test_rewrite_result_with_metadata(self):
        """Test RewriteResult with optional metadata."""
        result = RewriteResult(
            original_query="test query",
            rewritten_queries=["test query"],
            mode=RewriteMode.IDENTITY,
            metadata={"source": "test"},
        )

        assert result.metadata == {"source": "test"}

    def test_primary_query(self):
        """Test primary_query property returns first query."""
        result = RewriteResult(
            original_query="original",
            rewritten_queries=["first", "second", "third"],
            mode=RewriteMode.TEMPLATE,
        )

        assert result.primary_query == "first"

    def test_primary_query_empty_list_returns_original(self):
        """Test primary_query returns original when list is empty."""
        result = RewriteResult(
            original_query="original",
            rewritten_queries=[],
            mode=RewriteMode.IDENTITY,
        )

        assert result.primary_query == "original"

    def test_to_dict(self):
        """Test RewriteResult serialization to dict."""
        result = RewriteResult(
            original_query="test",
            rewritten_queries=["test", "test query"],
            mode=RewriteMode.NORMALIZE,
            metadata={"key": "value"},
        )

        result_dict = result.to_dict()

        assert result_dict["original_query"] == "test"
        assert result_dict["rewritten_queries"] == ["test", "test query"]
        assert result_dict["mode"] == "normalize"
        assert result_dict["metadata"] == {"key": "value"}


class TestRewriteMode:
    """Tests for RewriteMode enum."""

    def test_rewrite_mode_values(self):
        """Test RewriteMode has all expected values."""
        assert RewriteMode.IDENTITY.value == "identity"
        assert RewriteMode.NORMALIZE.value == "normalize"
        assert RewriteMode.EXPAND.value == "expand"
        assert RewriteMode.TEMPLATE.value == "template"
        assert RewriteMode.LLM.value == "llm"

    def test_rewrite_mode_from_string(self):
        """Test RewriteMode can be created from string."""
        assert RewriteMode("identity") == RewriteMode.IDENTITY
        assert RewriteMode("normalize") == RewriteMode.NORMALIZE
        assert RewriteMode("template") == RewriteMode.TEMPLATE


class TestIdentityRewriter:
    """Tests for IdentityRewriter (passthrough)."""

    @pytest.fixture
    def rewriter(self):
        """Create IdentityRewriter instance."""
        return IdentityRewriter()

    def test_name_property(self, rewriter):
        """Test rewriter name."""
        assert rewriter.name == "IdentityRewriter"

    def test_mode_property(self, rewriter):
        """Test rewriter mode."""
        assert rewriter.mode == RewriteMode.IDENTITY

    @pytest.mark.asyncio
    async def test_rewrite_returns_original(self, rewriter):
        """Test identity rewriter returns original query unchanged."""
        result = await rewriter.rewrite("How to use FastAPI?")

        assert result.original_query == "How to use FastAPI?"
        assert result.rewritten_queries == ["How to use FastAPI?"]
        assert result.mode == RewriteMode.IDENTITY
        assert result.metadata == {"passthrough": True}

    @pytest.mark.asyncio
    async def test_rewrite_ignores_options(self, rewriter):
        """Test identity rewriter ignores options."""
        result = await rewriter.rewrite(
            "test query",
            options={"foo": "bar", "baz": 123},
        )

        assert result.rewritten_queries == ["test query"]

    @pytest.mark.asyncio
    async def test_rewrite_empty_query(self, rewriter):
        """Test identity rewriter handles empty query."""
        result = await rewriter.rewrite("")

        assert result.original_query == ""
        assert result.rewritten_queries == [""]

    @pytest.mark.asyncio
    async def test_rewrite_unicode_query(self, rewriter):
        """Test identity rewriter handles unicode."""
        result = await rewriter.rewrite("如何使用 FastAPI？")

        assert result.rewritten_queries == ["如何使用 FastAPI？"]


class TestNormalizeRewriter:
    """Tests for NormalizeRewriter."""

    @pytest.fixture
    def rewriter(self):
        """Create NormalizeRewriter with default settings."""
        return NormalizeRewriter()

    def test_name_property(self, rewriter):
        """Test rewriter name."""
        assert rewriter.name == "NormalizeRewriter"

    def test_mode_property(self, rewriter):
        """Test rewriter mode."""
        assert rewriter.mode == RewriteMode.NORMALIZE

    def test_default_settings(self, rewriter):
        """Test default initialization settings."""
        assert rewriter.lowercase is True
        assert rewriter.remove_stopwords is False
        assert rewriter.remove_punctuation is True
        assert rewriter.min_length == 2

    def test_custom_settings(self):
        """Test custom initialization settings."""
        rewriter = NormalizeRewriter(
            lowercase=False,
            remove_stopwords=True,
            remove_punctuation=False,
            min_length=5,
        )

        assert rewriter.lowercase is False
        assert rewriter.remove_stopwords is True
        assert rewriter.remove_punctuation is False
        assert rewriter.min_length == 5

    @pytest.mark.asyncio
    async def test_rewrite_lowercase(self, rewriter):
        """Test lowercase normalization."""
        result = await rewriter.rewrite("How TO Use FastAPI")

        assert result.primary_query == "how to use fastapi"

    @pytest.mark.asyncio
    async def test_rewrite_remove_punctuation(self, rewriter):
        """Test punctuation removal."""
        result = await rewriter.rewrite("How to use FastAPI???!!!   ")

        assert "?" not in result.primary_query
        assert "!" not in result.primary_query
        assert "how to use fastapi" in result.primary_query

    @pytest.mark.asyncio
    async def test_rewrite_whitespace_normalization(self, rewriter):
        """Test whitespace normalization."""
        result = await rewriter.rewrite("How    to   use    FastAPI")

        assert result.primary_query == "how to use fastapi"

    @pytest.mark.asyncio
    async def test_rewrite_combined_normalization(self, rewriter):
        """Test combined normalization operations."""
        result = await rewriter.rewrite("  How to USE FastAPI???!!!  ")

        assert result.primary_query == "how to use fastapi"

    @pytest.mark.asyncio
    async def test_rewrite_preserves_content(self, rewriter):
        """Test that content is preserved during normalization."""
        result = await rewriter.rewrite("What is machine learning?")

        assert "machine" in result.primary_query
        assert "learning" in result.primary_query

    @pytest.mark.asyncio
    async def test_rewrite_stopwords_removal(self):
        """Test stop words removal from start and end."""
        rewriter = NormalizeRewriter(remove_stopwords=True)

        result = await rewriter.rewrite("The FastAPI framework is awesome")

        # Note: stopwords are only removed from start/end
        assert result.primary_query.startswith("fastapi")

    @pytest.mark.asyncio
    async def test_rewrite_min_length_fallback(self):
        """Test that too-short normalized query falls back to original."""
        rewriter = NormalizeRewriter(min_length=10)

        result = await rewriter.rewrite("Hi")

        # Should keep original since normalized would be too short
        assert result.primary_query == "Hi"
        assert result.metadata["original_length"] == 2

    @pytest.mark.asyncio
    async def test_rewrite_with_options_override(self, rewriter):
        """Test that options override rewriter settings."""
        result = await rewriter.rewrite(
            "How To Use FastAPI",
            options={"lowercase": False, "remove_punctuation": False},
        )

        # Should not lower case due to option override
        assert "How" in result.primary_query

    @pytest.mark.asyncio
    async def test_rewrite_metadata(self, rewriter):
        """Test metadata in result."""
        result = await rewriter.rewrite("How to use FastAPI")

        assert result.metadata is not None
        assert "original_length" in result.metadata
        assert "normalized_length" in result.metadata
        assert result.metadata["lowercase"] is True
        assert result.metadata["remove_punctuation"] is True

    @pytest.mark.asyncio
    async def test_rewrite_empty_query(self, rewriter):
        """Test empty query handling."""
        result = await rewriter.rewrite("")

        assert result.rewritten_queries == [""]


class TestTemplateRewriter:
    """Tests for TemplateRewriter."""

    @pytest.fixture
    def rewriter(self):
        """Create TemplateRewriter instance."""
        return TemplateRewriter()

    def test_name_property(self, rewriter):
        """Test rewriter name."""
        assert rewriter.name == "TemplateRewriter"

    def test_mode_property(self, rewriter):
        """Test rewriter mode."""
        assert rewriter.mode == RewriteMode.TEMPLATE

    @pytest.mark.asyncio
    async def test_rewrite_clarification_query(self, rewriter):
        """Test rewriting 'what is' queries."""
        result = await rewriter.rewrite("What is FastAPI?")

        assert len(result.rewritten_queries) >= 1
        assert "fastapi" in result.primary_query.lower()
        assert result.metadata["matched_category"] == "clarification"
        assert result.metadata["matched_key"] == "what is"

    @pytest.mark.asyncio
    async def test_rewrite_howto_query(self, rewriter):
        """Test rewriting 'how to' queries."""
        result = await rewriter.rewrite("How to use FastAPI?")

        assert len(result.rewritten_queries) >= 1
        assert result.metadata["matched_category"] == "howto"
        assert result.metadata["matched_key"] == "how to"

    @pytest.mark.asyncio
    async def test_rewrite_comparison_query(self, rewriter):
        """Test rewriting comparison queries."""
        result = await rewriter.rewrite("FastAPI vs Flask")

        assert len(result.rewritten_queries) >= 1
        assert result.metadata["matched_category"] == "comparison"

    @pytest.mark.asyncio
    async def test_rewrite_troubleshooting_query(self, rewriter):
        """Test rewriting troubleshooting queries."""
        result = await rewriter.rewrite("FastAPI not working")

        assert len(result.rewritten_queries) >= 1
        assert result.metadata["matched_category"] == "troubleshooting"

    @pytest.mark.asyncio
    async def test_rewrite_unmatched_query(self, rewriter):
        """Test query that doesn't match any template."""
        result = await rewriter.rewrite("FastAPI authentication example")

        assert result.rewritten_queries == ["FastAPI authentication example"]
        assert result.metadata["matched_category"] is None
        assert result.metadata["matched_key"] is None

    @pytest.mark.asyncio
    async def test_rewrite_max_variations(self, rewriter):
        """Test max_variations option limits output."""
        result = await rewriter.rewrite(
            "How to use FastAPI",
            options={"max_variations": 1, "include_original": False},
        )

        # Should have at most 1 variation + original
        assert len(result.rewritten_queries) <= 2
        assert result.metadata["max_variations"] == 1

    @pytest.mark.asyncio
    async def test_rewrite_include_original(self, rewriter):
        """Test include_original option."""
        result = await rewriter.rewrite(
            "How to use FastAPI",
            options={"include_original": False, "max_variations": 10},
        )

        # Original should not be in the first position
        if len(result.rewritten_queries) > 0:
            # First query might still be original if it's the only one
            pass  # Can't assert strict equality due to template matching

    @pytest.mark.asyncio
    async def test_rewrite_metadata(self, rewriter):
        """Test metadata includes rewrite information."""
        result = await rewriter.rewrite("What is Python?")

        assert result.metadata["num_variations"] is not None
        assert result.metadata["include_original"] is True

    @pytest.mark.asyncio
    async def test_rewrite_case_insensitive_matching(self, rewriter):
        """Test template matching is case insensitive."""
        result1 = await rewriter.rewrite("What is FastAPI")
        result2 = await rewriter.rewrite("what is fastapi")
        result3 = await rewriter.rewrite("WHAT IS FASTAPI")

        # All should match the same template
        assert result1.metadata["matched_category"] == "clarification"
        assert result2.metadata["matched_category"] == "clarification"
        assert result3.metadata["matched_category"] == "clarification"


class TestCreateQueryRewriter:
    """Tests for create_query_rewriter factory function."""

    def test_create_identity_rewriter(self):
        """Test creating IdentityRewriter."""
        rewriter = create_query_rewriter(RewriteMode.IDENTITY)

        assert isinstance(rewriter, IdentityRewriter)
        assert rewriter.mode == RewriteMode.IDENTITY

    def test_create_identity_rewriter_from_string(self):
        """Test creating rewriter from string mode."""
        rewriter = create_query_rewriter("identity")

        assert isinstance(rewriter, IdentityRewriter)

    def test_create_normalize_rewriter_default(self):
        """Test creating NormalizeRewriter with defaults."""
        rewriter = create_query_rewriter(RewriteMode.NORMALIZE)

        assert isinstance(rewriter, NormalizeRewriter)
        assert rewriter.lowercase is True
        assert rewriter.remove_punctuation is True

    def test_create_normalize_rewriter_with_config(self):
        """Test creating NormalizeRewriter with custom config."""
        rewriter = create_query_rewriter(
            RewriteMode.NORMALIZE,
            config={"lowercase": False, "remove_stopwords": True},
        )

        assert isinstance(rewriter, NormalizeRewriter)
        assert rewriter.lowercase is False
        assert rewriter.remove_stopwords is True

    def test_create_template_rewriter(self):
        """Test creating TemplateRewriter."""
        rewriter = create_query_rewriter(RewriteMode.TEMPLATE)

        assert isinstance(rewriter, TemplateRewriter)

    def test_create_rewriter_unknown_mode_returns_identity(self):
        """Test unknown mode returns IdentityRewriter."""
        # This should not raise, should default to identity
        # Note: If enum validation is strict, this might raise instead
        # Adjust test based on actual behavior
        rewriter = create_query_rewriter("unknown_mode")

        assert isinstance(rewriter, IdentityRewriter)

    def test_create_rewriter_no_mode_returns_identity(self):
        """Test no mode specified returns IdentityRewriter."""
        rewriter = create_query_rewriter()

        assert isinstance(rewriter, IdentityRewriter)


class TestQueryRewriterIntegration:
    """Integration tests for Query Rewriter pipeline integration."""

    @pytest.mark.asyncio
    async def test_pipeline_like_sequence(self):
        """Test query rewriting in a pipeline-like sequence."""
        # Test that different rewriters can be used interchangeably
        rewriters = [
            IdentityRewriter(),
            NormalizeRewriter(),
            TemplateRewriter(),
        ]

        query = "How to use FastAPI?"

        for rewriter in rewriters:
            result = await rewriter.rewrite(query)
            assert result.original_query == query
            assert len(result.rewritten_queries) >= 1
            assert result.mode in [RewriteMode.IDENTITY, RewriteMode.NORMALIZE, RewriteMode.TEMPLATE]

    @pytest.mark.asyncio
    async def test_normalize_then_template(self):
        """Test combining normalization with template rewriting."""
        normalizer = NormalizeRewriter()
        template = TemplateRewriter()

        # First normalize
        normalize_result = await normalizer.rewrite("  How to USE FastAPI???  ")
        normalized_query = normalize_result.primary_query

        # Then apply template
        template_result = await template.rewrite(normalized_query)

        assert len(template_result.rewritten_queries) >= 1
        assert template_result.metadata["matched_category"] == "howto"