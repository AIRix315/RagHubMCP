"""Tests for ChunkerRegistry.

Test cases:
- TC-1.9.5: Registry 选择正确 chunker
- TC-1.9.6: 未知语言使用默认 chunker
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestChunkerRegistry:
    """Tests for ChunkerRegistry singleton and registration."""

    def test_registry_is_singleton(self):
        """Registry is a singleton."""
        from chunkers.registry import registry
        from chunkers.registry import registry as registry2

        assert registry is registry2

    def test_builtin_chunkers_registered(self):
        """Built-in chunkers are auto-registered."""
        from chunkers.registry import registry

        assert registry.is_registered("simple")
        assert registry.is_registered("line")
        assert registry.is_registered("markdown")

    def test_get_chunker_by_name(self):
        """Can retrieve chunker by name."""
        from chunkers.registry import registry
        from chunkers.simple import SimpleChunker

        chunker_cls = registry.get("simple")
        assert chunker_cls is SimpleChunker

    def test_get_unregistered_chunker_fails(self):
        """Getting unregistered chunker raises KeyError."""
        from chunkers.registry import registry

        with pytest.raises(KeyError) as exc_info:
            registry.get("nonexistent-chunker")

        assert "not registered" in str(exc_info.value)

    def test_register_custom_chunker(self):
        """Can register custom chunker."""
        from chunkers.base import ChunkerPlugin
        from chunkers.registry import registry

        # Save original state
        original_chunkers = registry._chunkers.copy()
        original_lang_map = registry._language_map.copy()
        registry.clear()

        try:

            @registry.register("custom-test")
            class CustomChunker(ChunkerPlugin):
                NAME = "custom-test"

                def chunk(self, text):
                    return []

            assert registry.is_registered("custom-test")
            assert registry.get("custom-test") is CustomChunker
        finally:
            # Restore original registrations
            registry._chunkers = original_chunkers
            registry._language_map = original_lang_map

    def test_register_duplicate_fails(self):
        """Cannot register duplicate chunker name."""
        from chunkers.base import ChunkerPlugin
        from chunkers.registry import registry

        # Create a unique test name first
        test_name = "test-duplicate-check-unique"

        # Register it once
        @registry.register(test_name)
        class TestDupChunker(ChunkerPlugin):
            NAME = test_name

            def chunk(self, text):
                return []

        # Try to register again with same name should fail
        with pytest.raises(ValueError) as exc_info:

            @registry.register(test_name)
            class TestDupChunker2(ChunkerPlugin):
                NAME = test_name

                def chunk(self, text):
                    return []

        assert "already registered" in str(exc_info.value)


class TestRegistryLanguageSelection:
    """TC-1.9.5 和 TC-1.9.6: Registry 语言选择"""

    def test_get_for_markdown_language(self):
        """TC-1.9.5: Registry returns MarkdownChunker for markdown."""
        from chunkers.markdown import MarkdownChunker
        from chunkers.registry import registry

        chunker_cls = registry.get_for_language("markdown")
        assert chunker_cls is MarkdownChunker

    def test_get_for_md_language(self):
        """TC-1.9.5: Registry returns MarkdownChunker for md."""
        from chunkers.markdown import MarkdownChunker
        from chunkers.registry import registry

        chunker_cls = registry.get_for_language("md")
        assert chunker_cls is MarkdownChunker

    def test_get_for_unknown_language(self):
        """TC-1.9.6: Unknown language falls back to SimpleChunker."""
        from chunkers.registry import registry
        from chunkers.simple import SimpleChunker

        chunker_cls = registry.get_for_language("unknown-language-xyz")
        assert chunker_cls is SimpleChunker

    def test_get_for_python_language(self):
        """TC-1.9.6: Python uses PythonASTChunker when tree-sitter is available."""
        from chunkers.registry import registry

        # Python has a special AST chunker registered
        chunker_cls = registry.get_for_language("python")

        # Check if tree-sitter is available
        try:
            import tree_sitter_python

            from chunkers.python_ast import PythonASTChunker

            assert chunker_cls is PythonASTChunker
        except ImportError:
            # Fallback to SimpleChunker if tree-sitter not available
            from chunkers.simple import SimpleChunker

            assert chunker_cls is SimpleChunker

    def test_language_case_insensitive(self):
        """Language matching is case-insensitive."""
        from chunkers.markdown import MarkdownChunker
        from chunkers.registry import registry

        chunker_cls = registry.get_for_language("MARKDOWN")
        assert chunker_cls is MarkdownChunker

        chunker_cls = registry.get_for_language("Markdown")
        assert chunker_cls is MarkdownChunker


class TestRegistryListAndCheck:
    """Tests for registry listing and checking methods."""

    def test_list_chunkers(self):
        """Can list all registered chunkers."""
        from chunkers.registry import registry

        chunkers = registry.list_chunkers()

        assert "simple" in chunkers
        assert "line" in chunkers
        assert "markdown" in chunkers

    def test_is_registered_true(self):
        """is_registered returns True for registered chunkers."""
        from chunkers.registry import registry

        assert registry.is_registered("simple") is True
        assert registry.is_registered("line") is True
        assert registry.is_registered("markdown") is True

    def test_is_registered_false(self):
        """is_registered returns False for unregistered chunkers."""
        from chunkers.registry import registry

        assert registry.is_registered("nonexistent") is False

    def test_clear_removes_registrations(self):
        """clear() removes all registrations."""
        from chunkers.registry import registry

        # Save original state
        original_chunkers = registry._chunkers.copy()
        original_lang_map = registry._language_map.copy()

        try:
            registry.clear()

            assert registry.list_chunkers() == []
            assert not registry.is_registered("simple")
        finally:
            # Restore original state
            registry._chunkers = original_chunkers
            registry._language_map = original_lang_map
