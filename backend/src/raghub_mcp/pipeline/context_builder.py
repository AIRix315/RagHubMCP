"""Context Builder interface for RAG Pipeline.

This module defines the ContextBuilder abstract base class for
constructing the final context from retrieved documents.

Reference:
- Docs/11-V2-Desing.md (Section 7)
- Docs/12-V2-Blueprint.md (Module 4)
- RULE.md (RULE-2: 所有模块必须接口化)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .result import Document


class ContextBuilder(ABC):
    """Abstract base class for context builders.

    All context builder implementations must inherit from this class and
    implement the build() method.

    Context builders are responsible for:
    - Removing duplicate/similar documents
    - Sorting by relevance
    - Truncating to fit context limits
    - Merging consecutive content

    Example:
        >>> class MyContextBuilder(ContextBuilder):
        ...     def build(self, docs: list[Document], limit: int) -> list[Document]:
        ...         # Implementation
        ...         return docs[:limit]
    """

    @abstractmethod
    def build(
        self,
        documents: list[Document],
        limit: int,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Build final context from documents.

        Args:
            documents: List of documents to build context from.
            limit: Maximum number of documents to include.
            options: Optional builder options:
                - remove_duplicates: Whether to remove duplicates
                - merge_consecutive: Whether to merge consecutive content

        Returns:
            List of Document objects as the final context.
        """
        pass

    @property
    def name(self) -> str:
        """Get builder name."""
        return self.__class__.__name__


class DefaultContextBuilder(ContextBuilder):
    """Default context builder implementation.

    This builder provides basic context construction:
    - Deduplication (by content hash)
    - Sorting by score
    - Truncation to topK
    """

    def __init__(self) -> None:
        """Initialize default context builder."""
        pass

    def build(
        self,
        documents: list[Document],
        limit: int,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Build context with deduplication and sorting.

        Args:
            documents: List of documents.
            limit: Maximum number of documents.
            options: Optional builder options:
                - remove_duplicates: Remove duplicate content (default: True)
                - merge_consecutive: Merge consecutive content from same source (default: False)

        Returns:
            Deduplicated, sorted, and truncated documents.
        """
        options = options or {}
        remove_duplicates = options.get("remove_duplicates", True)
        merge_consecutive = options.get("merge_consecutive", False)

        if not documents:
            return []

        # Merge consecutive content first
        if merge_consecutive:
            documents = self._merge_consecutive(documents)

        # Deduplicate if requested
        if remove_duplicates:
            documents = self._deduplicate(documents)

        # Sort by score (descending)
        sorted_docs = sorted(
            documents,
            key=lambda d: d.score,
            reverse=True,
        )

        # Truncate to limit
        return sorted_docs[:limit]

    def _deduplicate(self, documents: list[Document]) -> list[Document]:
        """Remove duplicate documents by content hash.

        Args:
            documents: List of documents.

        Returns:
            Deduplicated list (first occurrence kept).
        """
        seen: dict[int, Document] = {}

        for doc in documents:
            # Create hash from text content
            content_hash = hash(doc.text)

            if content_hash not in seen:
                seen[content_hash] = doc

        return list(seen.values())

    def _merge_consecutive(self, documents: list[Document]) -> list[Document]:
        """Merge consecutive documents from the same source.

        Documents are considered consecutive if they have the same source
        and their positions indicate they were originally split.

        Args:
            documents: List of documents (should be in original order).

        Returns:
            List with consecutive documents merged.
        """
        if not documents:
            return []

        merged: list[Document] = []
        current_group: list[Document] = []
        current_source: str | None = None

        for doc in documents:
            source = doc.metadata.get("source") if doc.metadata else None

            if current_source == source:
                # Same source, add to current group
                current_group.append(doc)
            else:
                # Different source, flush current group if exists
                if current_group:
                    merged.append(self._merge_group(current_group))
                current_group = [doc]
                current_source = source

        # Flush final group
        if current_group:
            merged.append(self._merge_group(current_group))

        return merged

    def _merge_group(self, documents: list[Document]) -> Document:
        """Merge a group of documents into a single document.

        Args:
            documents: List of documents to merge (same source).

        Returns:
            A single merged document.
        """
        if len(documents) == 1:
            return documents[0]

        # Merge text content (preserve order)
        merged_text = "\n".join(doc.text for doc in documents)

        # Use metadata from first document
        merged_metadata = dict(documents[0].metadata) if documents[0].metadata else {}

        # Update start/end if available
        if documents[0].metadata and "start" in documents[0].metadata:
            start = documents[0].metadata.get("start", 0)
        else:
            start = 0

        if documents[-1].metadata and "end" in documents[-1].metadata:
            end = documents[-1].metadata.get("end", 0)
        else:
            end = 0

        merged_metadata["start"] = start
        merged_metadata["end"] = end
        merged_metadata["chunks_merged"] = len(documents)

        return Document(
            id=documents[0].id,
            text=merged_text,
            score=documents[0].score,  # Use highest score
            metadata=merged_metadata,
            vector_score=documents[0].vector_score,
            bm25_score=documents[0].bm25_score,
            rerank_score=documents[0].rerank_score,
        )


class MultiQueryContextBuilder(ContextBuilder):
    """Context builder that handles multi-query results.

    This builder is used when multiple queries are generated from
    the original query (for better recall).
    """

    def __init__(
        self,
        inner_builder: ContextBuilder | None = None,
    ) -> None:
        """Initialize multi-query context builder.

        Args:
            inner_builder: Inner builder to use for final construction.
        """
        self._inner = inner_builder or DefaultContextBuilder()

    def build(
        self,
        documents: list[Document],
        limit: int,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Build context from multi-query results.

        Groups documents by source query and removes near-duplicates
        before passing to the inner builder.

        Args:
            documents: List of documents from multiple queries.
            limit: Maximum number of documents.
            options: Optional builder options.

        Returns:
            Final context documents.
        """
        # Group by document ID (deduplicate across queries)
        unique_docs: dict[str, Document] = {}

        for doc in documents:
            if doc.id not in unique_docs:
                unique_docs[doc.id] = doc
            else:
                # Keep the one with higher score
                if doc.score > unique_docs[doc.id].score:
                    unique_docs[doc.id] = doc

        # Use inner builder for final construction
        deduped = list(unique_docs.values())
        return self._inner.build(deduped, limit, options)
