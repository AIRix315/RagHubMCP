"""Pipeline adapter for REST API.

This module provides adapters to convert Pipeline results
to API response formats.

Reference:
- Docs/11-V2-Desing.md (RULE-1: Pipeline是唯一执行入口)
- Docs/12-V2-Blueprint.md (Module 1)
"""

from __future__ import annotations

from typing import Any

from src.api.schemas import SearchResult, SearchResponse
from src.pipeline.result import RAGResult, Document


def rag_result_to_search_response(
    result: RAGResult,
    collection: str,
    embedding_provider: str,
    rerank_provider: str | None = None,
) -> SearchResponse:
    """Convert RAGResult to SearchResponse.
    
    This adapter transforms the pipeline's internal result format
    to the API response format expected by clients.
    
    Args:
        result: Pipeline result containing documents and metadata.
        collection: Collection name that was queried.
        embedding_provider: Name of the embedding provider used.
        rerank_provider: Name of the rerank provider used (if any).
        
    Returns:
        SearchResponse ready to be returned to the client.
        
    Example:
        >>> from pipeline import execute_search
        >>> from api.pipeline_adapter import rag_result_to_search_response
        >>> result = await execute_search("query", {"collection": "docs"})
        >>> response = rag_result_to_search_response(
        ...     result, "docs", "ollama", "flashrank"
        ... )
    """
    search_results = [
        SearchResult(
            id=doc.id,
            text=doc.text,
            score=doc.score,
            metadata=doc.metadata,
            rerank_score=doc.rerank_score,
        )
        for doc in result.documents
    ]
    
    return SearchResponse(
        query=result.query,
        results=search_results,
        total=len(search_results),
        collection=collection,
        embedding_provider=embedding_provider,
        rerank_provider=rerank_provider,
    )


def document_to_search_result(doc: Document) -> SearchResult:
    """Convert a single Document to SearchResult.
    
    Args:
        doc: Pipeline Document object.
        
    Returns:
        SearchResult for API response.
    """
    return SearchResult(
        id=doc.id,
        text=doc.text,
        score=doc.score,
        metadata=doc.metadata,
        rerank_score=doc.rerank_score,
    )


def documents_to_search_results(documents: list[Document]) -> list[SearchResult]:
    """Convert a list of Documents to SearchResults.
    
    Args:
        documents: List of pipeline Document objects.
        
    Returns:
        List of SearchResult objects.
    """
    return [document_to_search_result(doc) for doc in documents]


def rag_results_to_benchmark_results(
    results: list[tuple[str, RAGResult]],
) -> list[dict[str, Any]]:
    """Convert multiple RAGResults to benchmark result format.
    
    Args:
        results: List of (config_name, RAGResult) tuples.
        
    Returns:
        List of benchmark result dictionaries.
    """
    benchmark_results = []
    
    for config_name, result in results:
        benchmark_results.append({
            "config_name": config_name,
            "results": documents_to_search_results(result.documents),
            "latency_ms": result.execution_time_ms,
            "total": len(result.documents),
        })
    
    return benchmark_results