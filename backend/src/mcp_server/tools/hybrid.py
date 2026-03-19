"""Hybrid search MCP tool implementation.

This module provides the hybrid_search tool for combining
vector similarity search with BM25 lexical search using
Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Flag to track if tools are registered
_tools_registered = False


def register_hybrid_tools(mcp: "FastMCP") -> None:
    """Register hybrid search MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Hybrid tools already registered, skipping")
        return
    
    @mcp.tool()
    def hybrid_search(
        collection_name: str,
        query: str,
        n_results: int = 10,
        alpha: float | None = None,
        beta: float | None = None,
        where: dict[str, Any] | None = None,
    ) -> str:
        """Perform hybrid search combining vector similarity and BM25 lexical search.
        
        This tool combines semantic (vector) and keyword (BM25) search using
        Reciprocal Rank Fusion (RRF) for improved retrieval quality:
        1. Queries ChromaDB for vector similarity results
        2. Queries BM25 index for lexical matches
        3. Fuses results using RRF algorithm
        4. Returns ranked hybrid results
        
        Args:
            collection_name: Name of the ChromaDB collection to search.
            query: The search query string.
            n_results: Number of results to return (default: 10).
            alpha: Weight for vector search results (default: from config, typically 0.5).
                   Higher values prioritize semantic similarity.
            beta: Weight for BM25 search results (default: from config, typically 0.5).
                  Higher values prioritize keyword matching.
            where: Optional metadata filter using ChromaDB query syntax.
                   Examples: {"category": "docs"}, {"year": {"$gt": 2020}}
        
        Returns:
            JSON string containing hybrid search results with scores.
            Format: {
                "results": [
                    {
                        "id": str,
                        "text": str,
                        "score": float,
                        "vector_score": float,
                        "bm25_score": float,
                        "rank": int,
                        "metadata": dict,
                        "distance": float
                    },
                    ...
                ],
                "count": int,
                "query": str,
                "collection": str,
                "alpha": float,
                "beta": float
            }
        
        Raises:
            ValueError: If collection doesn't exist or query is invalid.
        
        Example:
            >>> result = hybrid_search(
            ...     collection_name="code_docs",
            ...     query="How to implement authentication?",
            ...     n_results=10,
            ...     alpha=0.6,
            ...     beta=0.4,
            ...     where={"language": "python"}
            ... )
        """
        # Validate inputs
        if not collection_name or not isinstance(collection_name, str):
            error_result = {
                "error": "collection_name must be a non-empty string",
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
        
        if not query or not isinstance(query, str):
            error_result = {
                "error": "query must be a non-empty string",
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
        
        if n_results <= 0:
            n_results = 10
        
        # Validate alpha and beta
        if alpha is not None and not (0 <= alpha <= 1):
            error_result = {
                "error": "alpha must be between 0 and 1",
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
        
        if beta is not None and not (0 <= beta <= 1):
            error_result = {
                "error": "beta must be between 0 and 1",
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
        
        try:
            # Get hybrid search service
            from services import get_hybrid_search_service
            
            service = get_hybrid_search_service(alpha=alpha, beta=beta)
            
            # Perform hybrid search
            results = service.search(
                collection_name=collection_name,
                query=query,
                n_results=n_results,
                where=where,
            )
            
            # Handle empty results
            if not results:
                result = {
                    "results": [],
                    "count": 0,
                    "query": query,
                    "collection": collection_name,
                    "alpha": service.alpha,
                    "beta": service.beta,
                    "message": f"No documents found in collection '{collection_name}'"
                }
                return json.dumps(result, indent=2)
            
            # Build output
            output_results = []
            for r in results:
                output_results.append({
                    "id": r.id,
                    "text": r.text,
                    "score": r.score,
                    "vector_score": r.vector_score,
                    "bm25_score": r.bm25_score,
                    "rank": r.rank,
                    "metadata": r.metadata,
                    "distance": r.distance,
                })
            
            output = {
                "results": output_results,
                "count": len(output_results),
                "query": query,
                "collection": collection_name,
                "alpha": service.alpha,
                "beta": service.beta,
            }
            
            logger.info(
                f"Hybrid search '{collection_name}': returned {len(results)} results "
                f"(alpha={service.alpha}, beta={service.beta})"
            )
            return json.dumps(output, indent=2)
            
        except ValueError as e:
            # Collection not found or invalid query
            logger.error(f"Hybrid search failed: {e}")
            error_result = {
                "error": str(e),
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            error_result = {
                "error": f"Internal error: {str(e)}",
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
    
    @mcp.tool()
    def bm25_index_documents(
        collection_name: str,
        documents: list[str],
        ids: list[str],
    ) -> str:
        """Index documents for BM25 lexical search.
        
        This tool creates or updates a BM25 index for a collection,
        enabling lexical/keyword search capabilities.
        
        Args:
            collection_name: Name of the collection to index.
            documents: List of document texts to index.
            ids: List of unique document IDs (must match documents length).
        
        Returns:
            JSON string with indexing result.
            Format: {
                "success": bool,
                "indexed_count": int,
                "collection": str,
                "message": str
            }
        
        Example:
            >>> result = bm25_index_documents(
            ...     collection_name="my_docs",
            ...     documents=["Document 1 text", "Document 2 text"],
            ...     ids=["doc1", "doc2"]
            ... )
        """
        # Validate inputs
        if not collection_name or not isinstance(collection_name, str):
            return json.dumps({
                "success": False,
                "indexed_count": 0,
                "collection": collection_name,
                "error": "collection_name must be a non-empty string"
            }, indent=2)
        
        if not documents or not isinstance(documents, list):
            return json.dumps({
                "success": False,
                "indexed_count": 0,
                "collection": collection_name,
                "error": "documents must be a non-empty list"
            }, indent=2)
        
        if not ids or not isinstance(ids, list):
            return json.dumps({
                "success": False,
                "indexed_count": 0,
                "collection": collection_name,
                "error": "ids must be a non-empty list"
            }, indent=2)
        
        if len(documents) != len(ids):
            return json.dumps({
                "success": False,
                "indexed_count": 0,
                "collection": collection_name,
                "error": "documents and ids must have the same length"
            }, indent=2)
        
        try:
            from services import get_bm25_service
            
            bm25_service = get_bm25_service()
            bm25_service.index_documents(collection_name, documents, ids)
            
            return json.dumps({
                "success": True,
                "indexed_count": len(documents),
                "collection": collection_name,
                "message": f"Successfully indexed {len(documents)} documents"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"BM25 indexing failed: {e}")
            return json.dumps({
                "success": False,
                "indexed_count": 0,
                "collection": collection_name,
                "error": str(e)
            }, indent=2)
    
    @mcp.tool()
    def bm25_query(
        collection_name: str,
        query: str,
        k: int = 10,
    ) -> str:
        """Query BM25 index for lexical/keyword search.
        
        This tool performs a pure BM25 search without vector search,
        useful for keyword-focused retrieval or testing BM25 index.
        
        Args:
            collection_name: Name of the collection to search.
            query: Search query string.
            k: Number of results to return (default: 10).
        
        Returns:
            JSON string with BM25 search results.
            Format: {
                "results": [
                    {"id": str, "score": float},
                    ...
                ],
                "count": int,
                "query": str,
                "collection": str
            }
        
        Example:
            >>> result = bm25_query(
            ...     collection_name="my_docs",
            ...     query="search keywords",
            ...     k=5
            ... )
        """
        # Validate inputs
        if not collection_name or not isinstance(collection_name, str):
            return json.dumps({
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
                "error": "collection_name must be a non-empty string"
            }, indent=2)
        
        if not query or not isinstance(query, str):
            return json.dumps({
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
                "error": "query must be a non-empty string"
            }, indent=2)
        
        if k <= 0:
            k = 10
        
        try:
            from services import get_bm25_service
            
            bm25_service = get_bm25_service()
            results = bm25_service.query(collection_name, query, k)
            
            output_results = [
                {"id": doc_id, "score": score}
                for doc_id, score in results
            ]
            
            return json.dumps({
                "results": output_results,
                "count": len(output_results),
                "query": query,
                "collection": collection_name
            }, indent=2)
            
        except Exception as e:
            logger.error(f"BM25 query failed: {e}")
            return json.dumps({
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
                "error": str(e)
            }, indent=2)
    
    _tools_registered = True
    logger.debug("Hybrid tools registered")