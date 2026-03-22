"""
RagHubMCP Python Entry Point for Go Wrapper

This module provides the startup logic for the Python backend
when called by the Go wrapper.

Usage:
    python -m rhm_app --service rest [--port 8818]
    python -m rhm_app --service mcp [--port 8819]
"""

import argparse
import sys
from pathlib import Path


def start_rest_api(port: int = 8818, host: str = "127.0.0.1"):
    """Start the REST API service."""
    import uvicorn
    from src.main import create_app
    
    print(f"[RHM-Python] Starting REST API on {host}:{port}")
    
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


def start_mcp_http(port: int = 8819, host: str = "127.0.0.1"):
    """Start the MCP HTTP service."""
    import uvicorn
    from src.mcp_server.server import mcp
    
    print(f"[RHM-Python] Starting MCP HTTP on {host}:{port}")
    
    # Create streamable HTTP app
    app = mcp.streamable_http_app(json_response=True)
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


def run_index(path: str, **kwargs):
    """Run index command."""
    print(f"[RHM-Python] Indexing path: {path}")
    # Import and run index logic
    from src.cli.main import cli
    sys.argv = ["raghub", "index", path]
    cli()


def run_search(query: str, **kwargs):
    """Run search command."""
    print(f"[RHM-Python] Searching: {query}")
    from src.cli.main import cli
    sys.argv = ["raghub", "query", query]
    cli()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RagHubMCP Python Backend",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # REST API command
    rest_parser = subparsers.add_parser("rest", help="Start REST API service")
    rest_parser.add_argument("--port", type=int, default=8818, help="Port number")
    rest_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    
    # MCP HTTP command
    mcp_parser = subparsers.add_parser("mcp", help="Start MCP HTTP service")
    mcp_parser.add_argument("--port", type=int, default=8819, help="Port number")
    mcp_parser.add_argument("--host", default="127.0.0.1", help="Host address")
    
    # Index command
    index_parser = subparsers.add_parser("index", help="Index a directory")
    index_parser.add_argument("path", help="Directory path to index")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search the knowledge base")
    search_parser.add_argument("query", help="Search query")
    
    args = parser.parse_args()
    
    if args.command == "rest":
        start_rest_api(port=args.port, host=args.host)
    elif args.command == "mcp":
        start_mcp_http(port=args.port, host=args.host)
    elif args.command == "index":
        run_index(args.path)
    elif args.command == "search":
        run_search(args.query)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()