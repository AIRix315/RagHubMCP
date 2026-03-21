"""Incremental indexer for detecting and processing file changes.

This module provides:
- Content hash-based change detection
- Incremental add/update/delete operations
- Integration with Indexer and FileWatcher
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from src.indexer.scanner import FileScanner
from src.indexer.watcher import FileEvent, FileEventType
from src.providers.vectorstore.base import BaseVectorStoreProvider

if TYPE_CHECKING:
    from src.indexer.indexer import Indexer
    from src.utils.config import IndexerConfig

logger = logging.getLogger(__name__)


@dataclass
class IncrementalResult:
    """Result of an incremental indexing operation.

    Attributes:
        files_added: Number of new files indexed.
        files_updated: Number of files updated.
        files_deleted: Number of files removed from index.
        chunks_added: Total chunks added.
        chunks_removed: Total chunks removed.
        errors: List of error messages.
    """

    files_added: int = 0
    files_updated: int = 0
    files_deleted: int = 0
    chunks_added: int = 0
    chunks_removed: int = 0
    errors: list[str] = field(default_factory=list)


class IncrementalIndexer:
    """Handles incremental indexing based on content hash.

    Detects changes by comparing content hashes stored in metadata
    with current file content hashes.

    Workflow:
        1. New file: Index all chunks with content_hash in metadata
        2. Modified file: Remove old chunks, re-index with new hash
        3. Deleted file: Remove all chunks for that file

    Example:
        >>> from src.indexer.indexer import Indexer
        >>> from src.indexer.watcher import FileWatcher, FileEvent, FileEventType
        >>>
        >>> # Create incremental indexer
        >>> incremental = IncrementalIndexer(indexer, collection)
        >>>
        >>> # Handle events from watcher
        >>> events = [FileEvent(FileEventType.CREATED, Path("/path/to/new.py"))]
        >>> result = incremental.process_events(events)
    """

    def __init__(
        self,
        indexer: Indexer,
        vectorstore: BaseVectorStoreProvider,
        collection_name: str = "default",
        config: IndexerConfig | None = None,
    ) -> None:
        """Initialize the incremental indexer.

        Args:
            indexer: Indexer instance for indexing files.
            vectorstore: VectorStore provider for storing vectors (RULE-3 compliant).
            collection_name: Collection name to use (default: "default").
            config: Optional indexer config (uses indexer's config if None).
        """
        self._indexer = indexer
        self._vectorstore = vectorstore
        self._collection_name = collection_name
        self._config = config
        self._scanner = FileScanner(config) if config else FileScanner()

        # Import SimpleChunker as fallback
        from src.chunkers import SimpleChunker

        self._fallback_chunker = SimpleChunker(
            chunk_size=config.chunk_size if config else 500,
            overlap=config.chunk_overlap if config else 50,
        )

    def _compute_hash(self, path: Path) -> str:
        """Compute MD5 hash of a file.

        Args:
            path: Path to the file.

        Returns:
            MD5 hash as hex string, or empty string on error.
        """
        return self._scanner._compute_hash(path)

    def _get_chunks_with_fallback(self, path: Path) -> list:
        """Get chunks from indexer with fallback to SimpleChunker.

        Some AST chunkers may return empty list when tree-sitter is
        unavailable. This method falls back to SimpleChunker in such cases.

        Args:
            path: Path to the file.

        Returns:
            List of Chunk objects.
        """
        chunks = self._indexer._chunk_file(path)

        # If AST chunker returned empty but file has content, use fallback
        if not chunks:
            try:
                content = path.read_text(encoding="utf-8")
                if content.strip():
                    # Use the indexer's _get_language method to get language
                    language = self._indexer._get_language(path)
                    metadata = {
                        "source": str(path),
                        "language": language,
                        "filename": path.name,
                    }
                    chunks = self._fallback_chunker.chunk(content, metadata)
                    logger.debug(f"Used fallback chunker for {path}")
            except Exception as e:
                logger.warning(f"Failed to chunk file with fallback: {e}")

        return chunks

    def _get_chunks_by_source(self, source: str) -> list[dict]:
        """Get all chunks for a source file.

        Args:
            source: Source file path string.

        Returns:
            List of chunk dictionaries with ids, metadatas.
        """
        try:
            results = self._vectorstore.get(
                collection=self._collection_name,
                where={"source": source},
            )
            return [{"id": result.id, "metadata": result.metadata} for result in results]
        except Exception as e:
            logger.error(f"Error getting chunks for {source}: {e}")
            return []

    def _delete_chunks_by_source(self, source: str) -> int:
        """Delete all chunks for a source file.

        Args:
            source: Source file path string.

        Returns:
            Number of chunks deleted.
        """
        chunks = self._get_chunks_by_source(source)
        if not chunks:
            return 0

        ids = [c["id"] for c in chunks]
        try:
            deleted_count = self._vectorstore.delete(collection=self._collection_name, ids=ids)
            logger.debug(f"Deleted {deleted_count} chunks for {source}")
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting chunks for {source}: {e}")
            return 0

    def _has_content_changed(self, source: str, new_hash: str) -> bool:
        """Check if file content has changed.

        Args:
            source: Source file path string.
            new_hash: New content hash.

        Returns:
            True if content has changed or file is new.
        """
        chunks = self._get_chunks_by_source(source)
        if not chunks:
            return True  # New file

        # Check hash from first chunk's metadata
        old_hash = chunks[0].get("metadata", {}).get("content_hash")
        return old_hash != new_hash

    def handle_created(self, path: Path) -> int:
        """Handle a newly created file.

        Args:
            path: Path to the new file.

        Returns:
            Number of chunks created.
        """
        if not path.exists():
            logger.warning(f"File does not exist: {path}")
            return 0

        source = str(path)
        new_hash = self._compute_hash(path)

        # Check if already indexed (could be a rename)
        if not self._has_content_changed(source, new_hash):
            logger.debug(f"File already indexed with same content: {path}")
            return 0

        # Index the file
        try:
            # Get chunks from indexer with fallback
            chunks = self._get_chunks_with_fallback(path)
            if not chunks:
                return 0

            # Prepare data with content_hash in metadata
            texts = [chunk.text for chunk in chunks]
            ids = [f"{source}:{chunk.start}:{chunk.end}" for chunk in chunks]

            metadatas = []
            for chunk in chunks:
                meta = dict(chunk.metadata)
                meta["start"] = chunk.start
                meta["end"] = chunk.end
                meta["content_hash"] = new_hash  # Add content hash
                metadatas.append(meta)

            # Generate embeddings
            embeddings = self._indexer._embedding_provider.embed_batch(texts)

            # Add to vectorstore
            self._vectorstore.add(
                collection=self._collection_name,
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

            logger.info(f"Indexed {len(chunks)} chunks from new file: {path}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error indexing new file {path}: {e}")
            return 0

    def handle_modified(self, path: Path) -> tuple[int, int]:
        """Handle a modified file.

        Args:
            path: Path to the modified file.

        Returns:
            Tuple of (chunks_removed, chunks_added).
        """
        if not path.exists():
            logger.warning(f"File does not exist: {path}")
            return 0, 0

        source = str(path)
        new_hash = self._compute_hash(path)

        # Check if content actually changed
        if not self._has_content_changed(source, new_hash):
            logger.debug(f"File content unchanged: {path}")
            return 0, 0

        # Delete old chunks
        chunks_removed = self._delete_chunks_by_source(source)

        # Re-index with new content
        chunks_added = 0
        try:
            chunks = self._get_chunks_with_fallback(path)
            if chunks:
                texts = [chunk.text for chunk in chunks]
                ids = [f"{source}:{chunk.start}:{chunk.end}" for chunk in chunks]

                metadatas = []
                for chunk in chunks:
                    meta = dict(chunk.metadata)
                    meta["start"] = chunk.start
                    meta["end"] = chunk.end
                    meta["content_hash"] = new_hash
                    metadatas.append(meta)

                embeddings = self._indexer._embedding_provider.embed_batch(texts)

                self._vectorstore.add(
                    collection=self._collection_name,
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )

                chunks_added = len(chunks)
                logger.info(
                    f"Updated {path}: removed {chunks_removed}, added {chunks_added} chunks"
                )
        except Exception as e:
            logger.error(f"Error re-indexing modified file {path}: {e}")

        return chunks_removed, chunks_added

    def handle_deleted(self, path: Path) -> int:
        """Handle a deleted file.

        Args:
            path: Path to the deleted file.

        Returns:
            Number of chunks removed.
        """
        source = str(path)
        chunks_removed = self._delete_chunks_by_source(source)

        if chunks_removed > 0:
            logger.info(f"Removed {chunks_removed} chunks for deleted file: {path}")

        return chunks_removed

    def process_events(self, events: list[FileEvent]) -> IncrementalResult:
        """Process a batch of file events.

        Args:
            events: List of file events to process.

        Returns:
            IncrementalResult with statistics.
        """
        result = IncrementalResult()

        for event in events:
            try:
                if event.event_type == FileEventType.CREATED:
                    chunks = self.handle_created(event.path)
                    if chunks > 0:
                        result.files_added += 1
                        result.chunks_added += chunks

                elif event.event_type == FileEventType.MODIFIED:
                    removed, added = self.handle_modified(event.path)
                    if removed > 0 or added > 0:
                        result.files_updated += 1
                        result.chunks_removed += removed
                        result.chunks_added += added

                elif event.event_type == FileEventType.DELETED:
                    removed = self.handle_deleted(event.path)
                    if removed > 0:
                        result.files_deleted += 1
                        result.chunks_removed += removed

            except Exception as e:
                error_msg = f"Error processing {event.event_type} for {event.path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        logger.info(
            f"Incremental index complete: "
            f"added={result.files_added}, updated={result.files_updated}, "
            f"deleted={result.files_deleted}, chunks_added={result.chunks_added}, "
            f"chunks_removed={result.chunks_removed}"
        )

        return result

    def sync_directory(
        self,
        path: Path | str,
        on_progress: Callable[[int, int, str], None] | None = None,
    ) -> IncrementalResult:
        """Synchronize a directory by detecting all changes.

        Scans the directory and compares with indexed content,
        handling new, modified, and deleted files.

        Args:
            path: Directory to synchronize.
            on_progress: Optional progress callback.

        Returns:
            IncrementalResult with statistics.
        """
        result = IncrementalResult()
        root = Path(path).resolve()

        # Get all indexed sources from vectorstore
        try:
            all_items = self._vectorstore.get(collection=self._collection_name)
            indexed_sources: set[str] = set()
            source_to_hash: dict[str, str] = {}

            for item in all_items:
                source = item.metadata.get("source", "")
                if source:
                    indexed_sources.add(source)
                    if "content_hash" in item.metadata:
                        source_to_hash[source] = item.metadata["content_hash"]
        except Exception as e:
            logger.error(f"Error getting indexed sources: {e}")
            indexed_sources = set()
            source_to_hash = {}

        # Scan current files
        scanned_files = self._scanner.scan(root, compute_hash=True)
        scanned_sources = {str(f.path) for f in scanned_files}

        # Find deleted files (in index but not on disk)
        deleted_sources = indexed_sources - scanned_sources
        for source in deleted_sources:
            removed = self._delete_chunks_by_source(source)
            if removed > 0:
                result.files_deleted += 1
                result.chunks_removed += removed

        # Process current files
        total = len(scanned_files)
        for i, file_info in enumerate(scanned_files):
            if on_progress:
                on_progress(i + 1, total, f"Syncing {file_info.path.name}")

            source = str(file_info.path)
            current_hash = file_info.content_hash or self._compute_hash(file_info.path)

            if source not in indexed_sources:
                # New file
                chunks = self.handle_created(file_info.path)
                if chunks > 0:
                    result.files_added += 1
                    result.chunks_added += chunks
            elif source_to_hash.get(source) != current_hash:
                # Modified file
                removed, added = self.handle_modified(file_info.path)
                if removed > 0 or added > 0:
                    result.files_updated += 1
                    result.chunks_removed += removed
                    result.chunks_added += added

        logger.info(
            f"Directory sync complete for {root}: "
            f"added={result.files_added}, updated={result.files_updated}, "
            f"deleted={result.files_deleted}"
        )

        return result
