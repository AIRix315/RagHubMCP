"""Benchmark MCP tool implementation.

This module provides the benchmark_search_config tool for comparing
different search configurations and evaluating retrieval performance.
"""

from __future__ import annotations

import json
import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Flag to track if tools are registered
_tools_registered = False


def calculate_recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    """Calculate Recall@K metric.
    
    Recall@K = |relevant ∩ retrieved[:k]| / |relevant|
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: List of relevant document IDs (ground truth)
        k: Number of top results to consider
        
    Returns:
        Recall@K score (0.0 to 1.0)
    """
    if not relevant_ids:
        return 0.0
    
    top_k = retrieved_ids[:k]
    relevant_set = set(relevant_ids)
    retrieved_set = set(top_k)
    
    intersection = relevant_set & retrieved_set
    return len(intersection) / len(relevant_set)


def calculate_mrr(
    retrieved_ids: list[str],
    relevant_ids: list[str],
) -> float:
    """Calculate Mean Reciprocal Rank (MRR).
    
    MRR = 1 / rank of first relevant document
    Returns 0.0 if no relevant document is found.
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: List of relevant document IDs (ground truth)
        
    Returns:
        MRR score (0.0 to 1.0)
    """
    if not relevant_ids or not retrieved_ids:
        return 0.0
    
    relevant_set = set(relevant_ids)
    
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_set:
            return 1.0 / rank
    
    return 0.0


def register_benchmark_tools(mcp: "FastMCP") -> None:
    """Register benchmark MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Benchmark tools already registered, skipping")
        return
    
    @mcp.tool()
    def benchmark_search_config(
        collection_name: str,
        queries: list[dict[str, Any]],
        configs: list[dict[str, Any]],
        metrics: list[str] | None = None,
    ) -> str:
        """Benchmark search configurations and compare retrieval performance.
        
        This tool evaluates different search configurations by:
        1. Running queries with each configuration
        2. Calculating retrieval metrics (Recall@K, MRR)
        3. Measuring latency statistics
        4. Recommending the best configuration
        
        Args:
            collection_name: Base collection name for queries.
                            Individual configs can override this.
            queries: List of query dictionaries. Each query must have:
                    - query: The search query string
                    - relevant_ids: List of relevant document IDs (ground truth)
                    Example: [
                        {"query": "What is ML?", "relevant_ids": ["doc1", "doc2"]},
                        ...
                    ]
            configs: List of configuration dictionaries. Each config can have:
                    - name: Configuration name (required)
                    - collection_name: Override collection (optional)
                    - rerank_provider: Rerank provider name (optional)
                    - n_results: Number of results to retrieve (default: 10)
                    - rerank_top_k: Top-k after reranking (default: 5)
                    Example: [
                        {"name": "config_a", "n_results": 10, "rerank_top_k": 5},
                        {"name": "config_b", "rerank_provider": "flashrank-mini"},
                        ...
                    ]
            metrics: Optional list of metrics to compute.
                    Default: ["recall_at_k", "mrr", "latency"]
        
        Returns:
            JSON string containing benchmark results:
            {
                "results": [
                    {
                        "config_name": str,
                        "metrics": {
                            "recall_at_k": float,
                            "mrr": float,
                            "latency_avg_ms": float,
                            "latency_min_ms": float,
                            "latency_max_ms": float
                        },
                        "query_results": [...]
                    },
                    ...
                ],
                "comparison": {
                    "best_config": str,
                    "best_metric": str,
                    "table": [...]
                },
                "summary": {
                    "total_queries": int,
                    "total_configs": int
                }
            }
        
        Example:
            >>> result = benchmark_search_config(
            ...     collection_name="code_docs",
            ...     queries=[
            ...         {"query": "authentication", "relevant_ids": ["auth.py", "login.py"]},
            ...     ],
            ...     configs=[
            ...         {"name": "baseline", "n_results": 10},
            ...         {"name": "with_rerank", "rerank_top_k": 5},
            ...     ]
            ... )
        """
        # Validate inputs
        if not collection_name or not isinstance(collection_name, str):
            return json.dumps({
                "error": "collection_name must be a non-empty string",
                "results": [],
            }, indent=2)
        
        if not queries or not isinstance(queries, list):
            return json.dumps({
                "error": "queries must be a non-empty list",
                "results": [],
            }, indent=2)
        
        if not configs or not isinstance(configs, list):
            return json.dumps({
                "error": "configs must be a non-empty list",
                "results": [],
            }, indent=2)
        
        # Default metrics
        if metrics is None:
            metrics = ["recall_at_k", "mrr", "latency"]
        
        try:
            from services import get_chroma_service
            from providers.factory import factory
            
            chroma_service = get_chroma_service()
            
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            return json.dumps({
                "error": f"Service initialization failed: {str(e)}",
                "results": [],
            }, indent=2)
        
        benchmark_results = []
        
        # Evaluate each configuration
        for config in configs:
            config_name = config.get("name", "unnamed")
            config_collection = config.get("collection_name", collection_name)
            n_results = config.get("n_results", 10)
            rerank_top_k = config.get("rerank_top_k", 5)
            rerank_provider_name = config.get("rerank_provider")
            
            # Track metrics for this config
            recall_scores = []
            mrr_scores = []
            latencies = []
            config_query_results = []
            
            for query_item in queries:
                query_text = query_item.get("query", "")
                relevant_ids = query_item.get("relevant_ids", [])
                
                if not query_text:
                    continue
                
                # Measure latency
                start_time = time.perf_counter()
                
                try:
                    # Query ChromaDB
                    query_results = chroma_service.query(
                        collection_name=config_collection,
                        query_text=query_text,
                        n_results=n_results,
                    )
                    
                    retrieved_ids = query_results.get("ids", [])
                    documents = query_results.get("documents", [])
                    metadatas = query_results.get("metadatas", [])
                    distances = query_results.get("distances", [])
                    
                    # Apply reranking if configured
                    if documents and rerank_top_k > 0:
                        try:
                            if rerank_provider_name:
                                rerank_provider = factory.get_rerank_provider(rerank_provider_name)
                            else:
                                rerank_provider = factory.get_rerank_provider()
                            
                            rerank_results = rerank_provider.rerank(
                                query=query_text,
                                documents=documents,
                                top_k=min(rerank_top_k, len(documents))
                            )
                            
                            # Reorder based on rerank results
                            reranked_ids = []
                            reranked_docs = []
                            reranked_metadatas = []
                            reranked_distances = []
                            
                            for r in rerank_results:
                                idx = r.index
                                reranked_ids.append(retrieved_ids[idx] if idx < len(retrieved_ids) else str(idx))
                                reranked_docs.append(documents[idx] if idx < len(documents) else "")
                                reranked_metadatas.append(metadatas[idx] if idx < len(metadatas) else {})
                                reranked_distances.append(distances[idx] if idx < len(distances) else None)
                            
                            retrieved_ids = reranked_ids
                            
                        except Exception as e:
                            logger.warning(f"Reranking failed for config {config_name}: {e}")
                    
                    end_time = time.perf_counter()
                    latency_ms = (end_time - start_time) * 1000
                    latencies.append(latency_ms)
                    
                    # Calculate metrics
                    if "recall_at_k" in metrics:
                        recall = calculate_recall_at_k(retrieved_ids, relevant_ids, rerank_top_k)
                        recall_scores.append(recall)
                    
                    if "mrr" in metrics:
                        mrr = calculate_mrr(retrieved_ids, relevant_ids)
                        mrr_scores.append(mrr)
                    
                    # Store query result
                    config_query_results.append({
                        "query": query_text,
                        "retrieved_ids": retrieved_ids[:rerank_top_k],
                        "latency_ms": round(latency_ms, 2),
                    })
                    
                except Exception as e:
                    logger.error(f"Query failed for config {config_name}: {e}")
                    latencies.append(0)
                    recall_scores.append(0)
                    mrr_scores.append(0)
            
            # Aggregate metrics
            avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
            avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            min_latency = min(latencies) if latencies else 0.0
            max_latency = max(latencies) if latencies else 0.0
            
            benchmark_results.append({
                "config_name": config_name,
                "metrics": {
                    "recall_at_k": round(avg_recall, 4),
                    "mrr": round(avg_mrr, 4),
                    "latency_avg_ms": round(avg_latency, 2),
                    "latency_min_ms": round(min_latency, 2),
                    "latency_max_ms": round(max_latency, 2),
                },
                "query_results": config_query_results,
            })
        
        # Determine best configuration
        best_config = None
        best_mrr = -1.0
        
        for result in benchmark_results:
            if result["metrics"]["mrr"] > best_mrr:
                best_mrr = result["metrics"]["mrr"]
                best_config = result["config_name"]
        
        # Build comparison table
        comparison_table = []
        for result in benchmark_results:
            comparison_table.append({
                "config": result["config_name"],
                "recall@k": result["metrics"]["recall_at_k"],
                "mrr": result["metrics"]["mrr"],
                "avg_latency_ms": result["metrics"]["latency_avg_ms"],
            })
        
        output = {
            "results": benchmark_results,
            "comparison": {
                "best_config": best_config,
                "best_metric": "mrr",
                "table": comparison_table,
            },
            "summary": {
                "total_queries": len(queries),
                "total_configs": len(configs),
            },
        }
        
        logger.info(
            f"Benchmark completed: {len(configs)} configs, {len(queries)} queries, "
            f"best: {best_config} (MRR={best_mrr:.4f})"
        )
        
        return json.dumps(output, indent=2)
    
    _tools_registered = True
    logger.debug("Benchmark tools registered")