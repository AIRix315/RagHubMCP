"""BM25 lexical search implementation for Hybrid Retrieval.

This module provides BM25 indexing and search functionality moved from
the deprecated services module. It is used internally by HybridRetriever
and follows the Pipeline architecture (RULE-1).

Reference:
- RULE.md (RULE-3: 禁止在模块中直接依赖具体实现)
- Docs/12-V2-Blueprint.md (Module 1.1)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import bm25s

logger = logging.getLogger(__name__)

# Collection index storage: collection_name -> BM25Index
_indexes: dict[str, BM25Index] = {}


class BM25Index:
    """BM25 index for a single collection.

    Stores the BM25 retriever, document corpus, and document IDs.
    """

    def __init__(self) -> None:
        """Initialize an empty BM25 index."""
        self.retriever: bm25s.BM25 | None = None
        self.corpus: list[str] = []
        self.doc_ids: list[str] = []
        self.doc_id_to_idx: dict[str, int] = {}

    def index_documents(
        self,
        documents: list[str],
        ids: list[str],
        stopwords: str = "en",
    ) -> None:
        """Index documents for BM25 search.

        Args:
            documents: List of document texts to index.
            ids: List of unique document IDs.
            stopwords: Stopwords language (default: "en").
        """
        if len(documents) != len(ids):
            raise ValueError("documents and ids must have the same length")

        # Build ID mapping
        self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(ids)}
        self.corpus = documents
        self.doc_ids = ids

        # Tokenize and index
        corpus_tokens = bm25s.tokenize(documents, stopwords=stopwords)
        self.retriever = bm25s.BM25()
        self.retriever.index(corpus_tokens)

        logger.debug(f"Indexed {len(documents)} documents for BM25")

    def add_documents(
        self,
        documents: list[str],
        ids: list[str],
        stopwords: str = "en",
    ) -> None:
        """Add documents to existing index (rebuilds the entire index).

        Note: BM25 doesn't support incremental updates, so we rebuild.

        Args:
            documents: List of document texts to add.
            ids: List of unique document IDs.
            stopwords: Stopwords language (default: "en").
        """
        # Check for duplicate IDs
        for doc_id in ids:
            if doc_id in self.doc_id_to_idx:
                logger.warning(f"Document ID '{doc_id}' already exists, will be replaced")

        # Merge with existing documents
        all_docs = self.corpus.copy()
        all_ids = self.doc_ids.copy()

        # Update or append
        for doc, doc_id in zip(documents, ids):
            if doc_id in self.doc_id_to_idx:
                # Replace existing
                idx = self.doc_id_to_idx[doc_id]
                all_docs[idx] = doc
            else:
                # Append new
                all_docs.append(doc)
                all_ids.append(doc_id)

        # Rebuild index
        self.index_documents(all_docs, all_ids, stopwords)

    def query(
        self,
        query_text: str,
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Query the BM25 index.

        Args:
            query_text: The search query.
            k: Number of results to return.

        Returns:
            List of (doc_id, score) tuples, sorted by score descending.
        """
        if self.retriever is None:
            logger.warning("Index not initialized, returning empty results")
            return []

        # Limit k to the number of documents
        k = min(k, len(self.doc_ids))
        if k == 0:
            return []

        # Tokenize query
        query_tokens = bm25s.tokenize(query_text, show_progress=False)

        # Retrieve results
        results, scores = self.retriever.retrieve(query_tokens, k=k)

        # results shape: (1, k), scores shape: (1, k)
        doc_indices = results[0]
        doc_scores = scores[0]

        # Convert to (doc_id, score) tuples
        output = []
        for idx, score in zip(doc_indices, doc_scores):
            if idx < len(self.doc_ids):
                doc_id = self.doc_ids[idx]
                output.append((doc_id, float(score)))

        return output

    def save(self, path: Path) -> None:
        """Save the BM25 index to disk.

        Args:
            path: Directory path to save the index.
        """
        if self.retriever is None:
            raise ValueError("No index to save")

        path.mkdir(parents=True, exist_ok=True)

        # Save BM25 retriever
        self.retriever.save(str(path / "bm25_index"), corpus=self.corpus)

        # Save document IDs mapping
        metadata = {
            "doc_ids": self.doc_ids,
        }
        with open(path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f)

        logger.debug(f"Saved BM25 index to {path}")

    def load(self, path: Path) -> None:
        """Load the BM25 index from disk.

        Args:
            path: Directory path to load the index from.
        """
        if not path.exists():
            raise FileNotFoundError(f"Index path not found: {path}")

        # Load BM25 retriever with corpus
        self.retriever = bm25s.BM25.load(str(path / "bm25_index"), load_corpus=True)

        # Load document IDs
        with open(path / "metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)

        self.doc_ids = metadata["doc_ids"]
        self.doc_id_to_idx = {doc_id: idx for idx, doc_id in enumerate(self.doc_ids)}
        self.corpus = self.retriever.corpus if hasattr(self.retriever, "corpus") else []

        logger.debug(f"Loaded BM25 index from {path}")

    def count(self) -> int:
        """Return the number of documents in the index.

        Returns:
            Number of indexed documents.
        """
        return len(self.doc_ids)


class BM25Service:
    """BM25 indexing and search service integrated into Pipeline.

    This class provides the same interface as the deprecated services.BM25Service
    but is now part of the pipeline module for RULE-1 compliance.

    The service manages per-collection BM25 indexes and supports:
    - Indexing documents for lexical search
    - Querying with BM25 scoring
    - Persistent storage of indexes
    """

    def __init__(self, persist_dir: str | Path | None = None) -> None:
        """Initialize BM25 service.

        Args:
            persist_dir: Optional directory for persistent index storage.
        """
        self._persist_dir = Path(persist_dir) if persist_dir else None
        self._indexes: dict[str, BM25Index] = {}

    def _get_collection_index(self, collection: str) -> BM25Index:
        """Get or create BM25 index for a collection.

        Args:
            collection: Collection name.

        Returns:
            BM25Index for the collection.
        """
        if collection not in self._indexes:
            self._indexes[collection] = BM25Index()
        return self._indexes[collection]

    def index(
        self,
        collection: str,
        documents: list[str],
        ids: list[str],
        stopwords: str = "en",
    ) -> None:
        """Index documents for a collection.

        Args:
            collection: Collection name.
            documents: List of document texts.
            ids: List of document IDs.
            stopwords: Stopwords language.
        """
        index = self._get_collection_index(collection)
        index.index_documents(documents, ids, stopwords)

        # Save to disk if persist_dir is set
        if self._persist_dir:
            index.save(self._persist_dir / collection)

    def query(
        self,
        collection: str,
        query: str,
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Query BM25 index for a collection.

        Args:
            collection: Collection name.
            query: Query text.
            k: Number of results.

        Returns:
            List of (doc_id, score) tuples.
        """
        # Load from disk if persist_dir is set and not in memory
        if self._persist_dir and collection not in self._indexes:
            index_path = self._persist_dir / collection
            if index_path.exists():
                bm25_index = BM25Index()
                try:
                    bm25_index.load(index_path)
                    self._indexes[collection] = bm25_index
                except Exception as e:
                    logger.warning(f"Failed to load BM25 index for {collection}: {e}")

        index = self._get_collection_index(collection)
        return index.query(query, k)

    def count(self, collection: str) -> int:
        """Return document count for a collection.

        Args:
            collection: Collection name.

        Returns:
            Number of indexed documents.
        """
        index = self._get_collection_index(collection)
        return index.count()

    def clear(self, collection: str) -> None:
        """Clear the index for a collection.

        Args:
            collection: Collection name.
        """
        if collection in self._indexes:
            del self._indexes[collection]

    def list_collections(self) -> list[str]:
        """List all collections with indexes.

        Returns:
            List of collection names.
        """
        return list(self._indexes.keys())


# Singleton instance
_bm25_service: BM25Service | None = None


def get_bm25_service(persist_dir: str | Path | None = None) -> BM25Service:
    """Get the singleton BM25Service instance.

    Args:
        persist_dir: Optional directory for persistent index storage.
            Only used on first call to initialize the service.

    Returns:
        BM25Service singleton instance.
    """
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25Service(persist_dir=persist_dir)
    return _bm25_service


def reset_bm25_service() -> None:
    """Reset the BM25Service singleton.

    This is primarily useful for testing.
    """
    global _bm25_service
    _bm25_service = None