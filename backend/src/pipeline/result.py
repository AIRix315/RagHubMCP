"""RAG Pipeline result data structures.

This module defines the data classes for RAG pipeline results:
- Document: A single document with metadata and scores
- RAGResult: Complete result from a RAG pipeline execution

Reference:
- Docs/11-V2-Desing.md (Section 4.1)
- Docs/12-V2-Blueprint.md (Module 1)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    """A single document from RAG pipeline.

    Attributes:
        id: Unique document identifier.
        text: Document text content.
        score: Relevance score (higher = more relevant).
        metadata: Optional metadata dictionary.
        vector_score: Vector similarity score (if available).
        bm25_score: BM25 score (if available).
        rerank_score: Reranked score (if available).
    """

    id: str
    text: str
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    vector_score: float | None = None
    bm25_score: float | None = None
    rerank_score: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert document to dictionary.

        Returns:
            Dictionary representation of the document.
        """
        return {
            "id": self.id,
            "text": self.text,
            "score": self.score,
            "metadata": self.metadata,
            "vector_score": self.vector_score,
            "bm25_score": self.bm25_score,
            "rerank_score": self.rerank_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Create document from dictionary.

        Args:
            data: Dictionary with document data.

        Returns:
            Document instance.
        """
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            score=data.get("score", 0.0),
            metadata=data.get("metadata", {}),
            vector_score=data.get("vector_score"),
            bm25_score=data.get("bm25_score"),
            rerank_score=data.get("rerank_score"),
        )


@dataclass
class RAGResult:
    """Result from RAG pipeline execution.

    Attributes:
        query: Original query string.
        documents: List of retrieved documents.
        total_results: Total number of matching documents.
        execution_time_ms: Execution time in milliseconds (optional).
        profile: Profile used for execution (optional).
        metadata: Additional result metadata (optional).
    """

    query: str
    documents: list[Document] = field(default_factory=list)
    total_results: int = 0
    execution_time_ms: float | None = None
    profile: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary.

        Returns:
            Dictionary representation of the result.
        """
        return {
            "query": self.query,
            "documents": [doc.to_dict() for doc in self.documents],
            "total_results": self.total_results,
            "execution_time_ms": self.execution_time_ms,
            "profile": self.profile,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RAGResult:
        """Create result from dictionary.

        Args:
            data: Dictionary with result data.

        Returns:
            RAGResult instance.
        """
        documents = [
            Document.from_dict(doc) if isinstance(doc, dict) else doc
            for doc in data.get("documents", [])
        ]
        return cls(
            query=data.get("query", ""),
            documents=documents,
            total_results=data.get("total_results", len(documents)),
            execution_time_ms=data.get("execution_time_ms"),
            profile=data.get("profile"),
            metadata=data.get("metadata", {}),
        )

    def __len__(self) -> int:
        """Return number of documents."""
        return len(self.documents)

    def __iter__(self):
        """Iterate over documents."""
        return iter(self.documents)

    def __getitem__(self, index: int) -> Document:
        """Get document by index."""
        return self.documents[index]
