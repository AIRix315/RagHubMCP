"""FlashRank rerank provider implementation.

This module provides a reranking provider using the FlashRank library,
which uses ONNX Runtime for fast, CPU-based reranking without requiring
PyTorch or GPU.

FlashRank models available:
- ms-marco-TinyBERT-L-2-v2 (default, ~4MB, fastest)
- ms-marco-MiniLM-L-12-v2 (~34MB, best cross-encoder)
- rank-T5-flan (~110MB, best zero-shot)
- ms-marco-MultiBERT-L-12 (~150MB, multilingual)

Reference: https://github.com/PrithivirajDamodaran/FlashRank
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from flashrank import Ranker, RerankRequest

from ..base import ProviderCategory
from ..registry import registry
from .base import BaseRerankProvider, RerankResult


# Default cache directory for FlashRank models
DEFAULT_CACHE_DIR = "./data/flashrank_cache"


@registry.register(ProviderCategory.RERANK, "flashrank")
class FlashRankRerankProvider(BaseRerankProvider):
    """FlashRank-based reranking provider.
    
    Uses FlashRank library for efficient, CPU-based document reranking.
    Models are automatically downloaded and cached locally.
    
    Attributes:
        NAME: Provider type identifier ("flashrank")
        model: FlashRank model name
        cache_dir: Directory for model caching
        max_length: Maximum token length for the model
    
    Example:
        >>> provider = FlashRankRerankProvider(
        ...     model="ms-marco-TinyBERT-L-2-v2",
        ...     cache_dir="./data/cache"
        ... )
        >>> results = provider.rerank(
        ...     query="What is machine learning?",
        ...     documents=["ML is a subset of AI.", "Python is a language."],
        ...     top_k=2
        ... )
    """
    
    NAME = "flashrank"
    
    # Class-level cache for Ranker instances (singleton per model config)
    _ranker_cache: dict[str, Ranker] = {}
    
    def __init__(
        self,
        model: str = "ms-marco-TinyBERT-L-2-v2",
        cache_dir: str = DEFAULT_CACHE_DIR,
        max_length: int = 512,
    ) -> None:
        """Initialize FlashRank reranking provider.
        
        Args:
            model: FlashRank model name. Options:
                - "ms-marco-TinyBERT-L-2-v2" (default, ~4MB)
                - "ms-marco-MiniLM-L-12-v2" (~34MB, best accuracy)
                - "rank-T5-flan" (~110MB, best zero-shot)
                - "ms-marco-MultiBERT-L-12" (~150MB, multilingual)
            cache_dir: Directory for caching downloaded models.
                       Default: "./data/flashrank_cache"
            max_length: Maximum token length. Default: 512
        """
        self._model = model
        self._cache_dir = cache_dir
        self._max_length = max_length
        self._ranker: Ranker | None = None
    
    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model
    
    @property
    def cache_dir(self) -> str:
        """Get the cache directory."""
        return self._cache_dir
    
    @property
    def max_length(self) -> int:
        """Get the maximum token length."""
        return self._max_length
    
    def _get_ranker(self) -> Ranker:
        """Get or create a cached Ranker instance.
        
        Uses a class-level cache to avoid reloading models.
        The cache key is based on model name and cache directory.
        
        Returns:
            Cached or newly created Ranker instance
        """
        # Create cache key from model and cache_dir
        cache_key = f"{self._model}:{self._cache_dir}"
        
        if cache_key not in self._ranker_cache:
            # Ensure cache directory exists
            Path(self._cache_dir).mkdir(parents=True, exist_ok=True)
            
            # Create and cache the ranker
            self._ranker_cache[cache_key] = Ranker(
                model_name=self._model,
                cache_dir=self._cache_dir,
                max_length=self._max_length,
            )
        
        return self._ranker_cache[cache_key]
    
    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Re-rank documents by relevance to query.
        
        Args:
            query: The search query
            documents: List of document texts to re-rank
            top_k: Number of top results to return
            
        Returns:
            List of RerankResult sorted by score (descending).
            Length is min(top_k, len(documents)).
            
        Note:
            Results are sorted by score in descending order
            (highest relevance first).
        """
        # Handle empty documents
        if not documents:
            return []
        
        # Prepare passages for FlashRank
        # FlashRank expects passages as list of dicts with "id", "text"
        passages = [
            {"id": str(i), "text": doc}
            for i, doc in enumerate(documents)
        ]
        
        # Create rerank request
        request = RerankRequest(query=query, passages=passages)
        
        # Get ranker and perform reranking
        ranker = self._get_ranker()
        ranked_results = ranker.rerank(request)
        
        # Convert FlashRank results to RerankResult
        # FlashRank returns: [{"id": str, "text": str, "score": float}, ...]
        results: list[RerankResult] = []
        for item in ranked_results[:top_k]:
            # Convert id back to int (original index)
            original_index = int(item["id"])
            score = float(item["score"])
            text = item["text"]
            
            results.append(RerankResult(
                index=original_index,
                score=score,
                text=text,
            ))
        
        return results
    
    @classmethod
    def from_config(cls, config: dict[str, Any]) -> FlashRankRerankProvider:
        """Create an instance from configuration dictionary.
        
        Args:
            config: Configuration from config.yaml providers section.
                   Expected keys:
                   - model: FlashRank model name (required)
                   - cache_dir: Cache directory (optional)
                   - max_length: Max token length (optional)
            
        Returns:
            New FlashRankRerankProvider instance
        """
        return cls(
            model=config.get("model", "ms-marco-TinyBERT-L-2-v2"),
            cache_dir=config.get("cache_dir", DEFAULT_CACHE_DIR),
            max_length=config.get("max_length", 512),
        )
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear the class-level ranker cache.
        
        Useful for testing or when models need to be reloaded.
        """
        cls._ranker_cache.clear()