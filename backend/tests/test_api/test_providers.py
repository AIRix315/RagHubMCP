"""Tests for Provider Management API endpoints.

This module tests the Provider CRUD and testing endpoints as defined in:
- Docs/22-Config-API-Design.md Section 3.2.2, 3.2.3
- TODO 1.10: Rerank相关API实现
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from utils.config import load_config


@pytest.fixture(scope="module")
def test_client():
    """Create test client for API testing."""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    load_config(str(config_path))

    from main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_rerank_provider():
    """Create a mock rerank provider for testing."""
    provider = MagicMock()
    provider.rerank = AsyncMock(return_value=[
        {"index": 0, "text": "doc1", "score": 0.95, "rank": 1},
        {"index": 1, "text": "doc2", "score": 0.85, "rank": 2},
    ])
    provider.type = "onnx"
    provider.model = "test-model"
    return provider


@pytest.fixture
def mock_embedding_provider():
    """Create a mock embedding provider for testing."""
    provider = MagicMock()
    provider.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    provider.type = "ollama"
    provider.model = "bge-m3"
    return provider


class TestProvidersList:
    """Tests for GET /api/providers endpoint."""

    def test_list_all_providers(self, test_client):
        """Test listing all providers grouped by category."""
        response = test_client.get("/api/providers")
        assert response.status_code == 200

        data = response.json()
        assert "embedding" in data
        assert "rerank" in data
        assert "vectorstore" in data

    def test_list_rerank_providers(self, test_client):
        """Test listing rerank providers only (Task 1.10.1)."""
        response = test_client.get("/api/providers/rerank")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Each provider should have required fields
        for provider in data:
            assert "name" in provider
            assert "type" in provider
            assert "status" in provider
            assert "is_default" in provider


class TestRerankProviderDetail:
    """Tests for GET /api/providers/rerank/{name} endpoint."""

    def test_get_rerank_provider_not_found(self, test_client):
        """Test 404 for non-existent provider."""
        response = test_client.get("/api/providers/rerank/nonexistent-provider")
        assert response.status_code == 404


class TestRerankProviderTest:
    """Tests for POST /api/providers/rerank/{name}/test endpoint (Task 1.10.2)."""

    def test_rerank_test_validation(self, test_client):
        """Test request validation for rerank test."""
        # Missing required fields
        response = test_client.post(
            "/api/providers/rerank/test-provider/test",
            json={},
        )
        assert response.status_code == 422  # Validation error

    def test_rerank_test_provider_not_found(self, test_client):
        """Test 404 for testing non-existent provider."""
        response = test_client.post(
            "/api/providers/rerank/nonexistent-provider/test",
            json={
                "query": "test query",
                "documents": ["doc1", "doc2"],
            },
        )
        assert response.status_code == 404


class TestProviderCRUD:
    """Tests for Provider CRUD operations (Task 1.10.3)."""

    def test_create_provider_validation(self, test_client):
        """Test provider creation validation."""
        # Missing required fields
        response = test_client.put(
            "/api/providers/rerank/new-provider",
            json={},
        )
        assert response.status_code == 422

    def test_delete_provider_not_found(self, test_client):
        """Test 404 for deleting non-existent provider."""
        response = test_client.delete("/api/providers/rerank/nonexistent-provider")
        assert response.status_code == 404

    def test_set_default_provider_not_found(self, test_client):
        """Test 404 for setting non-existent provider as default."""
        response = test_client.post("/api/providers/rerank/nonexistent-provider/set-default")
        assert response.status_code == 404


class TestProviderSchemas:
    """Tests for Provider-related Pydantic schemas."""

    def test_rerank_test_request_schema(self):
        """Test RerankTestRequest validation."""
        from api.schemas import RerankTestRequest

        # Valid request
        request = RerankTestRequest(
            query="test query",
            documents=["doc1", "doc2"],
        )
        assert request.query == "test query"
        assert len(request.documents) == 2
        assert request.top_k == 5  # default

        # Invalid top_k
        with pytest.raises(ValueError):
            RerankTestRequest(query="test", documents=["doc1"], top_k=0)

        with pytest.raises(ValueError):
            RerankTestRequest(query="test", documents=["doc1"], top_k=101)

    def test_rerank_test_response_schema(self):
        """Test RerankTestResponse model."""
        from api.schemas import RerankTestResponse, RerankResult

        result = RerankResult(
            index=0,
            text="test doc",
            score=0.95,
            rank=1,
        )
        assert result.index == 0
        assert result.score == 0.95

    def test_provider_info_schema(self):
        """Test ProviderInfo model."""
        from api.schemas import ProviderInfo

        info = ProviderInfo(
            name="test-provider",
            type="onnx",
            status="active",
            is_default=True,
        )
        assert info.name == "test-provider"
        assert info.status == "active"
        assert info.is_default is True

    def test_provider_create_request_schema(self):
        """Test ProviderCreateRequest validation."""
        from api.schemas import ProviderCreateRequest

        # Valid request with minimal fields
        request = ProviderCreateRequest(
            type="onnx",
            config={"model": "test-model"},
        )
        assert request.type == "onnx"
        assert request.config["model"] == "test-model"


class TestProviderStatus:
    """Tests for provider status checking."""

    def test_provider_status_values(self):
        """Test valid provider status values."""
        from api.schemas import ProviderStatus

        assert ProviderStatus.ACTIVE == "active"
        assert ProviderStatus.INACTIVE == "inactive"
        assert ProviderStatus.ERROR == "error"