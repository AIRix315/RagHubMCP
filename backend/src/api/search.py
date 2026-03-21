"""Search REST API endpoints.

This module provides endpoints for searching indexed documents.
All search operations go through the RAG Pipeline.

Reference:
- Docs/11-V2-Desing.md (RULE-1: Pipeline是唯一执行入口)
- Docs/12-V2-Blueprint.md (Module 1)
- RULE.md (RULE-3: 禁止在模块中直接依赖具体实现)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from src.utils.config import get_config

from .pipeline_adapter import rag_result_to_search_response
from .schemas import (
    ErrorResponse,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


def _get_vectorstore_provider() -> Any:
    """Get VectorStore provider through factory (RULE-3 compliant).

    Returns:
        VectorStoreProvider instance from factory.
    """
    from src.providers.factory import factory

    return factory.get_vectorstore_provider()


@router.post(
    "",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Search failed"},
    },
    summary="Execute search",
    description="Search indexed documents with optional reranking",
)
async def execute_search_endpoint(request: SearchRequest) -> SearchResponse:
    """Execute a search query.

    TC-1.15.5: POST /api/search executes search

    All search operations go through the RAG Pipeline:
    1. Retrieval (Hybrid: vector + BM25)
    2. Reranking (FlashRank)
    3. Context Building

    Args:
        request: Search request parameters.

    Returns:
        Search results.

    Raises:
        HTTPException: If search fails.
    """
    # Validate request
    if not request.query or not request.query.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_request",
                "message": "Query cannot be empty",
                "detail": None,
            },
        )

    if request.top_k < 1 or request.top_k > 100:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_request",
                "message": "top_k must be between 1 and 100",
                "detail": {"top_k": request.top_k},
            },
        )

    try:
        start_time = time.time()

        # Import pipeline (lazy to avoid circular imports)
        from src.pipeline import execute_search as pipeline_search

        config = get_config()

        # Build pipeline options
        options = {
            "collection": request.collection_name,
            "topK": request.top_k,
            "rerank": request.use_rerank,
        }

        # Execute search through pipeline
        result = await pipeline_search(request.query, options)

        # Get provider names for response
        emb_name = config.providers.embedding.default
        rerank_name = None
        if request.use_rerank:
            rerank_name = request.rerank_provider or config.providers.rerank.default

        # Convert to API response
        response = rag_result_to_search_response(
            result=result,
            collection=request.collection_name,
            embedding_provider=emb_name,
            rerank_provider=rerank_name,
        )

        latency = (time.time() - start_time) * 1000
        logger.info(
            f"Search completed: query='{request.query[:50]}...', "
            f"results={len(response.results)}, latency={latency:.2f}ms"
        )

        return response

    except ValueError as e:
        # Collection not found or invalid parameters
        logger.warning(f"Search validation error: {e}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "collection_not_found",
                "message": str(e),
                "detail": {"collection": request.collection_name},
            },
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "search_failed",
                "message": f"Search failed: {str(e)}",
                "detail": None,
            },
        )


# =============================================================================
# Collection Management Endpoints
# =============================================================================


@router.get(
    "/collections",
    response_model=dict,
    summary="List collections",
    description="List all collections from the vector store",
)
async def list_collections() -> dict[str, Any]:
    """List all collections.

    Returns:
        List of collection info.
    """
    vectorstore = _get_vectorstore_provider()
    collection_names = vectorstore.list_collections()

    result = []
    for name in collection_names:
        # Get collection details
        try:
            count = vectorstore.count(name)
            result.append(
                {
                    "name": name,
                    "count": count,
                    "metadata": {},  # Metadata not available through Provider interface
                }
            )
        except Exception:
            result.append(
                {
                    "name": name,
                    "count": 0,
                    "metadata": {},
                }
            )

    return {
        "collections": result,
        "total": len(result),
    }


@router.delete(
    "/collections/{name}",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
    },
    summary="Delete collection",
    description="Delete a collection by name from the vector store",
)
async def delete_collection(name: str) -> dict[str, Any]:
    """Delete a collection.

    Args:
        name: Collection name.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If collection not found.
    """
    vectorstore = _get_vectorstore_provider()

    try:
        vectorstore.delete_collection(name)
        logger.info(f"Collection deleted: {name}")
        return {
            "name": name,
            "message": "Collection deleted successfully",
        }
    except ValueError:
        # Collection not found
        logger.warning(f"Collection not found: {name}")
        raise HTTPException(
            status_code=404,
            detail={
                "error": "collection_not_found",
                "message": f"Collection not found: {name}",
                "detail": None,
            },
        )
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "delete_failed",
                "message": f"Failed to delete collection: {str(e)}",
                "detail": None,
            },
        )
