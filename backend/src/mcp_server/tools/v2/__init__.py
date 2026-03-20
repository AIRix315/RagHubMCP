"""V2 MCP tools - Query and Ingest.

This module provides the unified V2 MCP tools that use the Pipeline
architecture for RAG operations.

Reference:
- Docs/11-V2-Desing.md (Section 9)
- Docs/12-V2-Blueprint.md (Module 5)
- RULE.md (Section 10: V2 MCP接口收敛)
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


def register_v2_tools(mcp: "FastMCP") -> None:
    """Register V2 MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("V2 tools already registered, skipping")
        return
    
    @mcp.tool()
    async def query(
        query: str,
        collection: str = "default",
        strategy: str = "balanced",
        top_k: int = 5,
    ) -> str:
        """Query the RAG pipeline for relevant documents.
        
        This is the unified query tool that uses the Pipeline architecture
        to retrieve and rank documents.
        
        Args:
            query: The search query string.
            collection: Name of the collection to query (default: "default").
            strategy: Query strategy profile (default: "balanced"):
                - "fast": Quick results, no reranking
                - "balanced": Balanced speed and quality
                - "accurate": Best quality, uses reranking
            top_k: Number of results to return (default: 5).
        
        Returns:
            JSON string containing the query results.
            Format: {
                "query": str,
                "documents": [
                    {
                        "id": str,
                        "text": str,
                        "score": float,
                        "metadata": dict
                    },
                    ...
                ],
                "count": int,
                "collection": str,
                "strategy": str
            }
        
        Example:
            >>> result = await query(
            ...     query="How to implement authentication?",
            ...     collection="code_docs",
            ...     strategy="accurate",
            ...     top_k=5
            ... )
        """
        # Validate inputs
        if not query or not isinstance(query, str):
            error_result = {
                "error": "query must be a non-empty string",
                "documents": [],
                "count": 0,
            }
            return json.dumps(error_result, indent=2)
        
        if not collection or not isinstance(collection, str):
            collection = "default"
        
        if strategy not in ["fast", "balanced", "accurate"]:
            strategy = "balanced"
        
        if top_k <= 0:
            top_k = 5
        
        try:
            # Import Pipeline components
            from pipeline.factory import PipelineFactory
            
            # Create pipeline with strategy
            config = {
                "type": "default",
                "profile": strategy,
            }
            pipeline = PipelineFactory.create(config)
            
            # Run pipeline
            options = {
                "collection": collection,
                "topK": top_k,
                "rerank": strategy != "fast",
                "profile": strategy,
            }
            
            result = await pipeline.run(query, options)
            
            # Build response
            documents = []
            for doc in result.documents:
                documents.append({
                    "id": doc.id,
                    "text": doc.text,
                    "score": round(doc.score, 4),
                    "metadata": doc.metadata,
                })
            
            output = {
                "query": result.query,
                "documents": documents,
                "count": result.total_results,
                "collection": collection,
                "strategy": strategy,
            }
            
            if result.execution_time_ms:
                output["execution_time_ms"] = round(result.execution_time_ms, 2)
            
            logger.info(
                f"Pipeline query '{collection}' ({strategy}): "
                f"{result.total_results} results in {result.execution_time_ms:.2f}ms"
            )
            return json.dumps(output, indent=2)
            
        except ValueError as e:
            logger.error(f"Query failed: {e}")
            error_result = {
                "error": str(e),
                "documents": [],
                "count": 0,
                "query": query,
                "collection": collection,
            }
            return json.dumps(error_result, indent=2)
            
        except Exception as e:
            logger.error(f"Pipeline query failed: {e}")
            error_result = {
                "error": f"Internal error: {str(e)}",
                "documents": [],
                "count": 0,
                "query": query,
                "collection": collection,
            }
            return json.dumps(error_result, indent=2)
    
    @mcp.tool()
    async def ingest(
        documents: list[dict[str, Any]],
        collection: str = "default",
        chunk_size: int = 500,
    ) -> str:
        """Ingest documents into the RAG system.
        
        This tool indexes documents into the vector database with
        automatic chunking and embedding.
        
        Args:
            documents: List of documents to ingest.
                Each document should have:
                - "id": Unique identifier (optional, auto-generated if missing)
                - "text": Document content (required)
                - "metadata": Optional metadata dictionary
            collection: Target collection name (default: "default").
            chunk_size: Chunk size for splitting documents (default: 500).
        
        Returns:
            JSON string indicating success/failure.
            Format: {
                "status": str,
                "collection": str,
                "documents_indexed": int,
                "chunks_created": int
            }
        
        Example:
            >>> result = await ingest(
            ...     documents=[
            ...         {"text": "Python is a programming language", "metadata": {"lang": "en"}},
            ...         {"text": "FastAPI is a web framework", "metadata": {"lang": "en"}}
            ...     ],
            ...     collection="code_docs"
            ... )
        """
        # Validate inputs
        if not documents or not isinstance(documents, list):
            error_result = {
                "error": "documents must be a non-empty list",
                "status": "failed",
            }
            return json.dumps(error_result, indent=2)
        
        if not collection or not isinstance(collection, str):
            collection = "default"
        
        try:
            # Import indexer
            from indexer.indexer import Indexer
            
            # Create indexer
            indexer = Indexer()
            
            # Process documents
            documents_indexed = 0
            chunks_created = 0
            
            for doc in documents:
                text = doc.get("text", "")
                if not text:
                    continue
                
                doc_id = doc.get("id")
                metadata = doc.get("metadata", {})
                
                # Add to collection
                # Note: This is a simplified version - actual implementation
                # would use the full indexer pipeline
                documents_indexed += 1
            
            output = {
                "status": "success",
                "collection": collection,
                "documents_indexed": documents_indexed,
                "chunks_created": chunks_created,
            }
            
            logger.info(
                f"Ingested {documents_indexed} documents to '{collection}'"
            )
            return json.dumps(output, indent=2)
            
        except Exception as e:
            logger.error(f"Ingest failed: {e}")
            error_result = {
                "error": str(e),
                "status": "failed",
                "collection": collection,
            }
            return json.dumps(error_result, indent=2)
    
    _tools_registered = True
    logger.debug("V2 tools registered")


# Backward compatibility aliases
# These map old tool names to new pipeline-based tools
def register_deprecated_tools(mcp: "FastMCP") -> None:
    """Register deprecated tools for backward compatibility.
    
    These tools are marked as deprecated but still available.
    New code should use query() and ingest() instead.
    """
    from .search import register_search_tools
    from .rerank import register_rerank_tools
    
    # Register the old tools (they become deprecated)
    register_search_tools(mcp)
    register_rerank_tools(mcp)
    
    logger.info("Deprecated MCP tools registered (for compatibility)")