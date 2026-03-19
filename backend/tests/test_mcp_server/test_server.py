"""Tests for MCP Server implementation (TC-1.2.x)."""

import json
import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestConfigModule:
    """Tests for configuration module."""

    def test_config_import_success(self):
        """Test that config module can be imported."""
        from utils.config import Config, load_config, get_config
        assert Config is not None
        assert load_config is not None
        assert get_config is not None

    def test_config_dataclass_structure(self):
        """Test Config dataclass has required fields."""
        from utils.config import Config, ServerConfig, ChromaConfig
        
        config = Config()
        assert hasattr(config, "server")
        assert hasattr(config, "chroma")
        assert hasattr(config, "providers")
        assert hasattr(config, "indexer")
        assert hasattr(config, "logging")
        
        assert isinstance(config.server, ServerConfig)
        assert isinstance(config.chroma, ChromaConfig)

    def test_load_config_from_yaml(self):
        """Test loading configuration from config.yaml."""
        from utils.config import load_config
        
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        config = load_config(str(config_path))
        
        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8000
        assert config.chroma.persist_dir == "./data/chroma"

    def test_get_config_returns_loaded_config(self):
        """Test get_config returns the loaded configuration."""
        from utils.config import load_config, get_config
        
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        loaded = load_config(str(config_path))
        retrieved = get_config()
        
        assert retrieved is loaded
        assert retrieved.server.host == "0.0.0.0"


class TestMCPServer:
    """TC-1.2.x: MCP Server implementation tests."""

    def test_tc_1_2_1_server_startup(self):
        """TC-1.2.1: MCP Server 启动成功.
        
        Verify that MCP server instance can be created successfully.
        """
        # Import mcp instance and register tools
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        # Verify mcp instance exists
        assert mcp is not None
        assert mcp.name == "RagHubMCP"

    def test_tc_1_2_1_config_loaded(self):
        """TC-1.2.1: 配置加载成功.
        
        Verify configuration is loaded when server module is imported.
        """
        from utils.config import get_config
        
        config = get_config()
        
        # Verify config has required fields
        assert config.server.host is not None
        assert config.server.port is not None
        assert config.chroma is not None
        assert config.providers is not None

    @pytest.mark.anyio
    async def test_tc_1_2_2_client_connection(self):
        """TC-1.2.2: MCP 客户端可连接.
        
        Test that MCP client can connect and initialize session.
        Use FastMCP's built-in call_tool method for testing.
        """
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        # Test by calling ping tool directly
        result = await mcp.call_tool("ping", {})
        assert result is not None
        assert len(result) > 0
        # Result is a tuple: (list[TextContent], dict)
        result_text = result[0][0].text
        assert "ok" in result_text.lower()

    @pytest.mark.anyio
    async def test_tc_1_2_3_list_tools(self):
        """TC-1.2.3: list_tools 返回工具列表.
        
        Test that list_tools returns the registered tools.
        """
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        # Call list_tools method - returns ListToolsResult
        tools_result = await mcp.list_tools()
        
        # tools_result has .tools attribute which is a list
        tools_list = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
        
        # Extract tool names
        tool_names = [t.name for t in tools_list]
        
        # Verify expected tools are registered
        assert "ping" in tool_names
        assert "get_config" in tool_names
        assert "reload_config" in tool_names
        assert "list_tools" in tool_names

    @pytest.mark.anyio
    async def test_tc_1_2_4_config_reload(self):
        """TC-1.2.4: 配置热重载成功.
        
        Test that reload_config tool works correctly.
        """
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        # Call reload_config tool
        result = await mcp.call_tool("reload_config", {})
        assert result is not None
        
        # Result is a list of TextContent objects
        result_text = result[0][0].text
        result_dict = json.loads(result_text)
        assert "reloaded" in result_dict.get("status", "").lower()

    @pytest.mark.anyio
    async def test_ping_tool_returns_ok(self):
        """Test ping tool returns success status."""
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        result = await mcp.call_tool("ping", {})
        result_text = result[0][0].text
        result_dict = json.loads(result_text)
        
        assert result_dict.get("status") == "ok"
        assert result_dict.get("server") == "RagHubMCP"

    @pytest.mark.anyio
    async def test_get_config_tool_returns_config(self):
        """Test get_config tool returns configuration."""
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        result = await mcp.call_tool("get_config", {})
        result_text = result[0][0].text
        
        # Parse returned JSON
        config_dict = json.loads(result_text)
        
        assert "server" in config_dict
        assert "chroma" in config_dict
        assert "providers" in config_dict

    @pytest.mark.anyio
    async def test_list_tools_tool(self):
        """Test list_tools tool returns available tools."""
        from mcp_server.server import mcp, register_tools
        register_tools()
        
        result = await mcp.call_tool("list_tools", {})
        result_text = result[0][0].text
        
        tools = json.loads(result_text)
        assert isinstance(tools, list)
        assert len(tools) >= 4  # At least 4 basic tools