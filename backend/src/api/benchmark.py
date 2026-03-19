"""Benchmark REST API endpoints.

This module provides endpoints for running benchmark comparisons
between different embedding and reranking configurations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException

from utils.config import get_config

from .schemas import (
    BenchmarkConfig,
    BenchmarkRequest,
    BenchmarkResponse,
    BenchmarkResult,
    ErrorResponse,
    SearchResult,
)
from .search import perform_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


async def run_single_benchmark(
    query: str,
    collection_name: str,
    config: BenchmarkConfig,
) -> BenchmarkResult:
    """Run a single benchmark configuration.

    Args:
        query: Search query.
        collection_name: Collection to search.
        config: Benchmark configuration.

    Returns:
        Benchmark result.
    """
    start_time = time.time()

    results, emb_name, rerank_name = await perform_search(
        query=query,
        collection_name=collection_name,
        top_k=config.top_k,
        embedding_provider_name=config.embedding_provider,
        rerank_provider_name=config.rerank_provider,
        use_rerank=config.rerank_provider is not None,
    )

    latency = (time.time() - start_time) * 1000

    return BenchmarkResult(
        config_name=config.name,
        results=results,
        latency_ms=latency,
        embedding_provider=emb_name,
        rerank_provider=rerank_name,
    )


@router.post(
    "",
    response_model=BenchmarkResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Collection not found"},
        500: {"model": ErrorResponse, "description": "Benchmark failed"},
    },
    summary="Run benchmark comparison",
    description="Compare search results across different configurations",
)
async def run_benchmark(request: BenchmarkRequest) -> BenchmarkResponse:
    """Run a benchmark comparison.

    TC-1.15.6: POST /api/benchmark executes comparison

    Args:
        request: Benchmark request with configurations to compare.

    Returns:
        Benchmark results for each configuration.

    Raises:
        HTTPException: If benchmark fails.
    """
    start_time = time.time()

    # Validate at least one config
    if not request.configs:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_request",
                "message": "At least one benchmark configuration is required",
            },
        )

    try:
        # Run all benchmarks concurrently
        tasks = [
            run_single_benchmark(
                query=request.query,
                collection_name=request.collection_name,
                config=config,
            )
            for config in request.configs
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        benchmark_results: list[BenchmarkResult] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Benchmark config {i} failed: {result}")
                # Add a failed result
                benchmark_results.append(
                    BenchmarkResult(
                        config_name=request.configs[i].name,
                        results=[],
                        latency_ms=0,
                        embedding_provider=request.configs[i].embedding_provider,
                        rerank_provider=request.configs[i].rerank_provider,
                    )
                )
            else:
                benchmark_results.append(result)

        total_latency = (time.time() - start_time) * 1000

        logger.info(
            f"Benchmark completed: {len(benchmark_results)} configs, "
            f"total_latency={total_latency:.2f}ms"
        )

        return BenchmarkResponse(
            query=request.query,
            collection=request.collection_name,
            results=benchmark_results,
            total_latency_ms=total_latency,
        )

    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "benchmark_failed",
                "message": f"Benchmark failed: {str(e)}",
            },
        )
