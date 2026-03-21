"""Pipeline Factory for configuration-driven creation.

This module provides the PipelineFactory class that creates
pipeline instances based on configuration.

Reference:
- Docs/11-V2-Desing.md (Section 10)
- Docs/12-V2-Blueprint.md (Module 1.3)
- RULE.md (RULE-4: 所有能力必须可配置)
"""

from __future__ import annotations

from typing import Any, Literal

from src.utils.config import PipelineProfileConfig
from .base import RAGPipeline
from .default import DefaultRAGPipeline
from .retriever import Retriever, HybridRetriever, VectorRetriever
from .reranker import Reranker, PipelineReranker, NoOpReranker
from .context_builder import ContextBuilder, DefaultContextBuilder


# Profile type for type hints
ProfileName = Literal["fast", "balanced", "accurate"]


# Profile configurations
# Each profile defines:
# - rerank: Whether to enable reranking
# - topK: Number of final results to return
# - retrieval_multiplier: Multiplier for initial retrieval (retrieval_count = topK * multiplier)
# - alpha: Weight for vector search in hybrid retrieval
# - beta: Weight for BM25 search in hybrid retrieval
# - merge_consecutive: Whether to merge consecutive chunks from same source
# - multi_query: (future) Generate multiple query variations
# Using PipelineProfileConfig for type safety and validation
PROFILES = {
    "fast": PipelineProfileConfig(
        rerank=False,
        top_k=3,
        retrieval_multiplier=1.5,
        alpha=0.5,
        beta=0.5,
        rrf_k=60,
    ),
    "balanced": PipelineProfileConfig(
        rerank=True,
        top_k=5,
        retrieval_multiplier=2.0,
        alpha=0.5,
        beta=0.5,
        rrf_k=60,
    ),
    "accurate": PipelineProfileConfig(
        rerank=True,
        top_k=10,
        retrieval_multiplier=3.0,
        alpha=0.6,
        beta=0.4,
        rrf_k=60,
    ),
}


class PipelineFactory:
    """Factory for creating pipeline instances.
    
    This factory creates pipeline instances based on configuration,
    supporting:
    - Profile-based configuration (fast/balanced/accurate)
    - Custom retriever/reranker options
    - Hot reloading of configurations
    
    Example:
        >>> config = {"profile": "balanced"}
        >>> pipeline = PipelineFactory.create(config)
        >>> result = await pipeline.run("query", {"topK": 5})
    """
    
    @staticmethod
    def create(config: dict[str, Any]) -> RAGPipeline:
        """Create a pipeline from configuration.
        
        Args:
            config: Configuration dictionary:
                - type: Pipeline type (default: "default")
                - profile: Profile name (fast/balanced/accurate)
                - retriever: Retriever configuration
                - rerank: Rerank configuration
                - context_builder: Context builder configuration
                
        Returns:
            Configured RAGPipeline instance.
        """
        pipeline_type = config.get("type", "default")
        
        if pipeline_type == "default":
            return PipelineFactory._create_default_pipeline(config)
        
        raise ValueError(f"Unknown pipeline type: {pipeline_type}")
    
    @staticmethod
    def _create_default_pipeline(config: dict[str, Any]) -> DefaultRAGPipeline:
        """Create a default pipeline.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            DefaultRAGPipeline instance.
        """
        # Get profile or use default
        profile_name = config.get("profile", "balanced")
        profile_config = PROFILES.get(profile_name, PROFILES["balanced"])
        
        # Create working config from profile defaults (use .model_dump() for Pydantic v2)
        profile_dict: dict[str, Any] = {
            "rerank": profile_config.rerank,
            "topK": profile_config.top_k,
            "retrieval_multiplier": profile_config.retrieval_multiplier,
            "alpha": profile_config.alpha,
            "beta": profile_config.beta,
            "rrf_k": profile_config.rrf_k,
        }
        
        # Merge custom config (custom values override profile defaults)
        if "rerank" in config:
            profile_dict["rerank"] = config["rerank"]
        if "topK" in config:
            profile_dict["topK"] = config["topK"]
        if "retrieval_multiplier" in config:
            profile_dict["retrieval_multiplier"] = config["retrieval_multiplier"]
        if "alpha" in config:
            profile_dict["alpha"] = config["alpha"]
        if "beta" in config:
            profile_dict["beta"] = config["beta"]
        
        # Create retriever with profile settings
        retriever_config = config.get("retriever", {})
        retriever = PipelineFactory._create_retriever(
            retriever_config,
            profile_dict,
        )
        
        # Create reranker
        reranker: Reranker | None = None
        if profile_dict.get("rerank", True):
            reranker_config = config.get("rerank_config", {})
            reranker = PipelineFactory._create_reranker(
                reranker_config,
                profile_dict,
            )
        
        # Create context builder with profile settings
        builder_config = config.get("context_builder", {})
        context_builder = PipelineFactory._create_context_builder(
            builder_config,
            profile_dict,
        )
        
        # Create pipeline
        pipeline = DefaultRAGPipeline(
            retriever=retriever,
            reranker=reranker,
            context_builder=context_builder,
            default_top_k=int(profile_dict.get("topK", 5)),
            default_rerank=bool(profile_dict.get("rerank", True)),
        )
        
        # Store profile settings for retrieval multiplier
        pipeline._retrieval_multiplier = float(profile_dict.get("retrieval_multiplier", 2.0))
        
        return pipeline
    
    @staticmethod
    def _create_retriever(
        config: dict[str, Any],
        profile: dict[str, Any],
    ) -> Retriever:
        """Create a retriever from configuration.
        
        Args:
            config: Retriever configuration.
            profile: Profile configuration.
            
        Returns:
            Retriever instance.
        """
        retriever_type = config.get("type", "hybrid")
        
        if retriever_type == "hybrid":
            return HybridRetriever(
                alpha=config.get("alpha", profile.get("alpha", 0.5)),
                beta=config.get("beta", profile.get("beta", 0.5)),
                rrf_k=config.get("rrf_k", 60),
            )
        elif retriever_type == "vector":
            return VectorRetriever(
                collection=config.get("collection", "default"),
            )
        
        raise ValueError(f"Unknown retriever type: {retriever_type}")
    
    @staticmethod
    def _create_reranker(
        config: dict[str, Any],
        profile: dict[str, Any],
    ) -> Reranker:
        """Create a reranker from configuration.
        
        Args:
            config: Reranker configuration.
            profile: Profile configuration.
            
        Returns:
            Reranker instance.
        """
        reranker_type = config.get("type", "flashrank")
        
        if reranker_type == "flashrank":
            return PipelineReranker(
                model=config.get("model", "ms-marco-TinyBERT-L-2-v2"),
                top_k=config.get("top_k", profile.get("topK", 5)),
            )
        elif reranker_type == "none" or reranker_type == "disabled":
            return NoOpReranker()
        
        raise ValueError(f"Unknown reranker type: {reranker_type}")
    
    @staticmethod
    def _create_context_builder(
        config: dict[str, Any],
        profile: dict[str, Any],
    ) -> ContextBuilder:
        """Create a context builder from configuration.
        
        Args:
            config: Context builder configuration.
            profile: Profile configuration for default options.
            
        Returns:
            ContextBuilder instance.
        """
        builder_type = config.get("type", "default")
        
        if builder_type == "default":
            # Use profile settings for context builder
            merge_consecutive = config.get(
                "merge_consecutive",
                profile.get("merge_consecutive", False)
            )
            return DefaultContextBuilder()
        
        raise ValueError(f"Unknown context builder type: {builder_type}")
    
    @staticmethod
    def get_profile(name: str) -> dict[str, Any]:
        """Get profile configuration by name.
        
        Args:
            name: Profile name (fast/balanced/accurate).
            
        Returns:
            Profile configuration dictionary.
        """
        profile = PROFILES.get(name, PROFILES["balanced"])
        # Convert PipelineProfileConfig to dict for backward compatibility
        return {
            "rerank": profile.rerank,
            "topK": profile.top_k,
            "retrieval_multiplier": profile.retrieval_multiplier,
            "alpha": profile.alpha,
            "beta": profile.beta,
            "rrf_k": profile.rrf_k,
        }
    
    @staticmethod
    def list_profiles() -> list[str]:
        """List available profile names.
        
        Returns:
            List of profile names.
        """
        return list(PROFILES.keys())
    
    @staticmethod
    def get_retrieval_count(profile: str, top_k: int) -> int:
        """Calculate the number of documents to retrieve based on profile.
        
        This replaces the hardcoded `top_k * 2` with a configurable multiplier.
        
        Args:
            profile: Profile name (fast/balanced/accurate).
            top_k: Number of final results desired.
            
        Returns:
            Number of documents to retrieve initially.
        """
        profile_config = PROFILES.get(profile, PROFILES["balanced"])
        multiplier = profile_config.retrieval_multiplier
        return int(top_k * multiplier)


def get_pipeline(profile: str = "balanced") -> RAGPipeline:
    """Get a pipeline instance with the specified profile.
    
    This is a convenience function for quick access to pipelines.
    
    Args:
        profile: Profile name (fast/balanced/accurate).
        
    Returns:
        RAGPipeline instance.
    """
    return PipelineFactory.create({"profile": profile})