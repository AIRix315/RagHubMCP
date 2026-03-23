"""Debug API for Pipeline inspection.

This module provides debugging endpoints for inspecting Pipeline
intermediate states and real-time monitoring.

Reference: Docs/22-Config-API-Design.md Section 3.2.6
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/debug", tags=["debug"])


# =============================================================================
# In-memory debug store (for demo purposes)
# In production, use Redis or similar
# =============================================================================

_debug_store: dict[str, PipelineDebugInfo] = {}


# =============================================================================
# Pydantic Models
# =============================================================================


class StageDebugInfo(BaseModel):
    """Debug information for a single pipeline stage."""

    name: str = Field(..., description="Stage name")
    status: str = Field(..., description="Stage status (pending/running/completed/error)")
    input: dict[str, Any] = Field(default_factory=dict, description="Stage input data")
    output: dict[str, Any] = Field(default_factory=dict, description="Stage output data")
    latency_ms: float = Field(default=0.0, description="Stage latency in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PipelineDebugInfo(BaseModel):
    """Complete debug information for a pipeline execution."""

    query_id: str = Field(..., description="Unique query identifier")
    query: str = Field(..., description="Original query text")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    stages: list[StageDebugInfo] = Field(default_factory=list, description="Stage debug info")
    total_latency_ms: float = Field(default=0.0, description="Total pipeline latency")


class DebugQueryRequest(BaseModel):
    """Request to create a debug query."""

    query: str = Field(..., min_length=1, description="Query text")
    documents: list[str] = Field(default_factory=list, description="Documents to process")
    config: dict[str, Any] = Field(default_factory=dict, description="Pipeline config override")


class DebugQueryResponse(BaseModel):
    """Response for debug query creation."""

    query_id: str = Field(..., description="Unique query identifier")
    message: str = Field(default="Debug query created")


# =============================================================================
# API Endpoints
# =============================================================================


@router.post("/pipeline", response_model=DebugQueryResponse)
async def create_debug_query(request: DebugQueryRequest) -> DebugQueryResponse:
    """Create a new debug query for pipeline inspection.

    This creates a query ID that can be used to retrieve intermediate
    states and monitor execution progress.

    Args:
        request: Debug query request with query text and optional documents

    Returns:
        DebugQueryResponse with the query ID
    """
    query_id = str(uuid.uuid4())[:8]

    # Create initial debug info
    debug_info = PipelineDebugInfo(
        query_id=query_id,
        query=request.query,
        stages=[
            StageDebugInfo(
                name="retrieval",
                status="pending",
                input={"query": request.query},
                output={},
                metadata={},
            ),
            StageDebugInfo(
                name="rerank",
                status="pending",
                input={},
                output={},
                metadata={},
            ),
            StageDebugInfo(
                name="context",
                status="pending",
                input={},
                output={},
                metadata={},
            ),
        ],
    )

    # Store for retrieval
    _debug_store[query_id] = debug_info

    return DebugQueryResponse(query_id=query_id, message="Debug query created")


@router.get("/pipeline/{query_id}", response_model=PipelineDebugInfo)
async def get_pipeline_debug(query_id: str) -> PipelineDebugInfo:
    """Get debug information for a pipeline execution.

    Args:
        query_id: The query identifier

    Returns:
        PipelineDebugInfo with all stage details

    Raises:
        HTTPException: 404 if query_id not found
    """
    from fastapi import HTTPException

    if query_id not in _debug_store:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "query_not_found",
                "message": f"Query '{query_id}' not found. Create one with POST /api/debug/pipeline",
            },
        )

    return _debug_store[query_id]


@router.post("/pipeline/{query_id}/simulate")
async def simulate_pipeline_execution(query_id: str) -> dict[str, Any]:
    """Simulate pipeline execution for demo purposes.

    This simulates a complete pipeline execution with realistic
    intermediate states for debugging and testing.

    Args:
        query_id: The query identifier

    Returns:
        Updated debug info
    """
    import random
    import time

    from fastapi import HTTPException

    if query_id not in _debug_store:
        raise HTTPException(
            status_code=404,
            detail={"error": "query_not_found", "message": f"Query '{query_id}' not found"},
        )

    debug_info = _debug_store[query_id]

    # Simulate retrieval stage
    retrieval_stage = debug_info.stages[0]
    retrieval_stage.status = "running"
    time.sleep(0.1)  # Simulate processing
    retrieval_latency = random.uniform(30, 50)
    retrieval_stage.latency_ms = retrieval_latency
    retrieval_stage.status = "completed"
    retrieval_stage.output = {
        "candidates_count": random.randint(80, 120),
        "vector_candidates": random.randint(60, 90),
        "bm25_candidates": random.randint(40, 70),
    }
    retrieval_stage.metadata = {
        "strategy": "hybrid",
        "top_k": 100,
    }

    # Simulate rerank stage
    rerank_stage = debug_info.stages[1]
    rerank_stage.status = "running"
    rerank_stage.input = {"candidates": retrieval_stage.output["candidates_count"]}
    time.sleep(0.1)
    rerank_latency = random.uniform(40, 60)
    rerank_stage.latency_ms = rerank_latency
    rerank_stage.status = "completed"
    rerank_stage.output = {
        "ranked_count": 10,
        "top_scores": [round(random.uniform(0.85, 0.95), 4) for _ in range(5)],
    }
    rerank_stage.metadata = {
        "engine": "onnx-minilm",
        "strategy": "position_aware",
        "blend_ratios": {
            "rank_1_3": [0.75, 0.25],
            "rank_4_10": [0.60, 0.40],
        },
    }

    # Simulate context stage
    context_stage = debug_info.stages[2]
    context_stage.status = "running"
    context_stage.input = {"candidates": rerank_stage.output["ranked_count"]}
    time.sleep(0.1)
    context_latency = random.uniform(10, 20)
    context_stage.latency_ms = context_latency
    context_stage.status = "completed"
    context_stage.output = {
        "final_count": 8,
        "dedup_removed": 2,
        "final_tokens": random.randint(3000, 4000),
    }
    context_stage.metadata = {
        "deduplicate": True,
        "merge_continuous": True,
        "max_tokens": 4000,
    }

    # Update total latency
    debug_info.total_latency_ms = retrieval_latency + rerank_latency + context_latency

    return {
        "query_id": query_id,
        "status": "completed",
        "total_latency_ms": debug_info.total_latency_ms,
    }


@router.delete("/pipeline/{query_id}")
async def delete_debug_query(query_id: str) -> dict[str, str]:
    """Delete a debug query from the store.

    Args:
        query_id: The query identifier

    Returns:
        Confirmation message
    """
    from fastapi import HTTPException

    if query_id not in _debug_store:
        raise HTTPException(
            status_code=404,
            detail={"error": "query_not_found", "message": f"Query '{query_id}' not found"},
        )

    del _debug_store[query_id]

    return {"message": f"Debug query '{query_id}' deleted"}
