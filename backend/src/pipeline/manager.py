"""Pipeline singleton manager.

This module provides a singleton manager for RAG pipelines,
allowing easy access from API and MCP layers.

Reference:
- Docs/11-V2-Desing.md (RULE-1: Pipeline是唯一执行入口)
- Docs/12-V2-Blueprint.md (Module 1.3)
- RULE.md (RULE-1: Pipeline是唯一执行入口)
"""

from __future__ import annotations

import logging
from typing import Any

from .base import RAGPipeline
from .default import DefaultRAGPipeline
from .factory import PipelineFactory
from .result import RAGResult

logger = logging.getLogger(__name__)

# Singleton instance
_pipeline: RAGPipeline | None = None
_current_profile: str = "balanced"


def get_pipeline(profile: str = "balanced") -> RAGPipeline:
    """Get the singleton pipeline instance.
    
    This is the recommended way to obtain a pipeline instance.
    The pipeline is created lazily and cached for reuse.
    
    Args:
        profile: Pipeline profile (fast/balanced/accurate).
            - fast: No reranking, top_k=3
            - balanced: Reranking enabled, top_k=5 (default)
            - accurate: Reranking enabled, top_k=10, multi-query
            
    Returns:
        RAGPipeline singleton instance.
        
    Example:
        >>> from pipeline import get_pipeline
        >>> pipeline = get_pipeline("balanced")
        >>> result = await pipeline.run("What is AI?", {"collection": "docs"})
    """
    global _pipeline, _current_profile
    
    if _pipeline is None or profile != _current_profile:
        logger.info(f"Creating pipeline with profile: {profile}")
        _pipeline = PipelineFactory.create({"profile": profile})
        _current_profile = profile
    
    return _pipeline


def reset_pipeline() -> None:
    """Reset the singleton pipeline (for testing).
    
    This clears the cached pipeline instance, forcing a new
    pipeline to be created on the next get_pipeline() call.
    """
    global _pipeline, _current_profile
    _pipeline = None
    _current_profile = "balanced"
    logger.debug("Pipeline singleton reset")


async def execute_search(
    query: str,
    options: dict[str, Any] | None = None,
) -> RAGResult:
    """Convenience function to execute a search through the pipeline.
    
    This is the main entry point for all RAG operations. All search
    requests should go through this function to ensure consistent
    behavior and quality.
    
    Args:
        query: Search query text.
        options: Pipeline options:
            - collection: Collection name (default: "default")
            - topK: Number of results (default: 5)
            - rerank: Whether to rerank (default: True)
            - where: Metadata filter
            - profile: Pipeline profile (default: "balanced")
            
    Returns:
        RAGResult with retrieved documents.
        
    Raises:
        ValueError: If query is empty or invalid.
        RuntimeError: If pipeline execution fails.
        
    Example:
        >>> from pipeline import execute_search
        >>> result = await execute_search(
        ...     "What is machine learning?",
        ...     {"collection": "docs", "topK": 5}
        ... )
        >>> print(result.documents[0].text)
    """
    if not query or not isinstance(query, str):
        raise ValueError("Query must be a non-empty string")
    
    pipeline = get_pipeline()
    return await pipeline.run(query, options)


def create_pipeline(config: dict[str, Any]) -> RAGPipeline:
    """Create a new pipeline instance with custom configuration.
    
    Unlike get_pipeline(), this always creates a new instance.
    Use this when you need multiple pipelines with different configurations.
    
    Args:
        config: Pipeline configuration:
            - profile: Profile name (fast/balanced/accurate)
            - rerank: Whether to enable reranking
            - topK: Default number of results
            - retriever: Retriever configuration
            - reranker: Reranker configuration
            
    Returns:
        New RAGPipeline instance.
        
    Example:
        >>> from pipeline import create_pipeline
        >>> pipeline = create_pipeline({
        ...     "profile": "accurate",
        ...     "rerank": True,
        ...     "topK": 10,
        ... })
    """
    return PipelineFactory.create(config)