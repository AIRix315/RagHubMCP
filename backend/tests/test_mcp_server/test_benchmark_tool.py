"""Tests for benchmark MCP tool (TC-1.6.x).

Test cases:
- TC-1.6.1: 单配置 benchmark 成功
- TC-1.6.2: 多配置对比成功
- TC-1.6.3: Recall 计算正确
- TC-1.6.4: MRR 计算正确
- TC-1.6.5: 延迟统计正确
- TC-1.6.6: 推荐配置是 MRR 最高的
- TC-1.6.7: 空查询列表处理正确
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


class TestBenchmarkTool:
    """TC-1.6.x: Benchmark tool tests."""

    @pytest.fixture
    def mock_rerank_provider(self):
        """Create a mock rerank provider."""
        provider = MagicMock()
        provider.rerank.return_value = [
            MockRerankResult(index=0, score=0.95, text="Doc 1"),
            MockRerankResult(index=1, score=0.75, text="Doc 2"),
            MockRerankResult(index=2, score=0.45, text="Doc 3"),
        ]
        return provider

    @pytest.fixture
    def mock_chroma_service(self):
        """Create a mock ChromaService."""
        service = MagicMock()
        service.query.return_value = {
            "ids": ["doc1", "doc2", "doc3"],
            "documents": ["Doc 1", "Doc 2", "Doc 3"],
            "metadatas": [{"src": "a"}, {"src": "b"}, {"src": "c"}],
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
    async def test_tc_1_6_1_single_config_benchmark_success(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.6.1: 单配置 benchmark 成功."""
        queries = [
            {"query": "What is ML?", "relevant_ids": ["doc1", "doc2"]},
            {"query": "Deep learning?", "relevant_ids": ["doc2"]},
            {"query": "Python?", "relevant_ids": ["doc3"]},
        ]
        configs = [
            {"name": "baseline", "n_results": 10, "rerank_top_k": 3}
        ]

        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("benchmark_search_config", {
                    "collection_name": "test_collection",
                    "queries": queries,
                    "configs": configs,
                })

        # FastMCP returns (list[TextContent], dict)
        result_text = result[0].text
        result_dict = json.loads(result_text)

        # Verify structure
        assert "results" in result_dict
        assert "comparison" in result_dict
        assert "summary" in result_dict
        assert len(result_dict["results"]) == 1
        assert result_dict["summary"]["total_queries"] == 3
        assert result_dict["summary"]["total_configs"] == 1

    @pytest.mark.anyio
    async def test_tc_1_6_2_multi_config_comparison(
        self, mcp_server, mock_rerank_provider, mock_chroma_service
    ):
        """TC-1.6.2: 多配置对比成功."""
        queries = [
            {"query": "What is ML?", "relevant_ids": ["doc1"]},
        ]
        configs = [
            {"name": "config_a", "n_results": 5, "rerank_top_k": 3},
            {"name": "config_b", "n_results": 10, "rerank_top_k": 5},
        ]

        with patch("providers.factory.factory.get_rerank_provider", return_value=mock_rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma_service):
                result = await mcp_server.call_tool("benchmark_search_config", {
                    "collection_name": "test_collection",
                    "queries": queries,
                    "configs": configs,
                })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        # Verify comparison table
        assert len(result_dict["results"]) == 2
        assert "comparison" in result_dict
        assert "table" in result_dict["comparison"]
        assert len(result_dict["comparison"]["table"]) == 2
        assert result_dict["summary"]["total_configs"] == 2

    @pytest.mark.anyio
    async def test_tc_1_6_3_recall_calculation_correct(
        self, mcp_server, mock_rerank_provider
    ):
        """TC-1.6.3: Recall 计算正确."""
        # Setup: doc1, doc2 are relevant, retrieve doc1, doc3, doc2
        # Recall@3 = 2/2 = 1.0
        # Recall@2 = 1/2 = 0.5
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": ["doc1", "doc3", "doc2"],  # doc3 is not relevant
            "documents": ["Doc 1", "Doc 3", "Doc 2"],
            "metadatas": [{}, {}, {}],
            "distances": [0.1, 0.2, 0.3],
        }

        # Rerank returns same order - use correct param names
        rerank_provider = MagicMock()
        def mock_rerank(query, documents, top_k):
            return [
                MockRerankResult(index=i, score=0.9 - i * 0.1, text=documents[i])
                for i in range(min(top_k, len(documents)))
            ]
        rerank_provider.rerank.side_effect = mock_rerank

        queries = [
            {"query": "test", "relevant_ids": ["doc1", "doc2"]},
        ]
        configs = [
            {"name": "test_config", "n_results": 10, "rerank_top_k": 3}
        ]

        with patch("providers.factory.factory.get_rerank_provider", return_value=rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma):
                result = await mcp_server.call_tool("benchmark_search_config", {
                    "collection_name": "test_collection",
                    "queries": queries,
                    "configs": configs,
                })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        # Recall@3 = 2 relevant found in top 3 / 2 total relevant = 1.0
        recall = result_dict["results"][0]["metrics"]["recall_at_k"]
        assert recall == 1.0

    @pytest.mark.anyio
    async def test_tc_1_6_4_mrr_calculation_correct(
        self, mcp_server
    ):
        """TC-1.6.4: MRR 计算正确."""
        # Setup: relevant doc is at position 1, MRR = 1/1 = 1.0
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": ["doc1", "doc2", "doc3"],  # doc1 is relevant, at rank 1
            "documents": ["Doc 1", "Doc 2", "Doc 3"],
            "metadatas": [{}, {}, {}],
            "distances": [0.1, 0.2, 0.3],
        }

        rerank_provider = MagicMock()
        def mock_rerank(query, documents, top_k):
            return [
                MockRerankResult(index=i, score=0.9 - i * 0.1, text=documents[i])
                for i in range(min(top_k, len(documents)))
            ]
        rerank_provider.rerank.side_effect = mock_rerank

        queries = [
            {"query": "test", "relevant_ids": ["doc1"]},  # doc1 at rank 1
        ]
        configs = [
            {"name": "test_config", "n_results": 10, "rerank_top_k": 3}
        ]

        with patch("providers.factory.factory.get_rerank_provider", return_value=rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma):
                result = await mcp_server.call_tool("benchmark_search_config", {
                    "collection_name": "test_collection",
                    "queries": queries,
                    "configs": configs,
                })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        # MRR = 1/1 = 1.0 (doc1 is at rank 1)
        mrr = result_dict["results"][0]["metrics"]["mrr"]
        assert mrr == 1.0

    @pytest.mark.anyio
    async def test_tc_1_6_5_latency_statistics_correct(
        self, mcp_server
    ):
        """TC-1.6.5: 延迟统计正确."""
        # We can't control exact latency, but we can verify structure
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": ["doc1"],
            "documents": ["Doc 1"],
            "metadatas": [{}],
            "distances": [0.1],
        }

        rerank_provider = MagicMock()
        rerank_provider.rerank.return_value = [
            MockRerankResult(index=0, score=0.9, text="Doc 1"),
        ]

        queries = [
            {"query": "query 1", "relevant_ids": ["doc1"]},
            {"query": "query 2", "relevant_ids": ["doc1"]},
            {"query": "query 3", "relevant_ids": ["doc1"]},
        ]
        configs = [
            {"name": "test_config", "n_results": 10, "rerank_top_k": 1}
        ]

        with patch("providers.factory.factory.get_rerank_provider", return_value=rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma):
                result = await mcp_server.call_tool("benchmark_search_config", {
                    "collection_name": "test_collection",
                    "queries": queries,
                    "configs": configs,
                })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        metrics = result_dict["results"][0]["metrics"]
        
        # Verify latency metrics exist and are non-negative
        assert "latency_avg_ms" in metrics
        assert "latency_min_ms" in metrics
        assert "latency_max_ms" in metrics
        assert metrics["latency_avg_ms"] >= 0
        assert metrics["latency_min_ms"] >= 0
        assert metrics["latency_max_ms"] >= 0
        # max >= avg >= min
        assert metrics["latency_max_ms"] >= metrics["latency_min_ms"]

    @pytest.mark.anyio
    async def test_tc_1_6_6_recommend_best_mrr_config(
        self, mcp_server
    ):
        """TC-1.6.6: 推荐配置是 MRR 最高的."""
        # Config A: MRR = 1.0 (doc1 at rank 1)
        # Config B: MRR = 0.5 (doc2 at rank 2)

        rerank_provider = MagicMock()
        def mock_rerank(query, documents, top_k):
            return [
                MockRerankResult(index=i, score=0.9 - i * 0.1, text=documents[i])
                for i in range(min(top_k, len(documents)))
            ]
        rerank_provider.rerank.side_effect = mock_rerank

        queries = [
            {"query": "test", "relevant_ids": ["doc1"]},
        ]
        configs = [
            {"name": "config_a", "n_results": 10, "rerank_top_k": 3},
            {"name": "config_b", "n_results": 10, "rerank_top_k": 3},
        ]

        # Track call count to return different results for different configs
        call_count = [0]
        
        def mock_query_side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # Config A: doc1 at rank 1
                return {
                    "ids": ["doc1", "doc2", "doc3"],
                    "documents": ["Doc 1", "Doc 2", "Doc 3"],
                    "metadatas": [{}, {}, {}],
                    "distances": [0.1, 0.2, 0.3],
                }
            else:
                # Config B: doc1 at rank 2 (doc2 first)
                return {
                    "ids": ["doc2", "doc1", "doc3"],
                    "documents": ["Doc 2", "Doc 1", "Doc 3"],
                    "metadatas": [{}, {}, {}],
                    "distances": [0.1, 0.2, 0.3],
                }

        mock_chroma = MagicMock()
        mock_chroma.query.side_effect = mock_query_side_effect

        with patch("providers.factory.factory.get_rerank_provider", return_value=rerank_provider):
            with patch("services.get_chroma_service", return_value=mock_chroma):
                result = await mcp_server.call_tool("benchmark_search_config", {
                    "collection_name": "test_collection",
                    "queries": queries,
                    "configs": configs,
                })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        # Best config should be config_a (MRR = 1.0)
        assert result_dict["comparison"]["best_config"] == "config_a"
        assert result_dict["comparison"]["best_metric"] == "mrr"

    @pytest.mark.anyio
    async def test_tc_1_6_7_empty_queries_returns_error(
        self, mcp_server
    ):
        """TC-1.6.7: 空查询列表处理正确."""
        result = await mcp_server.call_tool("benchmark_search_config", {
            "collection_name": "test_collection",
            "queries": [],  # Empty queries
            "configs": [{"name": "test"}],
        })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        assert "error" in result_dict
        assert "empty" in result_dict["error"].lower()

    @pytest.mark.anyio
    async def test_tool_registered(self, mcp_server):
        """Test that benchmark_search_config tool is registered."""
        tools_result = await mcp_server.list_tools()
        tools_list = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
        tool_names = [t.name for t in tools_list]

        assert "benchmark_search_config" in tool_names

    @pytest.mark.anyio
    async def test_empty_configs_returns_error(self, mcp_server):
        """Test that empty configs returns error."""
        result = await mcp_server.call_tool("benchmark_search_config", {
            "collection_name": "test_collection",
            "queries": [{"query": "test", "relevant_ids": ["doc1"]}],
            "configs": [],  # Empty configs
        })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        assert "error" in result_dict

    @pytest.mark.anyio
    async def test_empty_collection_name_returns_error(self, mcp_server):
        """Test that empty collection_name returns error."""
        result = await mcp_server.call_tool("benchmark_search_config", {
            "collection_name": "",  # Empty collection name
            "queries": [{"query": "test", "relevant_ids": ["doc1"]}],
            "configs": [{"name": "test"}],
        })

        result_text = result[0].text
        result_dict = json.loads(result_text)

        assert "error" in result_dict


class TestMetricCalculations:
    """Unit tests for metric calculation functions."""

    def test_recall_at_k_all_relevant_found(self):
        """Test Recall@K when all relevant docs are retrieved."""
        from mcp_server.tools.benchmark import calculate_recall_at_k

        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1", "doc2"]
        
        recall = calculate_recall_at_k(retrieved, relevant, k=3)
        assert recall == 1.0

    def test_recall_at_k_partial(self):
        """Test Recall@K when partial relevant docs are retrieved."""
        from mcp_server.tools.benchmark import calculate_recall_at_k

        retrieved = ["doc1", "doc3", "doc4"]
        relevant = ["doc1", "doc2"]
        
        # Only doc1 found, 1 out of 2 relevant
        recall = calculate_recall_at_k(retrieved, relevant, k=3)
        assert recall == 0.5

    def test_recall_at_k_none_found(self):
        """Test Recall@K when no relevant docs are retrieved."""
        from mcp_server.tools.benchmark import calculate_recall_at_k

        retrieved = ["doc3", "doc4", "doc5"]
        relevant = ["doc1", "doc2"]
        
        recall = calculate_recall_at_k(retrieved, relevant, k=3)
        assert recall == 0.0

    def test_recall_at_k_empty_relevant(self):
        """Test Recall@K with empty relevant list."""
        from mcp_server.tools.benchmark import calculate_recall_at_k

        recall = calculate_recall_at_k(["doc1", "doc2"], [], k=3)
        assert recall == 0.0

    def test_mrr_first_position(self):
        """Test MRR when relevant doc is at position 1."""
        from mcp_server.tools.benchmark import calculate_mrr

        retrieved = ["doc1", "doc2", "doc3"]
        relevant = ["doc1"]
        
        mrr = calculate_mrr(retrieved, relevant)
        assert mrr == 1.0

    def test_mrr_second_position(self):
        """Test MRR when relevant doc is at position 2."""
        from mcp_server.tools.benchmark import calculate_mrr

        retrieved = ["doc2", "doc1", "doc3"]
        relevant = ["doc1"]
        
        mrr = calculate_mrr(retrieved, relevant)
        assert mrr == 0.5

    def test_mrr_third_position(self):
        """Test MRR when relevant doc is at position 3."""
        from mcp_server.tools.benchmark import calculate_mrr

        retrieved = ["doc2", "doc3", "doc1"]
        relevant = ["doc1"]
        
        mrr = calculate_mrr(retrieved, relevant)
        assert mrr == pytest.approx(1/3, rel=1e-4)

    def test_mrr_not_found(self):
        """Test MRR when relevant doc is not in results."""
        from mcp_server.tools.benchmark import calculate_mrr

        retrieved = ["doc2", "doc3", "doc4"]
        relevant = ["doc1"]
        
        mrr = calculate_mrr(retrieved, relevant)
        assert mrr == 0.0

    def test_mrr_multiple_relevant(self):
        """Test MRR with multiple relevant docs (uses first found)."""
        from mcp_server.tools.benchmark import calculate_mrr

        retrieved = ["doc2", "doc1", "doc3"]
        relevant = ["doc1", "doc3"]
        
        # doc1 is at position 2, doc3 is at position 3
        # MRR should use first found = 1/2 = 0.5
        mrr = calculate_mrr(retrieved, relevant)
        assert mrr == 0.5

    def test_mrr_empty_lists(self):
        """Test MRR with empty lists."""
        from mcp_server.tools.benchmark import calculate_mrr

        assert calculate_mrr([], ["doc1"]) == 0.0
        assert calculate_mrr(["doc1"], []) == 0.0
        assert calculate_mrr([], []) == 0.0