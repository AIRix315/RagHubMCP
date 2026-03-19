"""Rerank provider abstract base class.

This module defines the interface for reranking providers that re-order
documents based on relevance to a query.
"""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from ..base import BaseProvider


@dataclass
class RerankResult:
    """Result from a reranking operation.
    
    Attributes:
        index: Original index of the document in the input list
        score: Relevance score, typically in range [0, 1]
        text: Original document text (optional, for convenience)
    """
    index: int
    score: float
    text: str = ""
    
    def __lt__(self, other: RerankResult) -> bool:
        """Enable sorting by score (descending order)."""
        return self.score > other.score


class BaseRerankProvider(BaseProvider):
    """Abstract base class for reranking providers.
    
    Reranking providers re-order a list of documents based on their
    relevance to a query. This is typically used after initial retrieval
    to improve the quality of top-k results.
    
    Subclasses must implement:
    - NAME: Class attribute for provider identification
    - rerank(): Re-rank documents by relevance
    - from_config(): Factory method to create instances from config
    
    The async method (arerank) has a default implementation that wraps
    the synchronous method using asyncio.to_thread.
    
    Example:
        class MyRerankProvider(BaseRerankProvider):
            NAME = "my-rerank"
            
            def rerank(
                self,
                query: str,
                documents: list[str],
                top_k: int = 5
            ) -> list[RerankResult]:
                scores = self._compute_scores(query, documents)
                indexed = list(enumerate(scores))
                indexed.sort(key=lambda x: x[1], reverse=True)
                return [
                    RerankResult(index=i, score=s, text=documents[i])
                    for i, s in indexed[:top_k]
                ]
            
            @classmethod
            def from_config(cls, config: dict) -> "MyRerankProvider":
                return cls(model=config["model"])
    """
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5
    ) -> list[RerankResult]:
        """Re-rank documents by relevance to query.
        
        Args:
            query: The search query
            documents: List of document texts to re-rank
            top_k: Number of top results to return
            
        Returns:
            List of RerankResult sorted by score (descending).
            Length is min(top_k, len(documents)).
            
        Note:
            Results should be sorted by score in descending order
            (highest relevance first).
        """
        ...
    
    # =========================================================================
    # Async methods with default implementations
    # =========================================================================
    
    async def arerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5
    ) -> list[RerankResult]:
        """Async version of rerank.
        
        Default implementation wraps the synchronous method using asyncio.to_thread.
        Subclasses can override for native async support.
        
        Args:
            query: The search query
            documents: List of document texts to re-rank
            top_k: Number of top results to return
            
        Returns:
            List of RerankResult sorted by score
        """
        return await asyncio.to_thread(self.rerank, query, documents, top_k)
    
    # =========================================================================
    # Convenience methods
    # =========================================================================
    
    def rerank_with_metadata(
        self,
        query: str,
        documents: list[dict[str, Any]],
        text_key: str = "text",
        top_k: int = 5
    ) -> list[dict[str, Any]]:
        """Re-rank documents that include metadata.
        
        This is a convenience method for documents stored as dictionaries.
        
        Args:
            query: The search query
            documents: List of document dictionaries
            text_key: Key to access document text in each dict
            top_k: Number of top results to return
            
        Returns:
            List of document dictionaries with added 'rerank_score' field,
            sorted by score descending.
        """
        texts = [doc.get(text_key, "") for doc in documents]
        results = self.rerank(query, texts, top_k)
        
        ranked_docs = []
        for result in results:
            doc = documents[result.index].copy()
            doc["rerank_score"] = result.score
            ranked_docs.append(doc)
        
        return ranked_docs
    
    @classmethod
    @abstractmethod
    def from_config(cls, config: dict[str, Any]) -> BaseRerankProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Typically includes: name, type, model
            
        Returns:
            New provider instance
        """
        ...