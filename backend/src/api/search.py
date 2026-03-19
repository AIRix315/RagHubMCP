"""Search REST API endpoints.

This module provides endpoints for searching indexed documents.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import chromadb
from fastapi import APIRouter, HTTPException

from src.utils.config import get_config

from .schemas import (
    ErrorResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])

# Chroma client cache
_chroma_client: chromadb.Client | None = None


def get_chroma_client() -> chromadb.Client:
    """Get or create Chroma client.

    Returns:
        Chroma client instance.
    """
    global _chroma_client

    if _chroma_client is None:
        config = get_config()

        if config.chroma.host:
            # Remote Chroma server
            _chroma_client = chromadb.HttpClient(
                host=config.chroma.host,
                port=config.chroma.port or 8000,
            )
        else:
            # Local persistent Chroma
            _chroma_client = chromadb.PersistentClient(path=config.chroma.persist_dir)

    return _chroma_client


async def perform_search(
    query: str,
    collection_name: str,
    top_k: int,
    embedding_provider_name: str | None,
    rerank_provider_name: str | None,
    use_rerank: bool,
) -> tuple[list[SearchResult], str, str | None]:
    """Perform a search query.

    Args:
        query: Search query text.
        collection_name: Collection to search.
        top_k: Number of results.
        embedding_provider_name: Optional embedding provider.
        rerank_provider_name: Optional rerank provider.
        use_rerank: Whether to use reranking.

    Returns:
        Tuple of (results, embedding_provider_used, rerank_provider_used).
    """
    config = get_config()

    # Get embedding provider
    from providers.factory import factory

    emb_name = embedding_provider_name or config.providers.embedding.default
    embedding_provider = factory.get_embedding_provider(emb_name)

    # Generate query embedding
    query_embedding = embedding_provider.embed(query)

    # Get Chroma collection
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        logger.warning(f"Collection {collection_name} not found: {e}")
        return [], emb_name, None

    # Query Chroma
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Parse results
    search_results: list[SearchResult] = []

    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            text = results["documents"][0][i] if results["documents"] else ""
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0.0

            # Convert distance to similarity score (assuming cosine distance)
            score = 1.0 - distance

            search_results.append(
                SearchResult(
                    id=doc_id,
                    text=text,
                    score=score,
                    metadata=metadata,
                )
            )

    # Apply reranking if requested
    rerank_name = None
    if use_rerank and search_results:
        rerank_name = rerank_provider_name or config.providers.rerank.default

        try:
            rerank_provider = factory.get_rerank_provider(rerank_name)

            documents = [r.text for r in search_results]
            rerank_results = rerank_provider.rerank(query, documents, top_k)

            # Reorder and update scores
            reordered: list[SearchResult] = []
            for rr in rerank_results:
                original = search_results[rr.index]
                reordered.append(
                    SearchResult(
                        id=original.id,
                        text=original.text,
                        score=original.score,
                        metadata=original.metadata,
                        rerank_score=rr.score,
                    )
                )

            search_results = reordered

        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            rerank_name = None

    return search_results, emb_name, rerank_name


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
async def execute_search(request: SearchRequest) -> SearchResponse:
    """Execute a search query.

    TC-1.15.5: POST /api/search executes search

    Args:
        request: Search request parameters.

    Returns:
        Search results.

    Raises:
        HTTPException: If search fails.
    """
    try:
        start_time = time.time()

        results, emb_name, rerank_name = await perform_search(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k,
            embedding_provider_name=request.embedding_provider,
            rerank_provider_name=request.rerank_provider,
            use_rerank=request.use_rerank,
        )

        latency = (time.time() - start_time) * 1000

        logger.info(
            f"Search completed: query='{request.query[:50]}...', "
            f"results={len(results)}, latency={latency:.2f}ms"
        )

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            collection=request.collection_name,
            embedding_provider=emb_name,
            rerank_provider=rerank_name,
        )

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "search_failed",
                "message": f"Search failed: {str(e)}",
            },
        )


# =============================================================================
# Collection Management Endpoints
# =============================================================================


@router.get(
    "/collections",
    response_model=dict,
    summary="List collections",
    description="List all Chroma collections",
)
async def list_collections() -> dict[str, Any]:
    """List all collections.

    Returns:
        List of collection info.
    """
    client = get_chroma_client()
    collections = client.list_collections()

    result = []
    for coll in collections:
        result.append(
            {
                "name": coll.name,
                "count": coll.count(),
                "metadata": coll.metadata or {},
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
    description="Delete a Chroma collection by name",
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
    client = get_chroma_client()

    try:
        client.delete_collection(name)
        logger.info(f"Collection deleted: {name}")
        return {
            "name": name,
            "message": "Collection deleted successfully",
        }
    except Exception:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "collection_not_found",
                "message": f"Collection not found: {name}",
            },
        )
