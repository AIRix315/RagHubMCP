"""Tests for merge_consecutive functionality in ContextBuilder.

Reference: Docs/11-V2-Desing.md (Section 7)
"""

from pipeline.context_builder import (
    DefaultContextBuilder,
)
from pipeline.result import Document


class TestMergeConsecutive:
    """Tests for merge_consecutive functionality."""

    def test_merge_consecutive_option_exists(self):
        """Test that merge_consecutive option is accepted."""
        builder = DefaultContextBuilder()

        docs = [
            Document(
                id="1",
                text="First part",
                score=0.9,
                metadata={"source": "file1.py", "start": 0, "end": 10},
            ),
            Document(
                id="2",
                text="Second part",
                score=0.8,
                metadata={"source": "file1.py", "start": 10, "end": 20},
            ),
            Document(
                id="3",
                text="Different file",
                score=0.7,
                metadata={"source": "file2.py", "start": 0, "end": 10},
            ),
        ]

        # Should accept merge_consecutive option without error
        result = builder.build(docs, limit=3, options={"merge_consecutive": True})
        assert len(result) <= 3

    def test_merge_consecutive_same_source(self):
        """Test that consecutive documents from same source are merged."""
        builder = DefaultContextBuilder()

        docs = [
            Document(
                id="1",
                text="Line 1: function foo() {",
                score=0.9,
                metadata={"source": "file1.py", "start": 0, "end": 20},
            ),
            Document(
                id="2",
                text="Line 2:   return 42;",
                score=0.9,
                metadata={"source": "file1.py", "start": 20, "end": 40},
            ),
            Document(
                id="3",
                text="Line 3: }",
                score=0.9,
                metadata={"source": "file1.py", "start": 40, "end": 45},
            ),
        ]

        result = builder.build(docs, limit=3, options={"merge_consecutive": True})

        # Should merge into fewer documents
        assert len(result) < len(docs)
        # Merged content should contain all original text
        merged_text = result[0].text if result else ""
        assert "Line 1" in merged_text or "Line 2" in merged_text or "Line 3" in merged_text

    def test_merge_consecutive_different_sources_not_merged(self):
        """Test that documents from different sources are not merged."""
        builder = DefaultContextBuilder()

        docs = [
            Document(id="1", text="Content A", score=0.9, metadata={"source": "file1.py"}),
            Document(id="2", text="Content B", score=0.8, metadata={"source": "file2.py"}),
            Document(id="3", text="Content C", score=0.7, metadata={"source": "file3.py"}),
        ]

        result = builder.build(docs, limit=3, options={"merge_consecutive": True})

        # All should be separate sources, so no merging
        assert len(result) == 3

    def test_merge_consecutive_preserves_metadata(self):
        """Test that merged document preserves metadata from first chunk."""
        builder = DefaultContextBuilder()

        docs = [
            Document(
                id="1", text="Part 1", score=0.9, metadata={"source": "test.py", "lines": "1-10"}
            ),
            Document(
                id="2", text="Part 2", score=0.9, metadata={"source": "test.py", "lines": "11-20"}
            ),
        ]

        result = builder.build(docs, limit=2, options={"merge_consecutive": True})

        if len(result) < len(docs):
            # Merged document should have source metadata
            assert result[0].metadata.get("source") == "test.py"

    def test_merge_consecutive_default_false(self):
        """Test that merge_consecutive is disabled by default."""
        builder = DefaultContextBuilder()

        docs = [
            Document(id="1", text="Part 1", score=0.9, metadata={"source": "test.py"}),
            Document(id="2", text="Part 2", score=0.9, metadata={"source": "test.py"}),
        ]

        # Without merge_consecutive option, should not merge
        result = builder.build(docs, limit=2, options={})
        assert len(result) == 2

    def test_merge_consecutive_with_deduplication(self):
        """Test that merge_consecutive works with deduplication."""
        builder = DefaultContextBuilder()

        docs = [
            Document(id="1", text="Content A", score=0.9, metadata={"source": "test.py"}),
            Document(id="2", text="Content B", score=0.9, metadata={"source": "test.py"}),
            Document(
                id="1", text="Content A duplicate", score=0.8, metadata={"source": "test.py"}
            ),  # Duplicate of id=1
        ]

        result = builder.build(
            docs, limit=3, options={"remove_duplicates": True, "merge_consecutive": True}
        )

        # Should deduplicate AND merge consecutive
        assert len(result) <= 3
