"""Pipeline module for RagHubMCP V2.

This module provides the unified RAG Pipeline architecture:
- RAGPipeline: Abstract base class for all pipelines
- DefaultRAGPipeline: Default implementation with HybridSearch + Rerank
- PipelineFactory: Configuration-driven pipeline creation
- PipelineOptions: Options for pipeline execution
- Retriever: Interface for document retrieval
- Reranker: Interface for document reranking
- ContextBuilder: Interface for context construction
- get_pipeline: Singleton pipeline accessor
- execute_search: Convenience function for search
- get_retrieval_multiplier: Get retrieval multiplier for profile

Reference:
- Docs/11-V2-Desing.md
- Docs/12-V2-Blueprint.md
- RULE.md
"""

from .base import RAGPipeline
from .context_builder import ContextBuilder, DefaultContextBuilder
from .default import DefaultRAGPipeline
from .factory import PROFILES, PipelineFactory
from .manager import create_pipeline, execute_search, get_pipeline, reset_pipeline
from .options import PipelineOptions
from .reranker import PipelineReranker
from .result import Document, RAGResult
from .retriever import HybridRetriever, Retriever


def get_retrieval_multiplier(profile: str = "balanced") -> float:
    """Get the retrieval multiplier for a profile.

    This is a convenience function that retrieves the multiplier from
    the profile configuration without importing the entire factory.

    Args:
        profile: Profile name (fast/balanced/accurate).

    Returns:
        Retrieval multiplier (e.g., 1.5 for fast, 2.0 for balanced, 3.0 for accurate).
    """
    profile_config = PROFILES.get(profile, PROFILES["balanced"])
    value = profile_config.get("retrieval_multiplier", 2.0)
    return float(value) if not isinstance(value, int | float) else float(value)


__all__ = [
    # Core classes
    "RAGPipeline",
    "RAGResult",
    "Document",
    "DefaultRAGPipeline",
    "PipelineFactory",
    "PipelineOptions",
    # Interfaces
    "Retriever",
    "HybridRetriever",
    "PipelineReranker",
    "ContextBuilder",
    "DefaultContextBuilder",
    # Convenience functions
    "get_pipeline",
    "reset_pipeline",
    "execute_search",
    "create_pipeline",
    "get_retrieval_multiplier",
    # Constants
    "PROFILES",
]
