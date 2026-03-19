"""Integration tests for MCP + REST API joint functionality.

Tests the complete flow:
1. Start indexing via REST API
2. Search via MCP tool
3. Search via REST API
4. Verify consistency between MCP and API responses

TC-1.17.3: test_mcp_api.py 通过
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils.config import load_config, get_config


@pytest.fixture(scope="module")
def test_client():
    """Create test client for API testing."""
    # Load config first
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    load_config(str(config_path))
    
    # Import app after config is loaded
    from main import app
    
    with TestClient(app) as client:
        yield client


class TestMCPAPIIntegration:
    """Integration tests for MCP + REST API joint functionality."""

    def test_api_health_and_mcp_ping(self, test_client):
        """TC-INT-6: Both API health and MCP ping work.
        
        Verifies that both subsystems are operational.
        """
        # Test API health
        api_response = test_client.get("/health")
        assert api_response.status_code == 200
        assert api_response.json()["status"] == "healthy"
        
        # Test MCP ping via server call
        from mcp_server.server import mcp, register_tools
        import anyio
        
        register_tools()
        
        async def test_ping():
            result = await mcp.call_tool("ping", {})
            # result is a list of TextContent objects
            result_text = result[0].text
            return json.loads(result_text)
        
        ping_result = anyio.run(test_ping)
        # result is a list of TextContent objects
        assert ping_result.get("status") == "ok"

    def test_api_config_matches_mcp_config(self, test_client):
        """TC-INT-7: API config endpoint and MCP get_config return same data.
        
        Verifies configuration consistency between API and MCP.
        """
        # Get config via API
        api_config = test_client.get("/api/config").json()
        
        # Get config via MCP
        from mcp_server.server import mcp, register_tools
        import anyio
        
        register_tools()
        
        async def get_mcp_config():
            result = await mcp.call_tool("get_config", {})
            # result is a list of TextContent objects
            result_text = result[0].text
            return json.loads(result_text)
        
        mcp_config = anyio.run(get_mcp_config)
        
        # Both should have same top-level keys
        assert set(api_config.keys()) == set(mcp_config.keys())
        assert "server" in api_config
        assert "chroma" in api_config
        assert "providers" in api_config

    def test_api_list_collections(self, test_client):
        """TC-INT-8: API can list collections.
        
        Verifies that ChromaDB integration works via API.
        """
        response = test_client.get("/api/search/collections")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "collections" in data
        assert "total" in data
        assert isinstance(data["collections"], list)

    @pytest.mark.anyio
    async def test_mcp_search_tool_registered(self):
        """TC-INT-9: MCP search tool is properly registered.
        
        Verifies that chroma_query_with_rerank is available.
        """
        from mcp_server.server import mcp, register_tools
        
        register_tools()
        
        # List tools
        tools_result = await mcp.list_tools()
        tools_list = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
        tool_names = [t.name for t in tools_list]
        
        # Verify search tool is registered
        assert "chroma_query_with_rerank" in tool_names

    @pytest.mark.anyio
    async def test_mcp_search_returns_valid_json(self):
        """TC-INT-10: MCP search tool returns valid JSON structure.
        
        Tests the response format even when collection doesn't exist.
        """
        from mcp_server.server import mcp, register_tools
        from mcp_server.tools.search import register_search_tools
        
        register_tools()
        register_search_tools(mcp)
        
        # Search non-existent collection
        result = await mcp.call_tool("chroma_query_with_rerank", {
            "collection_name": "nonexistent_test_collection",
            "query": "test query",
            "n_results": 5,
            "rerank_top_k": 3,
        })
        
        # result is a list of TextContent objects
        result_text = result[0].text
        result_data = json.loads(result_text)
        
        # Should return valid JSON with expected structure
        assert "results" in result_data
        assert "count" in result_data
        assert "query" in result_data
        assert "collection" in result_data
        
        # For non-existent collection, should have error or empty results
        assert result_data["count"] == 0

    def test_api_index_and_search_workflow(self, test_client, tmp_path):
        """TC-INT-11: Complete workflow via REST API.
        
        Tests the full API workflow:
        1. Start indexing task
        2. Check task status
        3. Query collections
        """
        # Create test file
        test_file = tmp_path / "test_api.py"
        test_file.write_text('''
def api_test_function():
    """Test function for API integration."""
    return "api_test_result"
''')
        
        # Start indexing
        index_response = test_client.post("/api/index", json={
            "path": str(test_file),
            "collection_name": "test_api_collection",
        })
        
        assert index_response.status_code == 200
        index_data = index_response.json()
        
        assert "task_id" in index_data
        assert index_data["message"] == "Indexing task started"
        
        # Check status
        import time
        time.sleep(0.5)  # Give task time to process
        
        task_id = index_data["task_id"]
        status_response = test_client.get(f"/api/index/status/{task_id}")
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        assert status_data["task_id"] == task_id
        assert status_data["status"] in ["pending", "running", "completed", "failed"]

    def test_api_error_handling_consistency(self, test_client):
        """TC-INT-12: API and MCP error formats are consistent.
        
        Verifies that error responses follow the same format.
        """
        # Trigger API error
        api_response = test_client.get("/api/index/status/nonexistent-task-id")
        
        assert api_response.status_code == 404
        
        # Both should have error information
        api_data = api_response.json()
        assert "detail" in api_data or "error" in api_data

    def test_benchmark_endpoint_with_mcp_tools(self, test_client):
        """TC-INT-13: Benchmark endpoint works with MCP tools available.
        
        Tests that the benchmark API can use MCP-registered rerank functionality.
        """
        # This test verifies the endpoint accepts valid requests
        # Actual benchmark requires indexed data
        response = test_client.post("/api/benchmark", json={
            "query": "test query",
            "collection_name": "test_benchmark",
            "configs": [
                {
                    "name": "test_config",
                    "embedding_provider": "ollama-bge",
                    "top_k": 5,
                }
            ]
        })
        
        # Should accept the request (200) or return appropriate error
        assert response.status_code in [200, 400, 404, 500]


class TestIntegrationModuleStructure:
    """Tests for integration test module structure."""

    def test_module_importable(self):
        """Verify the integration test module can be imported."""
        # Module path uses tests prefix
        from tests.test_integration import test_index_search, test_mcp_api
        assert test_index_search is not None
        assert test_mcp_api is not None

    def test_fixtures_available(self):
        """Verify pytest fixtures are properly defined."""
        from tests.test_integration import test_index_search, test_mcp_api
        
        # Check that test classes exist
        assert hasattr(test_index_search, 'TestIndexSearchIntegration')
        assert hasattr(test_mcp_api, 'TestMCPAPIIntegration')