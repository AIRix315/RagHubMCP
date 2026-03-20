"""FastAPI application entry point for RagHubMCP.

This module creates and configures the FastAPI application,
mounting both the REST API and MCP Server.
"""

from __future__ import annotations

import argparse
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.router import api_router
from src.api.websocket import manager as ws_manager
from src.utils.config import get_config, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting RagHubMCP server...")

    # Initialize providers (warm up)
    try:
        from src.providers.factory import factory
        config = get_config()

        # Pre-load default providers
        if config.providers.embedding.default:
            factory.get_embedding_provider()
            logger.info(f"Initialized embedding provider: {config.providers.embedding.default}")

        if config.providers.rerank.default:
            factory.get_rerank_provider()
            logger.info(f"Initialized rerank provider: {config.providers.rerank.default}")

    except Exception as e:
        logger.warning(f"Could not initialize providers: {e}")

    yield

    # Shutdown
    logger.info("Shutting down RagHubMCP server...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="RagHubMCP",
        description="通用代码 RAG 中枢 - REST API + MCP Server",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS from config
    config = get_config()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )
    logger.info(f"CORS configured with origins: {config.cors.origins}")

    # Add exception handler for consistent error responses
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Global exception handler for consistent error responses.
        
        TC-1.15.7: Error response format is unified.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": str(exc),
                "detail": None,
            }
        )

    # Include API router
    app.include_router(api_router)

    # Add health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "RagHubMCP",
            "version": "0.1.0",
        }

    # WebSocket endpoint for progress updates
    @app.websocket("/ws/progress/{task_id}")
    async def websocket_progress(websocket: WebSocket, task_id: str):
        """WebSocket endpoint for real-time progress updates.

        Args:
            websocket: WebSocket connection.
            task_id: Task ID to subscribe to.
        """
        await ws_manager.connect(websocket, task_id)
        try:
            while True:
                # Wait for any message from client (heartbeat or close)
                data = await websocket.receive_text()

                # Handle heartbeat
                if data == "pong" or data == "ping":
                    await ws_manager.send_heartbeat(websocket)
                else:
                    # Echo back unknown messages as heartbeat
                    await ws_manager.send_heartbeat(websocket)

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for task: {task_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await ws_manager.disconnect(websocket)

    # Add root endpoint
    @app.get("/", tags=["root"])
    async def root() -> dict[str, Any]:
        """Root endpoint with API information."""
        return {
            "name": "RagHubMCP",
            "version": "0.1.0",
            "description": "通用代码 RAG 中枢",
            "docs": "/docs",
            "api": "/api",
            "health": "/health",
            "websocket": "/ws/progress/{task_id}",
        }

    return app


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="RagHubMCP - REST API + MCP Server for RAG operations"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    return parser


def main() -> None:
    """Main entry point for the server."""
    parser = create_parser()
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Try relative to backend directory
        backend_path = Path(__file__).parent.parent / args.config
        if backend_path.exists():
            config_path = backend_path

    try:
        load_config(str(config_path))
        logger.info(f"Configuration loaded from {config_path}")
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}, using defaults")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Get server config
    config = get_config()
    host = args.host or config.server.host
    port = args.port or config.server.port

    # Create app
    app = create_app()

    # Start server
    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "main:app" if args.reload else app,
        host=host,
        port=port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
    )


# Create app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    main()
