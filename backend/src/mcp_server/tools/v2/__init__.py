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

# Import unified error handling
from mcp_server.tools._errors import (
    error_response,
    success_response,
    validate_collection_name,
    validate_query,
    validate_documents,
    validate_positive_int,
    validate_range,
)

# Import strict validation functions (lazy import to avoid circular dependency)

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
                - "fast": Quick results, no reranking, 3 results
                  - retrieval_multiplier: 1.5x
                  - Best for: Simple lookups, quick previews
                - "balanced": Balanced speed and quality with reranking (default)
                  - retrieval_multiplier: 2.0x
                  - Best for: General purpose queries
                - "accurate": Best quality, higher latency
                  - retrieval_multiplier: 3.0x
                  - Best for: Research, detailed analysis
            top_k: Number of results to return (default: 5).
                  Note: Actual retrieval count is top_k * retrieval_multiplier
                  based on strategy, to allow for reranking.
        
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
                "strategy": str,
                "profile": str
            }
        
        Example:
            >>> result = await query(
            ...     query="How to implement authentication?",
            ...     collection="code_docs",
            ...     strategy="accurate",
            ...     top_k=5
            ... )
        """
        # Validate inputs using unified error handling
        error = validate_query(query)
        if error:
            return error_response(error, documents=[], count=0)
        
        if not collection or not isinstance(collection, str):
            collection = "default"
        
        # Validate and normalize strategy
        valid_strategies = ["fast", "balanced", "accurate"]
        if strategy not in valid_strategies:
            strategy = "balanced"
        
        if top_k <= 0:
            top_k = 5
        
        try:
            # Import Pipeline components
            from pipeline.factory import PipelineFactory, PROFILES
            
            # Get profile configuration for metadata
            profile_config = PROFILES.get(strategy, PROFILES["balanced"])
            
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
                "rerank": profile_config.rerank,
                "profile": strategy,
                "merge_consecutive": False,  # Not in PipelineProfileConfig
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
                "profile": {
                    "name": strategy,
                    "rerank": profile_config.rerank,
                    "retrieval_multiplier": profile_config.retrieval_multiplier,
                },
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
            return error_response(str(e), documents=[], count=0, query=query, collection=collection)
            
        except Exception as e:
            logger.error(f"Pipeline query failed: {e}")
            return error_response(f"Internal error: {str(e)}", documents=[], count=0, query=query, collection=collection)
    
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
                Must be a valid identifier: alphanumeric, underscores, hyphens.
            chunk_size: Chunk size for splitting documents (default: 500).
                Must be between 50 and 10000 characters.
        
        Returns:
            JSON string indicating success/failure.
            Format: {
                "status": str,
                "collection": str,
                "documents_indexed": int,
                "chunks_created": int,
                "errors": list (if any)
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
        import uuid
        
        # Import validation methods from unified error handling
        from mcp_server.tools._errors import (
            validate_collection_name_strict,
            validate_documents_list,
            validate_int_range,
            validate_metadata,
            validate_text_field,
        )
        
        # Validate inputs using unified validation methods
        # Auto-default empty collection to "default"
        if not collection:
            collection = "default"
        
        error = validate_documents_list(documents)
        if error:
            return error_response(error, status="failed", collection=collection)
        
        # Validate collection name strictly
        collection_error = validate_collection_name_strict(collection)
        if collection_error:
            return error_response(collection_error, status="failed", collection=collection)
        
        # Validate chunk_size with range validation
        chunk_error = validate_int_range(chunk_size, "chunk_size", 50, 10000)
        if chunk_error:
            # Auto-correct chunk_size instead of failing
            chunk_size = max(50, min(10000, chunk_size if isinstance(chunk_size, int) else 500))
            logger.warning(f"chunk_size adjusted to {chunk_size} (valid range: 50-10000)")
        
        try:
            # Get providers through factory (follows RULE-3)
            from providers.factory import factory
            from chunkers import SimpleChunker
            
            vectorstore = factory.get_vectorstore_provider()
            
            # Create chunker for text splitting
            chunker = SimpleChunker(chunk_size=chunk_size, overlap=min(50, chunk_size // 10))
            
            # Ensure collection exists
            if not vectorstore.collection_exists(collection):
                vectorstore.create_collection(collection)
            
            # Process documents
            documents_indexed = 0
            chunks_created = 0
            errors: list[str] = []
            
            for doc_idx, doc in enumerate(documents):
                if not isinstance(doc, dict):
                    errors.append(f"Document at index {doc_idx} is not a dictionary")
                    continue
                
                # Validate and sanitize text using unified validation
                text = doc.get("text", "")
                text_error = validate_text_field(text, "text")
                if text_error:
                    errors.append(f"Document at index {doc_idx}: {text_error}")
                    continue
                
                text = text.strip()
                
                # Get or generate document ID
                doc_id = doc.get("id")
                if doc_id:
                    # Validate ID format
                    if not isinstance(doc_id, str):
                        doc_id = str(doc_id)
                    doc_id = doc_id.strip()
                    if not doc_id:
                        doc_id = str(uuid.uuid4())
                else:
                    doc_id = str(uuid.uuid4())
                
                # Validate and sanitize metadata using unified validation
                metadata = doc.get("metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {}
                else:
                    # Deep validate metadata
                    valid, msg = validate_metadata(metadata)
                    if not valid:
                        errors.append(f"Document {doc_id} has invalid metadata: {msg}")
                        continue
                
                # Sanitize metadata values (ensure all values are JSON-serializable)
                sanitized_metadata = {"doc_id": doc_id}
                for k, v in metadata.items():
                    if isinstance(v, (str, int, float, bool, list, dict)) or v is None:
                        sanitized_metadata[k] = v
                    else:
                        sanitized_metadata[k] = str(v)
                
                # Chunk the document
                chunks = chunker.chunk(text, sanitized_metadata)
                
                if not chunks:
                    errors.append(f"Document {doc_id} produced no chunks")
                    continue
                
                # Prepare data for indexing
                chunk_texts = [chunk.text for chunk in chunks]
                chunk_ids = [f"{doc_id}:chunk:{i}" for i in range(len(chunks))]
                chunk_metadatas = []
                for i, chunk in enumerate(chunks):
                    meta = dict(chunk.metadata)
                    meta["chunk_index"] = i
                    meta["chunk_count"] = len(chunks)
                    chunk_metadatas.append(meta)
                
                # Index to vector store
                try:
                    vectorstore.add(
                        collection=collection,
                        documents=chunk_texts,
                        ids=chunk_ids,
                        metadatas=chunk_metadatas,
                    )
                    documents_indexed += 1
                    chunks_created += len(chunks)
                except Exception as e:
                    errors.append(f"Failed to index document {doc_id}: {str(e)}")
            
            # Build response
            status = "success" if documents_indexed > 0 else "partial" if chunks_created > 0 else "failed"
            output = {
                "status": status,
                "collection": collection,
                "documents_indexed": documents_indexed,
                "chunks_created": chunks_created,
                "total_documents": len(documents),
            }
            
            if errors:
                output["errors"] = errors
                output["error_count"] = len(errors)
            
            logger.info(
                f"Ingested {documents_indexed}/{len(documents)} documents "
                f"({chunks_created} chunks) to '{collection}'"
            )
            return json.dumps(output, indent=2)
            
        except Exception as e:
            logger.error(f"Ingest failed: {e}")
            return error_response(str(e), status="failed", collection=collection)
    
    _tools_registered = True
    logger.debug("V2 tools registered")