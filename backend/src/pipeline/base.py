"""RAG Pipeline abstract base class.

This module defines the RAGPipeline abstract base class that all
pipeline implementations must inherit from.

Reference:
- Docs/11-V2-Desing.md (Section 4.1)
- Docs/12-V2-Blueprint.md (Module 1.1)
- RULE.md (RULE-1: Pipeline是唯一执行入口)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .result import RAGResult


class RAGPipeline(ABC):
    """Abstract base class for RAG pipelines.
    
    All RAG pipeline implementations must inherit from this class and
    implement the run() method. The pipeline is the single entry point
    for all RAG operations.
    
    Design Principles (from RULE.md):
    - RULE-1: Pipeline is the only execution entry point
    - RULE-2: All modules must be interface-based (ABC)
    - RULE-3: No direct dependencies on concrete implementations
    
    Execution Flow:
        1. Query Normalize (optional)
        2. Retrieval (Hybrid)
        3. Rerank (required for quality)
        4. Context Builder (quality optimization)
        5. Return contexts
    
    Example:
        >>> class MyPipeline(RAGPipeline):
        ...     async def run(self, query: str, options: dict) -> RAGResult:
        ...         # Implementation
        ...         return RAGResult(query=query, documents=[], total_results=0)
    """
    
    @abstractmethod
    async def run(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> RAGResult:
        """Execute the RAG pipeline.
        
        This is the main entry point for all RAG operations. All RAG
        flows must go through this method.
        
        Args:
            query: The search query string.
            options: Optional configuration options:
                - topK: Number of results to return (default: 5)
                - rerank: Whether to apply reranking (default: True)
                - profile: Profile name (fast/balanced/accurate)
                - collection: Collection name to query
                - where: Metadata filter
                
        Returns:
            RAGResult containing the retrieved documents and metadata.
            
        Raises:
            ValueError: If query is invalid or collection not found.
            RuntimeError: If pipeline execution fails.
        """
        pass
    
    @property
    def name(self) -> str:
        """Get pipeline name.
        
        Returns:
            Pipeline name identifier.
        """
        return self.__class__.__name__
    
    def __repr__(self) -> str:
        """String representation of pipeline."""
        return f"{self.__class__.__name__}()"