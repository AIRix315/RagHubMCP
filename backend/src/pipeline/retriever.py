"""Retriever interface for RAG Pipeline.

This module defines the Retriever abstract base class for document
retrieval in the RAG pipeline.

Reference:
- Docs/11-V2-Desing.md (Section 5)
- Docs/12-V2-Blueprint.md (Module 1)
- RULE.md (RULE-2: 所有模块必须接口化)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .result import Document


class Retriever(ABC):
    """Abstract base class for document retrievers.
    
    All retriever implementations must inherit from this class and
    implement the retrieve() method.
    
    Supported retrieval methods:
    - Vector Search: Semantic similarity search
    - BM25: Lexical matching search
    - Hybrid: Combination of vector and BM25 (RRF)
    
    Example:
        >>> class MyRetriever(Retriever):
        ...     async def retrieve(self, query: str, options: dict) -> list[Document]:
        ...         # Implementation
        ...         return [Document(id="1", text="doc", score=0.9)]
    """
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Retrieve documents for a query.
        
        Args:
            query: The search query string.
            options: Optional retrieval options:
                - collection: Collection name to query
                - topK: Number of results to retrieve
                - where: Metadata filter
                
        Returns:
            List of Document objects sorted by relevance.
        """
        pass
    
    @property
    def name(self) -> str:
        """Get retriever name."""
        return self.__class__.__name__


class HybridRetriever(Retriever):
    """Hybrid retriever combining vector and BM25 search.
    
    This retriever uses the existing HybridSearchService to provide
    combined vector and lexical search results.
    
    Attributes:
        alpha: Weight for vector search (default: 0.5)
        beta: Weight for BM25 search (default: 0.5)
    """
    
    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        rrf_k: int = 60,
    ) -> None:
        """Initialize hybrid retriever.
        
        Args:
            alpha: Weight for vector search (default: 0.5)
            beta: Weight for BM25 search (default: 0.5)
            rrf_k: RRF constant (default: 60)
        """
        self._alpha = alpha
        self._beta = beta
        self._rrf_k = rrf_k
        self._service = None
    
    async def retrieve(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Retrieve documents using hybrid search.
        
        Args:
            query: The search query string.
            options: Optional retrieval options:
                - collection: Collection name (required)
                - topK: Number of results (default: 10)
                - where: Metadata filter
                
        Returns:
            List of Document objects sorted by relevance.
        """
        options = options or {}
        
        collection = options.get("collection", "default")
        top_k = options.get("topK", 10)
        where = options.get("where")
        
        # Lazy import to avoid circular dependency
        from src.services.hybrid_search import get_hybrid_search_service
        
        service = get_hybrid_search_service(
            alpha=self._alpha,
            beta=self._beta,
            rrf_k=self._rrf_k,
        )
        
        # Perform hybrid search
        results = service.search(
            collection_name=collection,
            query=query,
            n_results=top_k,
            where=where,
        )
        
        # Convert to Document objects
        documents = []
        for result in results:
            doc = Document(
                id=result.id,
                text=result.text,
                score=result.score,
                metadata=result.metadata or {},
                vector_score=result.vector_score,
                bm25_score=result.bm25_score,
            )
            documents.append(doc)
        
        return documents
    
    @property
    def alpha(self) -> float:
        """Get vector search weight."""
        return self._alpha
    
    @property
    def beta(self) -> float:
        """Get BM25 search weight."""
        return self._beta


class VectorRetriever(Retriever):
    """Vector-only retriever using semantic similarity.
    
    This retriever uses vector similarity search only via the
    BaseVectorStoreProvider interface.
    """
    
    def __init__(self, collection: str = "default") -> None:
        """Initialize vector retriever.
        
        Args:
            collection: Collection name to query.
        """
        self._collection = collection
    
    async def retrieve(
        self,
        query: str,
        options: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Retrieve documents using vector similarity.
        
        Args:
            query: The search query string.
            options: Optional retrieval options:
                - collection: Collection name
                - topK: Number of results
                - where: Metadata filter
                
        Returns:
            List of Document objects sorted by relevance.
        """
        options = options or {}
        
        collection = options.get("collection", self._collection)
        top_k = options.get("topK", 10)
        where = options.get("where")
        
        # Use VectorDBProvider interface (RULE-3 compliance)
        # Uses default provider from config - configuration driven
        from src.providers.factory import factory
        
        vectorstore = factory.get_vectorstore_provider()
        
        result = vectorstore.query(
            collection=collection,
            query_text=query,
            n_results=top_k,
            where=where,
        )
        
        documents = []
        for search_result in result.results:
            # Convert distance-based score from ChromaDB
            # ChromaDB returns distance (lower = better), we convert to score (higher = better)
            distance = search_result.score
            # Handle None or negative distance as default 0.0
            if distance is not None and distance >= 0:
                score = 1.0 / (1.0 + distance)
            else:
                score = 0.0
            
            # Handle None metadata
            metadata = search_result.metadata if search_result.metadata is not None else {}
            
            doc = Document(
                id=search_result.id,
                text=search_result.document,
                score=score,
                metadata=metadata,
                vector_score=score,
            )
            documents.append(doc)
        
        return documents