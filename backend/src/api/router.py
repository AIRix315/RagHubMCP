"""API Router configuration.

This module combines all API routers into a single router for mounting.
"""

from fastapi import APIRouter

from .benchmark import router as benchmark_router
from .config import router as config_router
from .index import router as index_router
from .search import router as search_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all sub-routers
api_router.include_router(config_router)
api_router.include_router(index_router)
api_router.include_router(search_router)
api_router.include_router(benchmark_router)


# Add a root endpoint for API health check
@api_router.get("", tags=["root"])
async def api_root() -> dict:
    """API root endpoint.

    Returns basic API information.
    """
    return {
        "name": "RagHubMCP API",
        "version": "0.1.0",
        "endpoints": [
            "/api/config",
            "/api/index",
            "/api/index/status/{task_id}",
            "/api/search",
            "/api/search/collections",
            "/api/benchmark",
        ],
    }
