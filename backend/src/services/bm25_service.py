"""BM25 service for lexical search.

This module provides a BM25-based indexing and search service using the bm25s library:
- Per-collection BM25 indexes
- Document indexing and querying
- Persistent storage support
- Thread-safe operations
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
        self.corpus = self.retriever.corpus if hasattr(self.retriever, 'corpus') else []
        
        logger.debug(f"Loaded BM25 index from {path}")
    
    def count(self) -> int:
        """Return the number of documents in the index.
        
        Returns:
            Number of indexed documents.
        """
        return len(self.doc_ids)


class BM25Service:
    """BM25 indexing and search service.
    
    Provides BM25-based lexical search with:
    - Per-collection index management
    - Document indexing and querying
    - Persistent storage support
    - Thread-safe singleton pattern
    
    Example:
        >>> service = get_bm25_service("./data/bm25")
        >>> service.index_documents("my_collection", ["doc1 text"], ["id1"])
        >>> results = service.query("my_collection", "search query", k=5)
    """
    
    def __init__(self, persist_dir: str) -> None:
        """Initialize BM25Service.
        
        Args:
            persist_dir: Directory for persistent storage of BM25 indexes.
        """
        self._persist_dir = Path(persist_dir)
        self._indexes: dict[str, BM25Index] = {}
    
    @property
    def persist_dir(self) -> Path:
        """Get the persist directory."""
        return self._persist_dir
    
    def _get_index_path(self, collection_name: str) -> Path:
        """Get the path for a collection's BM25 index.
        
        Args:
            collection_name: Name of the collection.
            
        Returns:
            Path to the collection's index directory.
        """
        return self._persist_dir / collection_name
    
    def get_or_create_index(self, collection_name: str) -> BM25Index:
        """Get or create a BM25 index for a collection.
        
        Args:
            collection_name: Name of the collection.
            
        Returns:
            BM25Index instance for the collection.
        """
        if collection_name not in self._indexes:
            self._indexes[collection_name] = BM25Index()
            
            # Try to load existing index
            index_path = self._get_index_path(collection_name)
            if (index_path / "bm25_index").exists():
                try:
                    self._indexes[collection_name].load(index_path)
                    logger.info(f"Loaded existing BM25 index for collection '{collection_name}'")
                except Exception as e:
                    logger.warning(f"Failed to load BM25 index: {e}")
        
        return self._indexes[collection_name]
    
    def index_documents(
        self,
        collection_name: str,
        documents: list[str],
        ids: list[str],
        stopwords: str = "en",
    ) -> None:
        """Index documents for a collection.
        
        Args:
            collection_name: Name of the collection.
            documents: List of document texts to index.
            ids: List of unique document IDs.
            stopwords: Stopwords language (default: "en").
        """
        if not documents:
            logger.warning("No documents to index")
            return
        
        index = self.get_or_create_index(collection_name)
        index.index_documents(documents, ids, stopwords)
        
        logger.info(f"Indexed {len(documents)} documents for collection '{collection_name}'")
    
    def add_documents(
        self,
        collection_name: str,
        documents: list[str],
        ids: list[str],
        stopwords: str = "en",
    ) -> None:
        """Add documents to an existing collection index.
        
        Args:
            collection_name: Name of the collection.
            documents: List of document texts to add.
            ids: List of unique document IDs.
            stopwords: Stopwords language (default: "en").
        """
        if not documents:
            logger.warning("No documents to add")
            return
        
        index = self.get_or_create_index(collection_name)
        index.add_documents(documents, ids, stopwords)
        
        logger.info(f"Added {len(documents)} documents to collection '{collection_name}'")
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        k: int = 10,
    ) -> list[tuple[str, float]]:
        """Query a collection's BM25 index.
        
        Args:
            collection_name: Name of the collection to query.
            query_text: The search query.
            k: Number of results to return.
            
        Returns:
            List of (doc_id, score) tuples, sorted by score descending.
        """
        index = self.get_or_create_index(collection_name)
        return index.query(query_text, k)
    
    def save_index(self, collection_name: str) -> None:
        """Save a collection's BM25 index to disk.
        
        Args:
            collection_name: Name of the collection.
        """
        if collection_name not in self._indexes:
            logger.warning(f"No index found for collection '{collection_name}'")
            return
        
        index_path = self._get_index_path(collection_name)
        self._indexes[collection_name].save(index_path)
        logger.info(f"Saved BM25 index for collection '{collection_name}'")
    
    def load_index(self, collection_name: str) -> bool:
        """Load a collection's BM25 index from disk.
        
        Args:
            collection_name: Name of the collection.
            
        Returns:
            True if index was loaded successfully, False otherwise.
        """
        index_path = self._get_index_path(collection_name)
        if not (index_path / "bm25_index").exists():
            logger.debug(f"No saved index found for collection '{collection_name}'")
            return False
        
        try:
            index = self.get_or_create_index(collection_name)
            index.load(index_path)
            return True
        except Exception as e:
            logger.error(f"Failed to load index for '{collection_name}': {e}")
            return False
    
    def delete_index(self, collection_name: str) -> None:
        """Delete a collection's BM25 index from memory and disk.
        
        Args:
            collection_name: Name of the collection.
        """
        # Remove from memory
        if collection_name in self._indexes:
            del self._indexes[collection_name]
        
        # Remove from disk
        import shutil
        index_path = self._get_index_path(collection_name)
        if index_path.exists():
            shutil.rmtree(index_path)
        
        logger.info(f"Deleted BM25 index for collection '{collection_name}'")
    
    def count(self, collection_name: str) -> int:
        """Count documents in a collection's BM25 index.
        
        Args:
            collection_name: Name of the collection.
            
        Returns:
            Number of indexed documents.
        """
        if collection_name not in self._indexes:
            return 0
        return self._indexes[collection_name].count()
    
    def list_indexed_collections(self) -> list[str]:
        """List collections with BM25 indexes in memory.
        
        Returns:
            List of collection names.
        """
        return list(self._indexes.keys())
    
    def reset(self) -> None:
        """Reset all indexes (for testing).
        
        Warning: This deletes all in-memory indexes but not disk files.
        """
        self._indexes.clear()
        logger.warning("Reset BM25Service - all in-memory indexes cleared")


# Singleton instance
_instance: BM25Service | None = None


def get_bm25_service(persist_dir: str | None = None) -> BM25Service:
    """Get the singleton BM25Service instance.
    
    Args:
        persist_dir: Directory for persistent storage. Required on first call.
                     If None, uses the previously configured directory or config.
    
    Returns:
        BM25Service singleton instance
        
    Raises:
        ValueError: If persist_dir is not provided on first call and no config exists
    """
    global _instance
    
    if _instance is not None:
        return _instance
    
    # First call - need persist_dir
    if persist_dir is None:
        try:
            from utils.config import get_config
            persist_dir = get_config().hybrid.bm25_persist_dir
        except (RuntimeError, AttributeError):
            raise ValueError(
                "persist_dir must be provided on first call to get_bm25_service(), "
                "or configuration must be loaded with hybrid settings."
            )
    
    _instance = BM25Service(persist_dir=persist_dir)
    return _instance


def reset_bm25_service() -> None:
    """Reset the singleton instance (for testing purposes)."""
    global _instance
    _instance = None
    logger.debug("BM25Service singleton reset")