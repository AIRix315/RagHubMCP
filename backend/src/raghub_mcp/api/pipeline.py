"""Pipeline Configuration API endpoints.

This module implements the Pipeline configuration API as defined in:
- Docs/22-Config-API-Design.md Section 3.2.4

Endpoints:
- GET /api/config/pipeline - Get pipeline configuration
- PUT /api/config/pipeline - Update pipeline configuration
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/config", tags=["config"])


# =============================================================================
# Pydantic Models
# =============================================================================


class RetrievalConfig(BaseModel):
    """Retrieval stage configuration."""

    top_k: int = Field(default=100, ge=1, le=500, description="Initial retrieval count")
    hybrid_enabled: bool = Field(default=True, description="Enable hybrid search")
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Vector weight in hybrid")
    bm25_enabled: bool = Field(default=True, description="Enable BM25")


class PositionAwareConfig(BaseModel):
    """Position-aware blending configuration."""

    rank_1_3: list[float] = Field(default=[0.75, 0.25], description="Weight for ranks 1-3")
    rank_4_10: list[float] = Field(default=[0.60, 0.40], description="Weight for ranks 4-10")
    rank_11_plus: list[float] = Field(default=[0.40, 0.60], description="Weight for rank 11+")


class RerankConfig(BaseModel):
    """Rerank stage configuration."""

    enabled: bool = Field(default=True, description="Enable rerank stage")
    provider: str = Field(default="onnx-minilm", description="Rerank provider name")
    top_k: int = Field(default=10, ge=1, le=100, description="Rerank result count")
    score_threshold: float = Field(default=0.3, ge=0.0, le=1.0, description="Score threshold")
    strategy: str = Field(default="standard", description="Rank strategy")
    position_aware: PositionAwareConfig = Field(
        default_factory=PositionAwareConfig, description="Position-aware config"
    )


class ContextConfig(BaseModel):
    """Context builder stage configuration."""

    enabled: bool = Field(default=True, description="Enable context builder")
    max_tokens: int = Field(default=4000, ge=500, le=16000, description="Max tokens")
    deduplicate: bool = Field(default=True, description="Enable deduplication")
    deduplication_threshold: float = Field(
        default=0.9, ge=0.5, le=1.0, description="Dedup similarity threshold"
    )
    merge_continuous: bool = Field(default=True, description="Merge continuous chunks")
    reordering: str = Field(default="relevance", description="Reordering strategy")


class PipelineConfigModel(BaseModel):
    """Complete pipeline configuration."""

    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    rerank: RerankConfig = Field(default_factory=RerankConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)


class PipelineConfigResponse(BaseModel):
    """Pipeline configuration response."""

    pipeline: PipelineConfigModel
    message: str = Field(default="Pipeline configuration loaded")


class PipelineConfigUpdateResponse(BaseModel):
    """Pipeline configuration update response."""

    pipeline: PipelineConfigModel
    message: str = Field(default="Pipeline configuration updated")
    requires_restart: bool = Field(default=False, description="Whether restart is needed")


# =============================================================================
# API Endpoints
# =============================================================================


@router.get("/pipeline", response_model=PipelineConfigResponse)
async def get_pipeline_config() -> PipelineConfigResponse:
    """Get current pipeline configuration.

    Returns:
        PipelineConfigResponse with current configuration.
    """
    # Return default configuration
    return PipelineConfigResponse(
        pipeline=PipelineConfigModel(
            retrieval=RetrievalConfig(),
            rerank=RerankConfig(),
            context=ContextConfig(),
        )
    )


@router.put("/pipeline", response_model=PipelineConfigUpdateResponse)
async def update_pipeline_config(config: PipelineConfigModel) -> PipelineConfigUpdateResponse:
    """Update pipeline configuration.

    Args:
        config: New pipeline configuration

    Returns:
        PipelineConfigUpdateResponse with updated configuration.
    """
    # Validate rank strategy
    valid_strategies = ["standard", "position_aware", "diversity"]
    if config.rerank.strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_strategy",
                "message": f"Invalid rank strategy. Valid options: {valid_strategies}",
            },
        )

    # Validate reordering
    valid_reordering = ["relevance", "chronological", "original"]
    if config.context.reordering not in valid_reordering:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_reordering",
                "message": f"Invalid reordering. Valid options: {valid_reordering}",
            },
        )

    return PipelineConfigUpdateResponse(
        pipeline=config,
        message="Pipeline configuration updated successfully",
        requires_restart=False,
    )
