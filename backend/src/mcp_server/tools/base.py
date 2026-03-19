"""Base MCP tools for RagHubMCP.

This module provides fundamental tools for server status, configuration
management, and basic operations.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Flag to track if tools are registered
_tools_registered = False


def register_base_tools(mcp: "FastMCP") -> None:
    """Register base MCP tools.
    
    Args:
        mcp: The FastMCP server instance to register tools with.
    """
    global _tools_registered
    
    # Avoid duplicate registration
    if _tools_registered:
        logger.debug("Tools already registered, skipping")
        return
    
    @mcp.tool()
    def ping() -> str:
        """Test MCP server connectivity.
        
        Returns a success status to confirm the server is responsive.
        Use this tool to verify the MCP connection is working correctly.
        
        Returns:
            JSON string with server status and name.
        """
        result = {
            "status": "ok",
            "server": "RagHubMCP",
            "message": "Server is running correctly"
        }
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def get_config() -> str:
        """Get the current server configuration.
        
        Returns the complete configuration currently loaded by the server.
        This includes server settings, Chroma configuration, provider settings,
        and indexer configuration.
        
        Returns:
            JSON string containing the current configuration.
        """
        # Use absolute import to avoid relative import issues
        from utils.config import get_config as _get_config, config_to_dict
        
        config = _get_config()
        config_dict = config_to_dict(config)
        
        return json.dumps(config_dict, indent=2, default=str)
    
    @mcp.tool()
    def reload_config() -> str:
        """Hot-reload the server configuration.
        
        Reloads the configuration from the config.yaml file without
        restarting the server. Use this when you've modified the
        configuration file and want the changes to take effect.
        
        Returns:
            JSON string confirming the reload operation.
        """
        from utils.config import reload_config as _reload_config
        
        try:
            _reload_config()
            result = {
                "status": "reloaded",
                "message": "Configuration reloaded successfully"
            }
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            result = {
                "status": "error",
                "message": f"Failed to reload configuration: {str(e)}"
            }
            logger.error(f"Failed to reload configuration: {e}")
        
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def list_tools() -> str:
        """List all available MCP tools.
        
        Returns a list of all tools registered with the MCP server.
        Use this to discover what operations are available.
        
        Returns:
            JSON string containing a list of tool names.
        """
        tools = [
            "ping",
            "get_config",
            "reload_config",
            "list_tools",
            "get_server_info"
        ]
        return json.dumps(tools, indent=2)
    
    @mcp.tool()
    def get_server_info() -> str:
        """Get server information and status.
        
        Returns detailed information about the server including
        version, transport mode, and configuration summary.
        
        Returns:
            JSON string with server information.
        """
        from utils.config import get_config as _get_config
        
        config = _get_config()
        
        info = {
            "name": "RagHubMCP",
            "version": "0.1.0",
            "description": "MCP Server for RAG operations with FlashRank reranking",
            "server": {
                "host": config.server.host,
                "port": config.server.port,
                "debug": config.server.debug
            },
            "providers": {
                "default_embedding": config.providers.embedding.default,
                "default_rerank": config.providers.rerank.default,
                "default_llm": config.providers.llm.default
            },
            "indexer": {
                "chunk_size": config.indexer.chunk_size,
                "chunk_overlap": config.indexer.chunk_overlap,
                "supported_file_types": config.indexer.file_types
            }
        }
        
        return json.dumps(info, indent=2)
    
    _tools_registered = True