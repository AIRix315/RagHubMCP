"""Pipeline Factory for configuration-driven creation.

This module provides the PipelineFactory class that creates
pipeline instances based on configuration.

Reference:
- Docs/11-V2-Desing.md (Section 10)
- Docs/12-V2-Blueprint.md (Module 1.3)
- RULE.md (RULE-4: 所有能力必须可配置)
"""

from __future__ import annotations

from typing import Any

from .base import RAGPipeline
from .default import DefaultRAGPipeline
from .retriever import Retriever, HybridRetriever, VectorRetriever
from .reranker import Reranker, PipelineReranker, NoOpReranker
from .context_builder import ContextBuilder, DefaultContextBuilder


# Profile configurations
PROFILES = {
    "fast": {
        "rerank": False,
        "topK": 3,
        "alpha": 0.5,
        "beta": 0.5,
    },
    "balanced": {
        "rerank": True,
        "topK": 5,
        "alpha": 0.5,
        "beta": 0.5,
    },
    "accurate": {
        "rerank": True,
        "topK": 10,
        "alpha": 0.6,
        "beta": 0.4,
        "multi_query": True,
    },
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
        profile = PROFILES.get(profile_name, PROFILES["balanced"])
        
        # Merge with custom config
        if "rerank" in config:
            profile["rerank"] = config["rerank"]
        if "topK" in config:
            profile["topK"] = config["topK"]
        
        # Create retriever
        retriever_config = config.get("retriever", {})
        retriever = PipelineFactory._create_retriever(
            retriever_config,
            profile,
        )
        
        # Create reranker
        reranker: Reranker | None = None
        if profile.get("rerank", True):
            reranker_config = config.get("rerank_config", {})
            reranker = PipelineFactory._create_reranker(
                reranker_config,
                profile,
            )
        
        # Create context builder
        builder_config = config.get("context_builder", {})
        context_builder = PipelineFactory._create_context_builder(builder_config)
        
        # Create pipeline
        pipeline = DefaultRAGPipeline(
            retriever=retriever,
            reranker=reranker,
            context_builder=context_builder,
            default_top_k=int(profile.get("topK", 5)),
            default_rerank=bool(profile.get("rerank", True)),
        )
        
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
    def _create_context_builder(config: dict[str, Any]) -> ContextBuilder:
        """Create a context builder from configuration.
        
        Args:
            config: Context builder configuration.
            
        Returns:
            ContextBuilder instance.
        """
        builder_type = config.get("type", "default")
        
        if builder_type == "default":
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
        return PROFILES.get(name, PROFILES["balanced"])
    
    @staticmethod
    def list_profiles() -> list[str]:
        """List available profile names.
        
        Returns:
            List of profile names.
        """
        return list(PROFILES.keys())


def get_pipeline(profile: str = "balanced") -> RAGPipeline:
    """Get a pipeline instance with the specified profile.
    
    This is a convenience function for quick access to pipelines.
    
    Args:
        profile: Profile name (fast/balanced/accurate).
        
    Returns:
        RAGPipeline instance.
    """
    return PipelineFactory.create({"profile": profile})