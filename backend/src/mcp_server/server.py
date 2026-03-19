"""MCP Server implementation for RagHubMCP.

This module provides the main MCP server entry point with support for
both stdio and streamable-http transports.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("RagHubMCP")


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser.
    
    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="RagHubMCP - MCP Server for RAG operations"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol to use (default: stdio)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP transport (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP transport (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    return parser


def register_tools() -> None:
    """Register all MCP tools.
    
    Tools are registered using the @mcp.tool() decorator.
    This function imports and registers tools from the tools module.
    """
    from .tools.base import register_base_tools
    from .tools.benchmark import register_benchmark_tools
    from .tools.rerank import register_rerank_tools
    from .tools.search import register_search_tools
    from .tools.hybrid import register_hybrid_tools
    
    register_base_tools(mcp)
    register_benchmark_tools(mcp)
    register_rerank_tools(mcp)
    register_search_tools(mcp)
    register_hybrid_tools(mcp)


def main() -> None:
    """Main entry point for the MCP server.
    
    Parses command-line arguments, loads configuration, and starts
    the MCP server with the specified transport.
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.is_absolute():
        # Try relative to backend directory
        backend_path = Path(__file__).parent.parent.parent / args.config
        if backend_path.exists():
            config_path = backend_path
    
    try:
        from ..utils.config import load_config
        load_config(str(config_path))
        logger.info(f"Configuration loaded from {config_path}")
    except FileNotFoundError:
        logger.warning(f"Configuration file not found: {config_path}, using defaults")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Register tools
    register_tools()
    logger.info("MCP tools registered")
    
    # Start server with appropriate transport
    if args.transport == "stdio":
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
    else:
        logger.info(f"Starting MCP server with HTTP transport on {args.host}:{args.port}")
        # Use uvicorn directly for HTTP transport with custom host/port
        import uvicorn
        
        # Create a stateless HTTP server for production
        app = mcp.streamable_http_app(json_response=True)
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()