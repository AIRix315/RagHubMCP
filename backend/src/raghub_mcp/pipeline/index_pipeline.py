"""Index Pipeline for unified indexing operations.

This module provides IndexPipeline that encapsulates:
- File scanning
- Chunking
- Embedding generation
- Vector store insertion
- BM25 index update

Reference: RULE-1 - Pipeline is the only execution entry.
"""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from raghub_mcp.utils.config import get_config

if TYPE_CHECKING:
    from raghub_mcp.chunkers.base import ChunkerPlugin
    from raghub_mcp.indexer.scanner import FileInfo, FileScanner

logger = logging.getLogger(__name__)


@dataclass
class IndexOptions:
    """Options for indexing operation."""

    collection_name: str = "default"
    chunk_size: int = 500
    chunk_overlap: int = 50
    recursive: bool = True
    embedding_provider: str | None = None
    file_types: list[str] | None = None
    exclude_dirs: list[str] | None = None


@dataclass
class IndexResult:
    """Result of indexing operation."""

    task_id: str
    total_files: int = 0
    processed_files: int = 0
    total_chunks: int = 0
    status: str = "pending"  # "pending", "running", "completed", "failed"
    message: str | None = None
    errors: list[str] = field(default_factory=list)


class IndexPipeline(ABC):
    """Abstract base class for indexing pipelines.

    This abstract class defines the interface for all indexing pipelines.
    Concrete implementations must provide the index method.

    Reference: RULE-1 - Pipeline is the only execution entry.
    """

    @abstractmethod
    async def index(
        self,
        path: str | Path,
        options: IndexOptions | None = None,
    ) -> IndexResult:
        """Execute indexing operation.

        Args:
            path: Directory or file path to index
            options: Indexing options

        Returns:
            IndexResult with task status and statistics
        """
        ...


class DefaultIndexPipeline(IndexPipeline):
    """Default implementation of IndexPipeline.

    This implementation:
    1. Scans files using FileScanner
    2. Chunks content using appropriate chunkers
    3. Generates embeddings via Provider
    4. Inserts into vector store
    5. Updates BM25 index

    Reference: RULE-3 - No direct dependency on concrete implementations.
    """

    def __init__(self) -> None:
        """Initialize the index pipeline."""
        self._config = get_config()
        # Lazy imports to avoid circular dependencies
        self._scanner: FileScanner | None = None
        self._chunker_cache: dict[str, Any] = {}

    def _get_scanner(self) -> FileScanner:
        """Get or create FileScanner instance."""
        if self._scanner is None:
            from raghub_mcp.indexer.scanner import FileScanner

            self._scanner = FileScanner()
        return self._scanner

    def _get_chunker(self, file_path: Path, options: IndexOptions) -> ChunkerPlugin:
        """Get appropriate chunker for file type."""
        from raghub_mcp.chunkers import factory as chunker_factory

        # Determine file type from extension
        file_type = file_path.suffix.lower()

        # Cache key includes file type and chunk options
        cache_key = f"{file_type}:{options.chunk_size}:{options.chunk_overlap}"

        if cache_key not in self._chunker_cache:
            # Get chunker via factory (RULE-3 compliance)
            chunker = chunker_factory.get_chunker(
                name=None,  # Let factory decide based on file_type
                file_type=file_type,
                chunk_size=options.chunk_size,
                overlap=options.chunk_overlap,
            )
            self._chunker_cache[cache_key] = chunker

        return self._chunker_cache[cache_key]

    async def index(
        self,
        path: str | Path,
        options: IndexOptions | None = None,
    ) -> IndexResult:
        """Execute indexing operation.

        Args:
            path: Directory or file path to index
            options: Indexing options

        Returns:
            IndexResult with task status and statistics
        """
        options = options or IndexOptions()
        task_id = str(uuid.uuid4())

        result = IndexResult(
            task_id=task_id,
            status="running",
        )

        try:
            # Resolve path
            target_path = Path(path).resolve()
            if not target_path.exists():
                result.status = "failed"
                result.message = f"Path does not exist: {path}"
                return result

            # Get providers through factory (RULE-3 compliance)
            from raghub_mcp.providers.factory import factory as provider_factory

            vectorstore = provider_factory.get_vectorstore_provider()
            embedding_provider = provider_factory.get_embedding_provider(
                options.embedding_provider
            )

            # Ensure collection exists
            if not vectorstore.collection_exists(options.collection_name):
                vectorstore.create_collection(options.collection_name)
                logger.info(f"Created collection: {options.collection_name}")

            # Scan files
            scanner = self._get_scanner()
            files = scanner.scan(target_path)
            result.total_files = len(files)

            if not files:
                result.status = "completed"
                result.message = "No files found to index"
                return result

            logger.info(f"Found {len(files)} files to index in {target_path}")

            # Process each file
            errors: list[str] = []
            for file_info in files:
                try:
                    await self._process_file(
                        file_info=file_info,
                        options=options,
                        vectorstore=vectorstore,
                        embedding_provider=embedding_provider,
                        result=result,
                    )
                except Exception as e:
                    error_msg = f"Failed to process {file_info.path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Update BM25 index if available
            try:
                await self._update_bm25_index(target_path, files, options)
            except Exception as e:
                logger.warning(f"BM25 index update failed (non-critical): {e}")

            # Finalize result
            result.processed_files = result.total_files - len(errors)
            result.status = "completed" if not errors else "partial"
            result.errors = errors
            result.message = (
                f"Indexed {result.processed_files}/{result.total_files} files, "
                f"{result.total_chunks} chunks created"
            )

            logger.info(f"Indexing completed: {result.message}")

        except Exception as e:
            result.status = "failed"
            result.message = f"Indexing failed: {e}"
            result.errors.append(str(e))
            logger.error(f"Indexing failed: {e}")

        return result

    async def _process_file(
        self,
        file_info: FileInfo,
        options: IndexOptions,
        vectorstore: Any,
        embedding_provider: Any,
        result: IndexResult,
    ) -> None:
        """Process a single file.

        Args:
            file_info: File information from scanner
            options: Indexing options
            vectorstore: Vector store provider
            embedding_provider: Embedding provider
            result: Result object to update
        """
        # Read file content
        try:
            content = file_info.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with different encoding
            content = file_info.path.read_text(encoding="latin-1")

        if not content.strip():
            logger.debug(f"Skipping empty file: {file_info.path}")
            return

        # Get appropriate chunker
        chunker = self._get_chunker(file_info.path, options)

        # Create metadata
        metadata = {
            "source": str(file_info.path),
            "file_name": file_info.path.name,
            "file_type": file_info.path.suffix,
            "file_size": file_info.size,
            "modified_time": file_info.modified_time,
        }

        # Chunk the content
        chunks = chunker.chunk(content, metadata)

        if not chunks:
            logger.debug(f"No chunks produced for: {file_info.path}")
            return

        # Prepare for indexing
        chunk_texts = [chunk.text for chunk in chunks]
        chunk_ids = [
            f"{file_info.path.name}:{chunk.metadata.get('chunk_index', i)}"
            for i, chunk in enumerate(chunks)
        ]
        chunk_metadatas = [dict(chunk.metadata) for chunk in chunks]

        # Generate embeddings and add to vector store
        try:
            vectorstore.add(
                collection=options.collection_name,
                documents=chunk_texts,
                ids=chunk_ids,
                metadatas=chunk_metadatas,
            )
            result.total_chunks += len(chunks)
            logger.debug(f"Indexed {len(chunks)} chunks from {file_info.path}")
        except Exception as e:
            raise RuntimeError(f"Failed to add to vector store: {e}") from e

    async def _update_bm25_index(
        self,
        root_path: Path,
        files: list[FileInfo],
        options: IndexOptions,
    ) -> None:
        """Update BM25 index for the indexed files.

        Args:
            root_path: Root path that was indexed
            files: List of files that were indexed
            options: Indexing options
        """
        try:
            from raghub_mcp.services.bm25_service import BM25Service

            bm25_service = BM25Service()
            # BM25 index update is optional and may fail gracefully
            await bm25_service.update_index(root_path, files)
            logger.debug(f"BM25 index updated for {len(files)} files")
        except ImportError:
            logger.debug("BM25 service not available, skipping BM25 update")
        except Exception as e:
            # BM25 is optional, log but don't fail
            logger.debug(f"BM25 update skipped: {e}")


# Singleton instance
_index_pipeline: IndexPipeline | None = None


def get_index_pipeline() -> IndexPipeline:
    """Get singleton IndexPipeline instance.

    Returns:
        DefaultIndexPipeline singleton instance
    """
    global _index_pipeline
    if _index_pipeline is None:
        _index_pipeline = DefaultIndexPipeline()
    return _index_pipeline


def reset_index_pipeline() -> None:
    """Reset the singleton IndexPipeline instance.

    Useful for testing or when configuration changes.
    """
    global _index_pipeline
    _index_pipeline = None


async def execute_index(
    path: str | Path,
    options: IndexOptions | None = None,
) -> IndexResult:
    """Convenience function to execute indexing.

    Args:
        path: Directory or file path to index
        options: Indexing options

    Returns:
        IndexResult with task status and statistics

    Example:
        >>> result = await execute_index("./docs", IndexOptions(collection_name="docs"))
        >>> print(f"Indexed {result.processed_files} files")
    """
    pipeline = get_index_pipeline()
    return await pipeline.index(path, options)
