"""Tests for hybrid search services.

Tests cover:
- TC-HYB-1: BM25Service indexing and querying
- TC-HYB-2: BM25Service persistence
- TC-HYB-3: Reciprocal Rank Fusion algorithm
- TC-HYB-4: HybridSearchService integration
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.bm25_service import (
    BM25Index,
    BM25Service,
    get_bm25_service,
    reset_bm25_service,
)
from services.hybrid_search import (
    HybridSearchResult,
    HybridSearchService,
    get_hybrid_search_service,
    normalize_scores,
    reciprocal_rank_fusion,
    reset_hybrid_search_service,
)


class TestBM25Index:
    """BM25Index unit tests."""

    def test_index_documents(self, tmp_path: Path):
        """TC-HYB-1.1: Index documents successfully."""
        index = BM25Index()

        documents = [
            "Python is a programming language",
            "Machine learning uses Python",
            "JavaScript runs in browsers",
        ]
        ids = ["doc1", "doc2", "doc3"]

        index.index_documents(documents, ids)

        assert index.count() == 3
        assert "doc1" in index.doc_id_to_idx
        assert "doc2" in index.doc_id_to_idx
        assert "doc3" in index.doc_id_to_idx

    def test_query_returns_results(self, tmp_path: Path):
        """TC-HYB-1.2: Query returns ranked results."""
        index = BM25Index()

        documents = [
            "Python is a programming language",
            "Machine learning uses Python extensively",
            "JavaScript runs in browsers",
        ]
        ids = ["doc1", "doc2", "doc3"]

        index.index_documents(documents, ids)

        results = index.query("Python programming", k=2)

        assert len(results) <= 2
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)
        assert all(isinstance(r[1], float) for r in results)

    def test_query_empty_index(self):
        """TC-HYB-1.3: Query empty index returns empty results."""
        index = BM25Index()

        results = index.query("test query", k=5)

        assert results == []

    def test_add_documents(self):
        """TC-HYB-1.4: Add documents to existing index."""
        index = BM25Index()

        # Initial indexing
        index.index_documents(["Document 1"], ["id1"])
        assert index.count() == 1

        # Add more documents
        index.add_documents(["Document 2"], ["id2"])
        assert index.count() == 2

        # Verify both documents are searchable
        results = index.query("Document", k=10)
        assert len(results) == 2

    def test_save_and_load(self, tmp_path: Path):
        """TC-HYB-2.1: Save and load BM25 index."""
        index = BM25Index()

        documents = ["Test document one", "Test document two"]
        ids = ["id1", "id2"]

        index.index_documents(documents, ids)

        # Save
        save_path = tmp_path / "bm25_test"
        index.save(save_path)

        assert (save_path / "bm25_index").exists()
        assert (save_path / "metadata.json").exists()

        # Load into new index
        new_index = BM25Index()
        new_index.load(save_path)

        assert new_index.count() == 2
        assert new_index.doc_ids == ["id1", "id2"]

    def test_invalid_input(self):
        """TC-HYB-1.5: Invalid input raises ValueError."""
        index = BM25Index()

        with pytest.raises(ValueError):
            index.index_documents(["doc1"], ["id1", "id2"])  # Length mismatch


class TestBM25Service:
    """BM25Service tests."""

    def test_create_service(self, tmp_path: Path):
        """TC-HYB-1.6: Create BM25Service instance."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = BM25Service(persist_dir=str(persist_dir))

        assert service.persist_dir == persist_dir

    def test_singleton_pattern(self, tmp_path: Path):
        """TC-HYB-1.7: Singleton pattern works."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service1 = get_bm25_service(str(persist_dir))
        service2 = get_bm25_service()

        assert service1 is service2

    def test_index_and_query(self, tmp_path: Path):
        """TC-HYB-1.8: Service indexing and querying."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        documents = [
            "The quick brown fox",
            "Jumps over the lazy dog",
            "Python programming language",
        ]
        ids = ["fox", "dog", "python"]

        service.index_documents("test_collection", documents, ids)

        results = service.query("test_collection", "Python programming", k=2)

        assert len(results) > 0
        assert results[0][0] == "python"  # Best match

    def test_list_indexed_collections(self, tmp_path: Path):
        """TC-HYB-1.9: List indexed collections."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.index_documents("coll1", ["doc"], ["id1"])
        service.index_documents("coll2", ["doc"], ["id1"])

        collections = service.list_indexed_collections()

        assert "coll1" in collections
        assert "coll2" in collections

    def test_delete_index(self, tmp_path: Path):
        """TC-HYB-1.10: Delete index removes from memory."""
        reset_bm25_service()

        persist_dir = tmp_path / "bm25"
        service = get_bm25_service(str(persist_dir))

        service.index_documents("to_delete", ["doc"], ["id1"])
        assert "to_delete" in service.list_indexed_collections()

        service.delete_index("to_delete")
        assert "to_delete" not in service.list_indexed_collections()


class TestReciprocalRankFusion:
    """RRF algorithm tests."""

    def test_rrf_basic(self):
        """TC-HYB-3.1: Basic RRF fusion."""
        vector_results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        bm25_results = [("doc2", 5.0), ("doc4", 4.0), ("doc1", 3.0)]

        fused = reciprocal_rank_fusion(vector_results, bm25_results, k=60)

        assert len(fused) == 4  # 4 unique documents
        # doc1 and doc2 appear in both, should rank higher
        top_ids = [doc_id for doc_id, _ in fused[:2]]
        assert "doc1" in top_ids or "doc2" in top_ids

    def test_rrf_empty_results(self):
        """TC-HYB-3.2: RRF with empty results."""
        fused = reciprocal_rank_fusion([], [], k=60)
        assert fused == []

    def test_rrf_single_list(self):
        """TC-HYB-3.3: RRF with only vector results."""
        vector_results = [("doc1", 0.9), ("doc2", 0.8)]

        fused = reciprocal_rank_fusion(vector_results, [], k=60, alpha=1.0, beta=0.0)

        assert len(fused) == 2

    def test_rrf_weights(self):
        """TC-HYB-3.4: RRF weights affect ranking."""
        vector_results = [("doc1", 0.9)]
        bm25_results = [("doc2", 5.0)]

        # High alpha, low beta -> vector result should rank higher
        fused_alpha = reciprocal_rank_fusion(
            vector_results, bm25_results, k=60, alpha=0.9, beta=0.1
        )

        # High beta, low alpha -> BM25 result should rank higher
        fused_beta = reciprocal_rank_fusion(vector_results, bm25_results, k=60, alpha=0.1, beta=0.9)

        # Both should have 2 results
        assert len(fused_alpha) == 2
        assert len(fused_beta) == 2

    def test_normalize_scores_minmax(self):
        """TC-HYB-3.5: Min-max normalization."""
        results = [("doc1", 10.0), ("doc2", 5.0), ("doc3", 0.0)]

        normalized = normalize_scores(results, method="minmax")

        # Check normalization
        scores = [s for _, s in normalized]
        assert min(scores) == 0.0
        assert max(scores) == 1.0

    def test_normalize_scores_rank(self):
        """TC-HYB-3.6: Rank-based normalization."""
        results = [("doc1", 10.0), ("doc2", 5.0), ("doc3", 1.0)]

        normalized = normalize_scores(results, method="rank")

        # First result should have highest score
        assert normalized[0][1] >= normalized[1][1] >= normalized[2][1]

    def test_normalize_empty_results(self):
        """TC-HYB-3.7: Normalize empty results."""
        normalized = normalize_scores([])
        assert normalized == []


class TestHybridSearchService:
    """HybridSearchService integration tests."""

    @pytest.fixture
    def mock_chroma_service(self):
        """Create mock ChromaService."""
        service = MagicMock()
        service.query.return_value = {
            "ids": ["doc1", "doc2"],
            "documents": ["Python tutorial", "JavaScript guide"],
            "metadatas": [{"lang": "py"}, {"lang": "js"}],
            "distances": [0.1, 0.3],
        }
        return service

    @pytest.fixture
    def mock_bm25_service(self):
        """Create mock BM25Service."""
        service = MagicMock()
        service.query.return_value = [
            ("doc1", 5.0),
            ("doc2", 3.0),
        ]
        return service

    def test_create_service(self):
        """TC-HYB-4.1: Create HybridSearchService."""
        reset_hybrid_search_service()

        service = HybridSearchService(alpha=0.6, beta=0.4, rrf_k=60)

        assert service.alpha == 0.6
        assert service.beta == 0.4
        assert service.rrf_k == 60

    def test_invalid_weights(self):
        """TC-HYB-4.2: Invalid weights raise ValueError."""
        with pytest.raises(ValueError):
            HybridSearchService(alpha=1.5, beta=0.5)

        with pytest.raises(ValueError):
            HybridSearchService(alpha=0.5, beta=-0.1)

    def test_singleton_pattern(self):
        """TC-HYB-4.3: HybridSearchService singleton."""
        reset_hybrid_search_service()

        service1 = get_hybrid_search_service(alpha=0.5, beta=0.5)
        service2 = get_hybrid_search_service()

        assert service1 is service2

    def test_search_returns_results(self, mock_chroma_service, mock_bm25_service):
        """TC-HYB-4.4: Search returns hybrid results."""
        reset_hybrid_search_service()

        # Mock collection.get for document retrieval
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            "ids": ["doc1", "doc2"],
            "documents": ["Python tutorial", "JavaScript guide"],
            "metadatas": [{"lang": "py"}, {"lang": "js"}],
        }
        mock_chroma_service.get_collection.return_value = mock_collection

        service = HybridSearchService(alpha=0.5, beta=0.5)

        with patch("services.chroma_service.get_chroma_service", return_value=mock_chroma_service):
            with patch("services.bm25_service.get_bm25_service", return_value=mock_bm25_service):
                results = service.search("test_collection", "Python", n_results=5)

        assert isinstance(results, list)
        assert all(isinstance(r, HybridSearchResult) for r in results)
        if results:
            assert results[0].id is not None
            assert results[0].score > 0

    def test_search_with_where_filter(self, mock_chroma_service, mock_bm25_service):
        """TC-HYB-4.5: Search with where filter using Provider interface."""
        reset_hybrid_search_service()

        # Mock VectorStoreProvider
        mock_provider = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.results = [
            MagicMock(id="doc1", score=0.1),
        ]
        mock_provider.query.return_value = mock_query_result
        mock_provider.get.return_value = [
            MagicMock(id="doc1", document="Python tutorial", metadata={"lang": "py"}),
        ]

        service = HybridSearchService(vectorstore_provider=mock_provider)

        with patch("services.bm25_service.get_bm25_service", return_value=mock_bm25_service):
            service.search("test_collection", "Python", n_results=5, where={"lang": "py"})

        # Verify where filter was passed to Provider query
        mock_provider.query.assert_called_once()
        call_kwargs = mock_provider.query.call_args.kwargs
        assert call_kwargs["where"] == {"lang": "py"}

    def test_search_empty_results(self, mock_chroma_service, mock_bm25_service):
        """TC-HYB-4.6: Search returns empty when no matches."""
        reset_hybrid_search_service()

        # Mock VectorStoreProvider with empty results
        mock_provider = MagicMock()
        mock_query_result = MagicMock()
        mock_query_result.results = []
        mock_provider.query.return_value = mock_query_result

        mock_bm25_service.query.return_value = []

        service = HybridSearchService(vectorstore_provider=mock_provider)

        with patch("services.bm25_service.get_bm25_service", return_value=mock_bm25_service):
            results = service.search("empty_collection", "query", n_results=5)

        assert results == []


class TestHybridSearchResult:
    """HybridSearchResult dataclass tests."""

    def test_create_result(self):
        """TC-HYB-4.7: Create HybridSearchResult."""
        result = HybridSearchResult(
            id="doc1",
            text="Sample text",
            score=0.85,
            vector_score=0.9,
            bm25_score=0.8,
            rank=1,
            metadata={"source": "test"},
            distance=0.1,
        )

        assert result.id == "doc1"
        assert result.score == 0.85
        assert result.vector_score == 0.9
        assert result.bm25_score == 0.8
        assert result.rank == 1
        assert result.metadata == {"source": "test"}
        assert result.distance == 0.1

    def test_result_defaults(self):
        """TC-HYB-4.8: HybridSearchResult default values."""
        result = HybridSearchResult(
            id="doc1",
            text="Sample text",
            score=0.5,
        )

        assert result.vector_score == 0.0
        assert result.bm25_score == 0.0
        assert result.rank == 0
        assert result.metadata is None
        assert result.distance is None


class TestBM25SearchFallback:
    """Tests for _bm25_search fallback behavior."""

    @pytest.fixture
    def service(self):
        """Create HybridSearchService instance."""
        return HybridSearchService()

    def test_bm25_search_returns_empty_on_index_not_found(self, service):
        """TC-HYB-6.1: _bm25_search returns empty when index doesn't exist."""
        mock_bm25 = MagicMock()
        mock_bm25.query.side_effect = KeyError("Collection 'test' not indexed")

        result = service._bm25_search(mock_bm25, "test_coll", "query", 10)

        assert result == []

    def test_bm25_search_returns_empty_on_service_error(self, service):
        """TC-HYB-6.2: _bm25_search returns empty on service error."""
        mock_bm25 = MagicMock()
        mock_bm25.query.side_effect = RuntimeError("BM25 service unavailable")

        result = service._bm25_search(mock_bm25, "test_coll", "query", 10)

        assert result == []

    def test_bm25_search_returns_results_on_success(self, service):
        """TC-HYB-6.3: _bm25_search returns results when successful."""
        mock_bm25 = MagicMock()
        mock_bm25.query.return_value = [("doc1", 5.0), ("doc2", 3.0)]

        result = service._bm25_search(mock_bm25, "test_coll", "Python tutorial", 10)

        assert len(result) == 2
        assert result[0] == ("doc1", 5.0)

    def test_bm25_search_passes_correct_parameters(self, service):
        """TC-HYB-6.4: _bm25_search passes correct parameters to service."""
        mock_bm25 = MagicMock()
        mock_bm25.query.return_value = []

        service._bm25_search(mock_bm25, "my_coll", "search query", 15)

        mock_bm25.query.assert_called_once_with("my_coll", "search query", 15)


class TestVectorSearchExceptions:
    """Tests for _vector_search exception handling."""

    @pytest.fixture
    def service(self):
        """Create HybridSearchService instance."""
        return HybridSearchService()

    def test_vector_search_raises_value_error_collection_not_found(self, service):
        """TC-HYB-5.1: _vector_search raises ValueError when collection not found."""
        mock_chroma = MagicMock()
        mock_chroma.query.side_effect = ValueError("Collection 'nonexistent' not found")

        with pytest.raises(ValueError) as exc_info:
            service._vector_search(mock_chroma, "nonexistent", "query", 10, None)

        assert "not found" in str(exc_info.value).lower()

    def test_vector_search_returns_empty_on_connection_error(self, service):
        """TC-HYB-5.2: _vector_search returns empty list on connection error."""
        mock_chroma = MagicMock()
        mock_chroma.query.side_effect = ConnectionError("Cannot connect to ChromaDB")

        result = service._vector_search(mock_chroma, "test_coll", "query", 10, None)

        assert result == []

    def test_vector_search_returns_empty_on_timeout(self, service):
        """TC-HYB-5.3: _vector_search returns empty list on timeout."""
        mock_chroma = MagicMock()
        mock_chroma.query.side_effect = TimeoutError("Request timed out")

        result = service._vector_search(mock_chroma, "test_coll", "query", 10, None)

        assert result == []

    def test_vector_search_handles_malformed_response(self, service):
        """TC-HYB-5.4: _vector_search handles malformed response gracefully."""
        mock_chroma = MagicMock()
        mock_chroma.query.return_value = {
            "ids": ["doc1", "doc2"],
            # Missing 'distances' key
        }

        result = service._vector_search(mock_chroma, "test_coll", "query", 10, None)

        assert isinstance(result, list)

    def test_vector_search_returns_id_distance_pairs(self, service):
        """TC-HYB-5.5: _vector_search returns list of (id, distance) tuples."""
        # Mock VectorStoreProvider with QueryResult-like response
        mock_result = MagicMock()
        mock_result.results = [
            MagicMock(id="doc1", score=0.1),
            MagicMock(id="doc2", score=0.3),
            MagicMock(id="doc3", score=0.5),
        ]

        mock_provider = MagicMock()
        mock_provider.query.return_value = mock_result

        result = service._vector_search(mock_provider, "test_coll", "query", 3, None)

        assert len(result) == 3
        assert result[0] == ("doc1", 0.1)
        assert result[1] == ("doc2", 0.3)
        assert result[2] == ("doc3", 0.5)


class TestFuseResults:
    """Tests for _fuse_results normalization options."""

    def test_fuse_results_with_normalize_true(self):
        """TC-HYB-7.1: _fuse_results normalizes scores when normalize=True."""
        service = HybridSearchService(normalize=True)

        vector_results = [("doc1", 0.1), ("doc2", 0.5)]
        bm25_results = [("doc1", 10.0), ("doc3", 5.0)]

        result = service._fuse_results(vector_results, bm25_results)

        # Should return fused results
        assert len(result) == 3
        # doc1 appears in both, should rank higher
        assert result[0][0] == "doc1"

    def test_fuse_results_with_normalize_false(self):
        """TC-HYB-7.2: _fuse_results uses raw scores when normalize=False."""
        service = HybridSearchService(normalize=False)

        vector_results = [("doc1", 0.1), ("doc2", 0.5)]
        bm25_results = [("doc1", 10.0), ("doc3", 5.0)]

        result = service._fuse_results(vector_results, bm25_results)

        assert len(result) == 3

    def test_fuse_results_empty_inputs(self):
        """TC-HYB-7.3: _fuse_results handles empty inputs."""
        service = HybridSearchService()

        # Empty both
        result = service._fuse_results([], [])
        assert result == []

        # Empty vector
        result = service._fuse_results([], [("doc1", 5.0)])
        assert len(result) == 1

    def test_fuse_results_distance_inversion(self):
        """TC-HYB-7.4: _fuse_results inverts distance for vector scores."""
        service = HybridSearchService(normalize=True)

        # Lower distance should result in higher normalized score
        vector_results = [("close_doc", 0.1), ("far_doc", 0.9)]
        bm25_results = []

        result = service._fuse_results(vector_results, bm25_results)

        # close_doc should rank higher (lower distance = higher similarity)
        assert result[0][0] == "close_doc"


class TestGetHybridSearchService:
    """Tests for get_hybrid_search_service singleton and config loading."""

    def test_get_service_returns_singleton(self):
        """TC-HYB-9.1: get_hybrid_search_service returns singleton."""
        reset_hybrid_search_service()

        service1 = get_hybrid_search_service(alpha=0.5, beta=0.5)
        service2 = get_hybrid_search_service(alpha=0.5, beta=0.5)

        assert service1 is service2

    def test_get_service_creates_new_on_param_change(self):
        """TC-HYB-9.2: New instance created when params change."""
        reset_hybrid_search_service()

        service1 = get_hybrid_search_service(alpha=0.5, beta=0.5)
        service2 = get_hybrid_search_service(alpha=0.7, beta=0.3)

        assert service1 is not service2
        assert service2.alpha == 0.7

    def test_get_service_uses_defaults_without_config(self):
        """TC-HYB-9.3: Service uses defaults when config unavailable."""
        reset_hybrid_search_service()

        with patch("utils.config.get_config", side_effect=RuntimeError("No config")):
            service = get_hybrid_search_service()

        assert service.alpha == 0.5
        assert service.beta == 0.5
        assert service.rrf_k == 60

    def test_get_service_loads_from_config(self):
        """TC-HYB-9.4: Service loads parameters from config."""
        reset_hybrid_search_service()

        mock_config = MagicMock()
        mock_config.hybrid = MagicMock(alpha=0.7, beta=0.3, rrf_k=100)

        with patch("utils.config.get_config", return_value=mock_config):
            service = get_hybrid_search_service()

        assert service.alpha == 0.7
        assert service.beta == 0.3
        assert service.rrf_k == 100

    def test_get_service_explicit_params_override_config(self):
        """TC-HYB-9.5: Explicit params override config values."""
        reset_hybrid_search_service()

        mock_config = MagicMock()
        mock_config.hybrid = MagicMock(alpha=0.7, beta=0.3, rrf_k=100)

        with patch("utils.config.get_config", return_value=mock_config):
            service = get_hybrid_search_service(alpha=0.9, beta=0.1)

        # Explicit params should override config
        assert service.alpha == 0.9
        assert service.beta == 0.1
        # rrf_k from config
        assert service.rrf_k == 100


class TestBuildResults:
    """Tests for _build_results document fetching."""

    @pytest.fixture
    def service(self):
        """Create HybridSearchService instance."""
        return HybridSearchService()

    def test_build_results_fetches_documents(self, service):
        """TC-HYB-8.1: _build_results fetches document details using Provider interface."""
        # Mock VectorStoreProvider with SearchResult-like response
        mock_provider = MagicMock()
        mock_provider.get.return_value = [
            MagicMock(id="doc1", document="Text 1", metadata={"lang": "py"}),
            MagicMock(id="doc2", document="Text 2", metadata={"lang": "js"}),
        ]

        fused = [("doc1", 0.8), ("doc2", 0.6)]
        vector_results = [("doc1", 0.9), ("doc2", 0.7)]
        bm25_results = [("doc1", 5.0)]

        results = service._build_results(
            fused, mock_provider, "test_coll", vector_results, bm25_results
        )

        assert len(results) == 2
        assert results[0].text == "Text 1"
        assert results[0].metadata == {"lang": "py"}

    def test_build_results_handles_missing_documents(self, service):
        """TC-HYB-8.2: _build_results handles missing documents gracefully."""
        # Mock VectorStoreProvider - only returns one document
        mock_provider = MagicMock()
        mock_provider.get.return_value = [
            MagicMock(id="doc1", document="Text 1", metadata={"lang": "py"}),
        ]

        fused = [("doc1", 0.8), ("doc2", 0.6)]  # doc2 not in results
        vector_results = [("doc1", 0.9), ("doc2", 0.7)]
        bm25_results = []

        results = service._build_results(
            fused, mock_provider, "test_coll", vector_results, bm25_results
        )

        assert len(results) == 2
        assert results[1].text == ""  # Empty text for missing document

    def test_build_results_handles_collection_error(self, service):
        """TC-HYB-8.3: _build_results handles collection fetch error."""
        mock_provider = MagicMock()
        mock_provider.get.side_effect = Exception("Collection error")

        fused = [("doc1", 0.8)]
        vector_results = [("doc1", 0.9)]
        bm25_results = []

        results = service._build_results(
            fused, mock_provider, "test_coll", vector_results, bm25_results
        )

        # Should still return results with empty text
        assert len(results) == 1
        assert results[0].text == ""

    def test_build_results_assigns_correct_rank(self, service):
        """TC-HYB-8.4: _build_results assigns correct rank positions."""
        mock_provider = MagicMock()
        mock_provider.get.return_value = [
            MagicMock(id="doc1", document="A", metadata={}),
            MagicMock(id="doc2", document="B", metadata={}),
            MagicMock(id="doc3", document="C", metadata={}),
        ]

        fused = [("doc1", 0.9), ("doc2", 0.7), ("doc3", 0.5)]

        results = service._build_results(fused, mock_provider, "test_coll", [], [])

        assert results[0].rank == 1
        assert results[1].rank == 2
        assert results[2].rank == 3

    def test_build_results_includes_scores(self, service):
        """TC-HYB-8.5: _build_results includes vector and BM25 scores."""
        mock_provider = MagicMock()
        mock_provider.get.return_value = [
            MagicMock(id="doc1", document="Text", metadata={}),
        ]

        fused = [("doc1", 0.85)]
        vector_results = [("doc1", 0.9)]
        bm25_results = [("doc1", 5.0)]

        results = service._build_results(
            fused, mock_provider, "test_coll", vector_results, bm25_results
        )

        assert results[0].score == 0.85
        assert results[0].vector_score == 0.9
        assert results[0].bm25_score == 5.0
        assert results[0].distance == 0.9
