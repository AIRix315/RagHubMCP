"""Tests for rerank MCP tool (TC-1.7.x).

Test cases:
- TC-1.7.1: 文档列表重排成功
- TC-1.7.2: 返回结果包含原文档内容
- TC-1.7.3: 返回结果包含 score
- TC-1.7.4: top_k 参数生效
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


class TestRerankTool:
    """TC-1.7.x: Rerank tool tests."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock rerank provider."""
        provider = MagicMock()
        provider.rerank.return_value = [
            MockRerankResult(index=0, score=0.95, text="Machine learning is a subset of AI."),
            MockRerankResult(index=1, score=0.75, text="Deep learning uses neural networks."),
            MockRerankResult(index=2, score=0.45, text="Python is a programming language."),
        ]
        return provider

    @pytest.fixture
    def mcp_server(self):
        """Create MCP server with registered tools."""
        from mcp_server.server import mcp, register_tools
        register_tools()
        return mcp

    @pytest.mark.anyio
    async def test_tc_1_7_1_rerank_success(self, mcp_server, mock_provider):
        """TC-1.7.1: 文档列表重排成功.
        
        Verify that rerank_documents tool successfully re-ranks documents.
        """
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_provider):
            result = await mcp_server.call_tool("rerank_documents", {
                "query": "What is machine learning?",
                "documents": [
                    "Machine learning is a subset of AI.",
                    "Deep learning uses neural networks.",
                    "Python is a programming language.",
                ],
                "top_k": 3,
            })
        
        # Parse result - call_tool returns list[TextContent] directly
        result_text = result[0].text
        result_dict = json.loads(result_text)
        
        # Verify structure
        assert "results" in result_dict
        assert "count" in result_dict
        assert "query" in result_dict
        assert result_dict["count"] == 3

    @pytest.mark.anyio
    async def test_tc_1_7_2_returns_document_content(self, mcp_server, mock_provider):
        """TC-1.7.2: 返回结果包含原文档内容.
        
        Verify that each result includes the original document text.
        """
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_provider):
            result = await mcp_server.call_tool("rerank_documents", {
                "query": "What is machine learning?",
                "documents": [
                    "Machine learning is a subset of AI.",
                    "Deep learning uses neural networks.",
                ],
                "top_k": 2,
            })
        
        result_text = result[0].text
        result_dict = json.loads(result_text)
        
        # Verify each result has 'text' field
        for item in result_dict["results"]:
            assert "text" in item
            assert isinstance(item["text"], str)
            assert len(item["text"]) > 0

    @pytest.mark.anyio
    async def test_tc_1_7_3_returns_score(self, mcp_server, mock_provider):
        """TC-1.7.3: 返回结果包含 score.
        
        Verify that each result includes a relevance score.
        """
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_provider):
            result = await mcp_server.call_tool("rerank_documents", {
                "query": "What is machine learning?",
                "documents": [
                    "Machine learning is a subset of AI.",
                    "Deep learning uses neural networks.",
                ],
                "top_k": 2,
            })
        
        result_text = result[0].text
        result_dict = json.loads(result_text)
        
        # Verify each result has 'score' field
        for item in result_dict["results"]:
            assert "score" in item
            assert isinstance(item["score"], (int, float))
            assert 0 <= item["score"] <= 1  # Scores typically in [0, 1]

    @pytest.mark.anyio
    async def test_tc_1_7_4_top_k_parameter(self, mcp_server):
        """TC-1.7.4: top_k 参数生效.
        
        Verify that top_k parameter limits the number of returned results.
        """
        # Create provider that returns results based on top_k
        def mock_rerank(query, documents, top_k):
            return [
                MockRerankResult(index=i, score=0.9 - i * 0.1, text=f"Document {i}")
                for i in range(min(top_k, len(documents)))
            ]
        
        mock_provider = MagicMock()
        mock_provider.rerank.side_effect = mock_rerank
        
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_provider):
            # Request only top 2
            result = await mcp_server.call_tool("rerank_documents", {
                "query": "Test query",
                "documents": [f"Document {i}" for i in range(5)],
                "top_k": 2,
            })
        
        result_text = result[0].text
        result_dict = json.loads(result_text)
        
        # Verify only 2 results returned
        assert result_dict["count"] == 2
        assert len(result_dict["results"]) == 2
        
        # Verify provider was called with top_k=2
        mock_provider.rerank.assert_called_once()
        call_args = mock_provider.rerank.call_args
        assert call_args[0][0] == "Test query"  # query
        assert len(call_args[0][1]) == 5  # documents
        assert call_args[0][2] == 2  # top_k

    @pytest.mark.anyio
    async def test_empty_documents_returns_empty_result(self, mcp_server):
        """Test that empty document list returns empty results gracefully."""
        result = await mcp_server.call_tool("rerank_documents", {
            "query": "Test query",
            "documents": [],
            "top_k": 5,
        })
        
        result_text = result[0].text
        result_dict = json.loads(result_text)
        
        assert result_dict["count"] == 0
        assert result_dict["results"] == []
        assert "message" in result_dict

    @pytest.mark.anyio
    async def test_result_includes_original_index(self, mcp_server, mock_provider):
        """Test that results include original document index."""
        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_provider):
            result = await mcp_server.call_tool("rerank_documents", {
                "query": "What is machine learning?",
                "documents": [
                    "Machine learning is a subset of AI.",
                    "Deep learning uses neural networks.",
                    "Python is a programming language.",
                ],
                "top_k": 3,
            })
        
        result_text = result[0].text
        result_dict = json.loads(result_text)
        
        # Verify each result has 'index' field
        for item in result_dict["results"]:
            assert "index" in item
            assert isinstance(item["index"], int)
            assert 0 <= item["index"] < 3

    @pytest.mark.anyio
    async def test_rerank_tool_registered(self, mcp_server):
        """Test that rerank_documents tool is registered."""
        tools_result = await mcp_server.list_tools()
        tools_list = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
        tool_names = [t.name for t in tools_list]
        
        assert "rerank_documents" in tool_names