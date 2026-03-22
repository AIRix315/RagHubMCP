"""RerankEngine - Core reranking engine.

This module provides the main RerankEngine class that assembles
all components (Scorer, PostProcessors, RankStrategy) into a
complete reranking pipeline.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from .core.processor import BasePostProcessor
from .core.ranker import BaseRankStrategy, ScoredDocument
from .core.scorer import BaseScorer
from .models import RerankContext, RerankRequest, RerankResult

logger = logging.getLogger(__name__)


@dataclass
class RerankConfig:
    """RerankEngine configuration.

    Attributes:
        scorer_type: Type of scorer ("onnx", "api", "vector").
        scorer_config: Configuration for the scorer.
        rank_strategy: Name of rank strategy ("standard", "diversity").
        rank_strategy_config: Configuration for rank strategy.
        post_processors: List of post-processor configs.
        enable_profiling: Enable timing/profiling.
    """

    scorer_type: str = "onnx"
    scorer_config: dict[str, Any] = field(default_factory=dict)
    rank_strategy: str = "standard"
    rank_strategy_config: dict[str, Any] = field(default_factory=dict)
    post_processors: list[dict[str, Any]] = field(default_factory=list)
    enable_profiling: bool = False


class RerankEngine:
    """Main reranking engine.

    Assembles scoring, post-processing, and ranking into a complete
    pipeline with full observability.

    The pipeline is:
        1. Extract documents from request
        2. Score documents with Scorer
        3. Apply post-processors (threshold, normalize, etc.)
        4. Rank with RankStrategy
        5. Build and return results

    Example:
        >>> config = RerankConfig(
        ...     scorer_type="onnx",
        ...     scorer_config={"model_path": "./model.onnx", ...},
        ... )
        >>> engine = RerankEngine(config)
        >>> results = engine.rerank(request)
    """

    def __init__(self, config: RerankConfig) -> None:
        """Initialize RerankEngine.

        Args:
            config: Engine configuration.
        """
        self.config = config

        # Initialize components (lazy for scorers)
        self._scorer: BaseScorer | None = None
        self._rank_strategy: BaseRankStrategy | None = None
        self._post_processors: list[BasePostProcessor] = []

        logger.info(
            f"RerankEngine initialized with "
            f"scorer_type={config.scorer_type}, "
            f"strategy={config.rank_strategy}"
        )

    @property
    def scorer(self) -> BaseScorer:
        """Get scorer (lazy initialization)."""
        if self._scorer is None:
            self._scorer = self._create_scorer()
        return self._scorer

    @property
    def rank_strategy(self) -> BaseRankStrategy:
        """Get rank strategy (lazy initialization)."""
        if self._rank_strategy is None:
            self._rank_strategy = self._create_rank_strategy()
        return self._rank_strategy

    @property
    def post_processors(self) -> list[BasePostProcessor]:
        """Get post processors (lazy initialization)."""
        if not self._post_processors and self.config.post_processors:
            self._post_processors = self._create_post_processors()
        return self._post_processors

    def _create_scorer(self) -> BaseScorer:
        """Create scorer based on configuration."""
        from .scorers.onnx_scorer import ONNXScorer

        if self.config.scorer_type == "onnx":
            return ONNXScorer(**self.config.scorer_config)
        else:
            raise ValueError(f"Unknown scorer type: {self.config.scorer_type}")

    def _create_rank_strategy(self) -> BaseRankStrategy:
        """Create rank strategy based on configuration."""
        from .strategies.diversity import DiversityRankStrategy
        from .strategies.standard import StandardRankStrategy

        if self.config.rank_strategy == "standard":
            return StandardRankStrategy()
        elif self.config.rank_strategy == "diversity":
            return DiversityRankStrategy(
                **self.config.rank_strategy_config
            )
        else:
            raise ValueError(f"Unknown rank strategy: {self.config.rank_strategy}")

    def _create_post_processors(self) -> list[BasePostProcessor]:
        """Create post processors based on configuration."""
        from .processors.normalize import NormalizeProcessor
        from .processors.threshold import ThresholdProcessor

        processors = []
        for proc_config in self.config.post_processors:
            proc_type = proc_config.get("type", "")
            proc_params = proc_config.get("config", {})

            if proc_type == "threshold":
                processors.append(ThresholdProcessor(**proc_params))
            elif proc_type == "normalize":
                processors.append(NormalizeProcessor(**proc_params))
            else:
                logger.warning(f"Unknown processor type: {proc_type}")

        return processors

    def rerank(self, request: RerankRequest) -> list[RerankResult]:
        """Execute rerank pipeline.

        Args:
            request: Rerank request with query and documents.

        Returns:
            List of RerankResult sorted by score (highest first).
        """
        context = RerankContext(request=request)
        start_time = time.time()

        try:
            # 1. Extract documents
            documents = request.documents
            texts = [doc.get("text", "") for doc in documents]
            doc_ids = [doc.get("id", str(i)) for i, doc in enumerate(documents)]
            metadata_list = [doc.get("metadata", {}) for doc in documents]

            if not documents:
                return []

            # 2. Score
            logger.debug(f"Scoring {len(texts)} documents")
            raw_scores = self.scorer.compute_scores(request.query, texts)
            context.intermediate_scores["raw"] = raw_scores
            context.add_step("scoring", {"scorer": self.scorer.name})

            # 3. Post-process
            processed_scores = raw_scores.copy()
            for processor in self.post_processors:
                logger.debug(f"Applying processor: {processor.name}")
                processed_scores = processor.process(
                    processed_scores, texts, **request.scorer_config
                )
                context.intermediate_scores[processor.name] = processed_scores

            context.add_step("post_processing")

            # 4. Build ScoredDocuments
            scored_docs = [
                ScoredDocument(
                    document_id=doc_ids[i],
                    text=texts[i],
                    score=float(processed_scores[i]),
                    metadata=metadata_list[i],
                    original_index=i,
                )
                for i in range(len(texts))
            ]

            # 5. Rank
            logger.debug(f"Ranking {len(scored_docs)} documents")
            ranked = self.rank_strategy.rank(
                scored_docs,
                top_k=request.top_k,
                **request.rank_strategy_config
            )
            context.add_step("ranking", {"strategy": self.rank_strategy.name})

            # 6. Build results
            results = [
                RerankResult(
                    document_id=doc.document_id,
                    text=doc.text,
                    score=doc.score,
                    rank=i + 1,
                    metadata=doc.metadata,
                    original_index=doc.original_index,
                    processing_info={
                        "raw_score": float(raw_scores[doc.original_index]),
                        "processors_applied": [p.name for p in self.post_processors],
                    },
                )
                for i, doc in enumerate(ranked)
            ]

            # Record timing
            context.latency_ms = (time.time() - start_time) * 1000
            context.scorer_name = self.scorer.name
            context.rank_strategy_name = self.rank_strategy.name

            logger.info(
                f"Rerank completed: {len(results)} results in "
                f"{context.latency_ms:.2f}ms"
            )

            return results

        except Exception as e:
            logger.error(f"Rerank failed: {e}")
            raise

    def get_config(self) -> dict[str, Any]:
        """Get engine configuration."""
        return {
            "scorer": {
                "type": self.config.scorer_type,
                "name": self.scorer.name,
                "supports_batch": self.scorer.supports_batch,
            },
            "rank_strategy": {
                "type": self.config.rank_strategy,
                "name": self.rank_strategy.name,
            },
            "post_processors": [
                {"type": p.name} for p in self.post_processors
            ],
        }