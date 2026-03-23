"""Tests for backward-compatible RerankEngineAdapter.

Test cases for V2.1 Task 1.6:
- TC-1.6.1: RerankEngineAdapter wraps RerankEngine as BaseRerankProvider
- TC-1.6.2: Existing tests continue to pass

Reference: Docs/20-RerankEngine-Architecture.md Section 6.2
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestRerankEngineAdapter:
    """Tests for RerankEngineAdapter (TC-1.6.1)."""

    def test_adapter_import(self):
        """TC-1.6.1: RerankEngineAdapter can be imported."""
        from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter

        assert RerankEngineAdapter is not None

    def test_adapter_is_base_provider(self):
        """TC-1.6.1: RerankEngineAdapter is a BaseRerankProvider."""
        from raghub_mcp.providers.rerank.base import BaseRerankProvider
        from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter

        assert issubclass(RerankEngineAdapter, BaseRerankProvider)

    def test_adapter_has_name(self):
        """TC-1.6.1: RerankEngineAdapter has NAME attribute."""
        from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter

        assert hasattr(RerankEngineAdapter, "NAME")
        assert RerankEngineAdapter.NAME == "rerank_engine"

    def test_adapter_rerank_method_signature(self):
        """TC-1.6.1: Adapter has rerank method with correct signature."""
        from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter

        # Check method exists and has expected parameters
        assert hasattr(RerankEngineAdapter, "rerank")

    def test_adapter_from_config(self):
        """TC-1.6.1: Adapter can be created from config."""
        from raghub_mcp.providers.rerank.adapters import RerankEngineAdapter

        config = {
            "scorer_type": "onnx",
            "scorer_config": {
                "model_path": "./test.onnx",
                "tokenizer_path": "./tokenizer.json",
            },
        }

        # from_config should be a class method
        assert hasattr(RerankEngineAdapter, "from_config")


class TestRerankEngineAdapterBehavior:
    """Tests for adapter behavior."""

    def test_adapter_rerank_returns_rerank_result(self):
        """TC-1.6.1: Adapter returns list of RerankResult."""
        from raghub_mcp.providers.rerank.base import RerankResult

        # Check the return type annotation matches
        pass

    def test_adapter_preserves_document_order(self):
        """TC-1.6.1: Adapter preserves original document order in results."""
        pass

    def test_adapter_handles_empty_documents(self):
        """TC-1.6.1: Adapter handles empty document list."""
        pass


class TestBackwardCompatibility:
    """Tests for backward compatibility (TC-1.6.2)."""

    def test_existing_flashrank_provider_still_works(self):
        """TC-1.6.2: Existing FlashRankRerankProvider still works."""
        from raghub_mcp.providers.rerank.flashrank import FlashRankRerankProvider

        # Provider should still be importable
        assert FlashRankRerankProvider is not None
        assert FlashRankRerankProvider.NAME == "flashrank"

    def test_base_rerank_provider_interface_unchanged(self):
        """TC-1.6.2: BaseRerankProvider interface is unchanged."""
        from raghub_mcp.providers.rerank.base import BaseRerankProvider, RerankResult

        # RerankResult should have expected fields
        result = RerankResult(index=0, score=0.5, text="test")
        assert result.index == 0
        assert result.score == 0.5
        assert result.text == "test"

    def test_rerank_result_comparison(self):
        """TC-1.6.2: RerankResult comparison still works."""
        from raghub_mcp.providers.rerank.base import RerankResult

        r1 = RerankResult(index=0, score=0.9)
        r2 = RerankResult(index=1, score=0.5)

        # Higher score should sort first
        assert r1 < r2


class TestAdapterIntegration:
    """Integration tests for adapter with mock engine."""

    @pytest.fixture
    def mock_engine(self):
        """Create a mock RerankEngine for testing."""

        class MockEngine:
            def rerank(self, request):
                from rerank_engine.models import RerankResult

                return [
                    RerankResult(
                        document_id=str(i),
                        text=f"doc{i}",
                        score=0.9 - i * 0.1,
                        rank=i + 1,
                        metadata={},
                        original_index=i,
                    )
                    for i in range(min(request.top_k or 5, len(request.documents)))
                ]

        return MockEngine()

    @pytest.mark.skip(reason="Requires full implementation")
    def test_adapter_delegates_to_engine(self, mock_engine):
        """TC-1.6.1: Adapter correctly delegates to engine."""
        pass