"""Rerank MCP tool implementation.

This module provides the rerank_documents tool for re-ordering documents
based on relevance to a query using configured rerank providers.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Flag to track if tools are registered
_tools_registered = False


def register_rerank_tools(mcp: "FastMCP") -> None:
    """Register rerank MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Rerank tools already registered, skipping")
        return
    
    @mcp.tool()
    def rerank_documents(
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> str:
        """Re-rank documents by relevance to a query.
        
        Uses the configured rerank provider to re-order a list of documents
        based on their semantic relevance to the query. Returns documents
        sorted by relevance score (highest first).
        
        Args:
            query: The search query string to rank documents against.
            documents: List of document texts to re-rank.
            top_k: Number of top results to return. Default: 5.
                   If top_k > len(documents), returns all documents.
        
        Returns:
            JSON string containing reranked results with scores.
            Format: {
                "results": [
                    {"index": int, "score": float, "text": str},
                    ...
                ],
                "count": int,
                "query": str
            }
        
        Example:
            >>> result = rerank_documents(
            ...     query="What is machine learning?",
            ...     documents=["ML is AI.", "Python is a language."],
            ...     top_k=2
            ... )
        """
        # Handle empty documents
        if not documents:
            result = {
                "results": [],
                "count": 0,
                "query": query,
                "message": "No documents provided for reranking"
            }
            return json.dumps(result, indent=2)
        
        # Validate top_k
        if top_k <= 0:
            top_k = len(documents)
        
        try:
            # Get rerank provider from factory
            from providers.factory import factory
            provider = factory.get_rerank_provider()
            
            # Perform reranking
            rerank_results = provider.rerank(query, documents, top_k)
            
            # Convert RerankResult to JSON-serializable format
            results = [
                {
                    "index": r.index,
                    "score": r.score,
                    "text": r.text,
                }
                for r in rerank_results
            ]
            
            output = {
                "results": results,
                "count": len(results),
                "query": query,
            }
            
            logger.info(f"Reranked {len(documents)} documents, returned top {len(results)}")
            return json.dumps(output, indent=2)
            
        except Exception as e:
            logger.error(f"Rerank failed: {e}")
            error_result = {
                "error": str(e),
                "results": [],
                "count": 0,
                "query": query,
            }
            return json.dumps(error_result, indent=2)
    
    _tools_registered = True
    logger.debug("Rerank tools registered")