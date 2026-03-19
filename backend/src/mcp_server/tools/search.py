"""Search MCP tool implementation.

This module provides the chroma_query_with_rerank tool for combining
ChromaDB vector search with reranking for improved relevance.
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


def register_search_tools(mcp: "FastMCP") -> None:
    """Register search MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Search tools already registered, skipping")
        return
    
    @mcp.tool()
    def chroma_query_with_rerank(
        collection_name: str,
        query: str,
        n_results: int = 10,
        rerank_top_k: int = 5,
        where: dict[str, Any] | None = None,
    ) -> str:
        """Query ChromaDB and rerank results for improved relevance.
        
        This tool combines vector similarity search with reranking:
        1. Queries ChromaDB collection for relevant documents
        2. Uses rerank model to reorder results by relevance
        3. Returns top-k most relevant documents
        
        Args:
            collection_name: Name of the ChromaDB collection to query.
            query: The search query string.
            n_results: Number of documents to retrieve from ChromaDB (default: 10).
                       Higher values give rerank more candidates to work with.
            rerank_top_k: Number of top results to return after reranking (default: 5).
            where: Optional metadata filter using ChromaDB query syntax.
                   Examples: {"category": "docs"}, {"year": {"$gt": 2020}}
        
        Returns:
            JSON string containing reranked results with scores.
            Format: {
                "results": [
                    {
                        "id": str,
                        "text": str,
                        "score": float,
                        "metadata": dict,
                        "distance": float
                    },
                    ...
                ],
                "count": int,
                "query": str,
                "collection": str
            }
        
        Raises:
            ValueError: If collection doesn't exist or query is invalid.
        
        Example:
            >>> result = chroma_query_with_rerank(
            ...     collection_name="code_docs",
            ...     query="How to implement authentication?",
            ...     n_results=20,
            ...     rerank_top_k=5,
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
        
        if rerank_top_k <= 0:
            rerank_top_k = 5
        
        try:
            # Get ChromaService
            from services import get_chroma_service
            
            chroma_service = get_chroma_service()
            
            # Query ChromaDB
            query_results = chroma_service.query(
                collection_name=collection_name,
                query_text=query,
                n_results=n_results,
                where=where,
            )
            
            # Handle empty results
            if not query_results.get("documents"):
                result = {
                    "results": [],
                    "count": 0,
                    "query": query,
                    "collection": collection_name,
                    "message": f"No documents found in collection '{collection_name}'"
                }
                return json.dumps(result, indent=2)
            
            # Prepare documents for reranking
            documents = query_results.get("documents", [])
            ids = query_results.get("ids", [])
            metadatas = query_results.get("metadatas", [])
            distances = query_results.get("distances", [])
            
            # Handle empty documents list
            if not documents:
                result = {
                    "results": [],
                    "count": 0,
                    "query": query,
                    "collection": collection_name,
                    "message": "Collection is empty"
                }
                return json.dumps(result, indent=2)
            
            # Get rerank provider
            from providers.factory import factory
            
            rerank_provider = factory.get_rerank_provider()
            
            # Perform reranking
            rerank_results = rerank_provider.rerank(
                query=query,
                documents=documents,
                top_k=min(rerank_top_k, len(documents))
            )
            
            # Build final results
            results = []
            for r in rerank_results:
                idx = r.index
                result_item = {
                    "id": ids[idx] if idx < len(ids) else str(idx),
                    "text": r.text,
                    "score": round(r.score, 4),
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                    "distance": round(distances[idx], 4) if idx < len(distances) else None,
                }
                results.append(result_item)
            
            output = {
                "results": results,
                "count": len(results),
                "query": query,
                "collection": collection_name,
            }
            
            logger.info(
                f"Query '{collection_name}': retrieved {len(documents)}, "
                f"reranked to top {len(results)}"
            )
            return json.dumps(output, indent=2)
            
        except ValueError as e:
            # Collection not found or invalid query
            logger.error(f"Query failed: {e}")
            error_result = {
                "error": str(e),
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
            
        except Exception as e:
            logger.error(f"Query with rerank failed: {e}")
            error_result = {
                "error": f"Internal error: {str(e)}",
                "results": [],
                "count": 0,
                "query": query,
                "collection": collection_name,
            }
            return json.dumps(error_result, indent=2)
    
    _tools_registered = True
    logger.debug("Search tools registered")