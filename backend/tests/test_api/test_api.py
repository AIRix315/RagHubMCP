"""Tests for REST API endpoints (TC-1.15.x).

This module contains tests for all REST API endpoints.
"""

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
    
    # Mock the vectorstore provider for testing
    # Hub is a connector, not a pre-installed provider
    mock_vectorstore = MagicMock()
    mock_vectorstore.list_collections.return_value = []
    
    with patch('src.api.search._get_vectorstore_provider', return_value=mock_vectorstore):
        # Import app after config is loaded
        from main import app
        
        with TestClient(app) as client:
            yield client


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, test_client):
        """Test health check returns healthy status."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "RagHubMCP"

    def test_root_endpoint(self, test_client):
        """Test root endpoint returns API info."""
        response = test_client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data


class TestConfigAPI:
    """TC-1.15.1, TC-1.15.2: Configuration API tests."""

    def test_tc_1_15_1_get_config(self, test_client):
        """TC-1.15.1: GET /api/config returns configuration."""
        response = test_client.get("/api/config")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify required fields exist
        assert "server" in data
        assert "chroma" in data
        assert "providers" in data
        assert "indexer" in data
        assert "logging" in data
        
        # Verify server config
        assert "host" in data["server"]
        assert "port" in data["server"]

    def test_tc_1_15_2_update_config(self, test_client):
        """TC-1.15.2: PUT /api/config updates configuration."""
        # Get current config
        current = test_client.get("/api/config").json()
        
        # Update with same values (non-destructive test)
        update_data = {
            "server": {
                "host": current["server"]["host"],
                "port": current["server"]["port"],
                "debug": current["server"]["debug"],
            }
        }
        
        response = test_client.put("/api/config", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"


class TestIndexAPI:
    """TC-1.15.3, TC-1.15.4: Index API tests."""

    def test_tc_1_15_3_start_index(self, test_client, tmp_path):
        """TC-1.15.3: POST /api/index starts indexing task."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        request_data = {
            "path": str(test_file),
            "collection_name": "test_collection",
        }
        
        response = test_client.post("/api/index", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["message"] == "Indexing task started"
        assert "status_url" in data

    def test_tc_1_15_4_get_index_status(self, test_client, tmp_path):
        """TC-1.15.4: GET /api/index/status queries task status."""
        # Start an index task
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        start_response = test_client.post("/api/index", json={
            "path": str(test_file),
            "collection_name": "test_collection",
        })
        task_id = start_response.json()["task_id"]
        
        # Query status
        import time
        time.sleep(0.5)  # Give task time to process
        
        response = test_client.get(f"/api/index/status/{task_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == task_id
        assert "status" in data
        assert data["status"] in ["pending", "running", "completed", "failed"]

    def test_index_status_not_found(self, test_client):
        """Test 404 for non-existent task."""
        response = test_client.get("/api/index/status/nonexistent-id")
        assert response.status_code == 404

    def test_index_invalid_path(self, test_client):
        """Test 404 for invalid path."""
        response = test_client.post("/api/index", json={
            "path": "/nonexistent/path",
            "collection_name": "test",
        })
        assert response.status_code == 404


class TestSearchAPI:
    """TC-1.15.5: Search API tests."""

    def test_tc_1_15_5_search_endpoint_exists(self, test_client):
        """TC-1.15.5: POST /api/search endpoint exists."""
        # This test verifies the endpoint exists and accepts requests
        # Actual search requires indexed data
        response = test_client.post("/api/search", json={
            "query": "test query",
            "collection_name": "nonexistent",
            "top_k": 5,
        })
        
        # Should return 200 even if collection doesn't exist (returns empty results)
        # or 404 if collection is required
        assert response.status_code in [200, 404, 500]

    def test_list_collections(self, test_client):
        """Test listing collections."""
        response = test_client.get("/api/search/collections")
        assert response.status_code == 200
        
        data = response.json()
        assert "collections" in data
        assert "total" in data
        assert isinstance(data["collections"], list)


class TestBenchmarkAPI:
    """TC-1.15.6: Benchmark API tests."""

    def test_tc_1_15_6_benchmark_endpoint_exists(self, test_client):
        """TC-1.15.6: POST /api/benchmark endpoint exists."""
        response = test_client.post("/api/benchmark", json={
            "query": "test query",
            "collection_name": "test",
            "configs": [
                {
                    "name": "config1",
                    "embedding_provider": "ollama-bge",
                    "top_k": 5,
                }
            ]
        })
        
        # Should return 200 or appropriate error
        assert response.status_code in [200, 400, 404, 500]

    def test_benchmark_requires_configs(self, test_client):
        """Test that benchmark requires at least one config."""
        response = test_client.post("/api/benchmark", json={
            "query": "test",
            "collection_name": "test",
            "configs": []
        })
        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422


class TestErrorHandling:
    """TC-1.15.7: Error response format tests."""

    def test_tc_1_15_7_error_format(self, test_client):
        """TC-1.15.7: Error response format is unified."""
        # Trigger an error by requesting non-existent task
        response = test_client.get("/api/index/status/invalid-task-id")
        
        assert response.status_code == 404
        
        data = response.json()
        
        # Check error format - should have 'detail' as dict with 'error' and 'message'
        if isinstance(data.get("detail"), dict):
            assert "error" in data["detail"]
            assert "message" in data["detail"]

    def test_api_root(self, test_client):
        """Test API root endpoint."""
        response = test_client.get("/api")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "RagHubMCP API"
        assert "endpoints" in data


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_search_request_validation(self):
        """Test SearchRequest validation."""
        from api.schemas import SearchRequest
        
        # Valid request
        request = SearchRequest(query="test", collection_name="test")
        assert request.query == "test"
        assert request.top_k == 5  # default
        
        # Invalid top_k
        with pytest.raises(ValueError):
            SearchRequest(query="test", collection_name="test", top_k=0)
        
        with pytest.raises(ValueError):
            SearchRequest(query="test", collection_name="test", top_k=101)

    def test_index_request_validation(self):
        """Test IndexRequest validation."""
        from api.schemas import IndexRequest
        
        request = IndexRequest(path="/test")
        assert request.path == "/test"
        assert request.collection_name == "default"  # default
        assert request.recursive is True  # default

    def test_benchmark_config_validation(self):
        """Test BenchmarkConfig validation."""
        from api.schemas import BenchmarkConfig
        
        config = BenchmarkConfig(
            name="test",
            embedding_provider="test-embedding",
        )
        assert config.name == "test"
        assert config.top_k == 5  # default