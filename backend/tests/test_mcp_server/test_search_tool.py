"""Tests for search MCP tool (TC-1.5.x).

Test cases:
- TC-1.5.1: 查询空 collection 返回空结果
- TC-1.5.2: 查询返回正确数量文档
- TC-1.5.3: rerank_top_k 生效
- TC-1.5.4: where 条件过滤生效
- TC-1.5.5: 返回结果包含 scores
- TC-1.5.6: 结果按 score 降序排列
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


@dataclass
class MockRerankResult:
    """Mock RerankResult for testing."""
    index: int
    score: float
    text: str


class TestSearchTool:
    """TC-1.5.x: Search tool tests."""

    @pytest.fixture
    def mock_rerank_provider(self):
        """Create a mock rerank provider."""
        provider = MagicMock()
        # Default: return results sorted by score descending
        provider.rerank.return_value = [
            MockRerankResult(index=0, score=0.95, text="Machine learning is AI."),
            MockRerankResult(index=1, score=0.75, text="Deep learning uses neural nets."),
            MockRerankResult(index=2, score=0.45, text="Python is a language."),
        ]
        return provider

    @pytest.fixture
    def mock_chroma_service(self):
        """Create a mock ChromaService."""
        service = MagicMock()
        # Default: return some documents
        service.query.return_value = {
            "ids": ["id1", "id2", "id3"],
            "documents": [
                "Machine learning is AI.",
                "Deep learning uses neural nets.",
                "Python is a language.",
            ],
            "metadatas": [
                {"source": "ml_docs"},
                {"source": "dl_docs"},
                {"source": "py_docs"},
            ],
            "distances": [0.1, 0.2, 0.3],
        }
        return service

    @pytest.fixture
    def mcp_server(self):
        """Create MCP server with registered tools."""
        from mcp_server.server import mcp, register_tools
        register_tools()
        return mcp

    @pytest.mark.anyio
    async def test_tc_1_5_1_empty_collection_returns_empty(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.5.1: 查询空 collection 返回空结果."""
        # Setup: collection returns empty documents
        mock_chroma_service.query.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": [],
        }

        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "empty_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 5,
                })

        # call_tool returns list[TextContent]
        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        assert result_dict["count"] == 0
        assert result_dict["results"] == []
        assert "message" in result_dict

    @pytest.mark.anyio
    async def test_tc_1_5_2_returns_correct_document_count(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.5.2: 查询返回正确数量文档."""
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_collection",
                    "query": "What is machine learning?",
                    "n_results": 10,
                    "rerank_top_k": 3,
                })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        assert result_dict["count"] == 3
        assert len(result_dict["results"]) == 3

    @pytest.mark.anyio
    async def test_tc_1_5_3_rerank_top_k_effective(
        self, mcp_server, mock_chroma_service
    ):
        """TC-1.5.3: rerank_top_k 参数生效."""
        # Create rerank provider that respects top_k
        def mock_rerank(query, documents, top_k):
            return [
                MockRerankResult(index=i, score=0.9 - i * 0.1, text=documents[i])
                for i in range(min(top_k, len(documents)))
            ]

        rerank_provider = MagicMock()
        rerank_provider.rerank.side_effect = mock_rerank

        with patch("providers.factory.factory.get_rerank_provider", return_value=rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 2,  # Request only top 2
                })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        # Should return exactly 2 results
        assert result_dict["count"] == 2
        assert len(result_dict["results"]) == 2

    @pytest.mark.anyio
    async def test_tc_1_5_4_where_filter_effective(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.5.4: where 条件过滤生效."""
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 5,
                    "where": {"source": "ml_docs"},
                })

        # Verify query was called with where filter
        mock_chroma_service.query.assert_called_once()
        call_kwargs = mock_chroma_service.query.call_args.kwargs
        assert call_kwargs["where"] == {"source": "ml_docs"}

    @pytest.mark.anyio
    async def test_tc_1_5_5_results_contain_scores(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.5.5: 返回结果包含 scores."""
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 3,
                })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        # Each result should have a score
        for item in result_dict["results"]:
            assert "score" in item
            assert isinstance(item["score"], (int, float))
            assert 0 <= item["score"] <= 1

    @pytest.mark.anyio
    async def test_tc_1_5_6_results_sorted_by_score_descending(
        self, mcp_server, mock_chroma_service
    ):
        """TC-1.5.6: 结果按 score 降序排列."""
        # Create rerank provider with specific scores
        rerank_provider = MagicMock()
        rerank_provider.rerank.return_value = [
            MockRerankResult(index=0, score=0.95, text="Doc 1"),
            MockRerankResult(index=1, score=0.75, text="Doc 2"),
            MockRerankResult(index=2, score=0.45, text="Doc 3"),
        ]

        with patch("providers.factory.factory.get_rerank_provider", return_value=rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 3,
                })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        # Results should be sorted by score descending
        scores = [item["score"] for item in result_dict["results"]]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.anyio
    async def test_invalid_collection_returns_error(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.5.7: 无效 collection_name 抛出明确错误."""
        # Setup: query raises ValueError
        mock_chroma_service.query.side_effect = ValueError("Collection 'invalid' not found")

        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "invalid_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 5,
                })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        assert "error" in result_dict
        assert "not found" in result_dict["error"].lower()
        assert result_dict["count"] == 0

    @pytest.mark.anyio
    async def test_tool_registered(self, mcp_server):
        """Test that chroma_query_with_rerank tool is registered."""
        tools_result = await mcp_server.list_tools()
        tools_list = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
        tool_names = [t.name for t in tools_list]

        assert "chroma_query_with_rerank" in tool_names

    @pytest.mark.anyio
    async def test_empty_query_returns_error(self, mcp_server):
        """Test that empty query returns error."""
        result = await mcp_server.call_tool("chroma_query_with_rerank", {
            "collection_name": "test_collection",
            "query": "",
            "n_results": 10,
            "rerank_top_k": 5,
        })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        assert "error" in result_dict
        assert result_dict["count"] == 0

    @pytest.mark.anyio
    async def test_results_include_id_text_metadata(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """Test that results include id, text, and metadata fields."""
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("chroma_query_with_rerank", {
                    "collection_name": "test_collection",
                    "query": "test query",
                    "n_results": 10,
                    "rerank_top_k": 3,
                })

        result_text = result[0][0].text
        result_dict = json.loads(result_text)

        for item in result_dict["results"]:
            assert "id" in item
            assert "text" in item
            assert "metadata" in item
            assert "distance" in item