"""Indexer - Orchestrates file indexing workflow.

This module provides the Indexer class that coordinates:
1. File scanning (FileScanner)
2. Text chunking (ChunkerRegistry)
3. Embedding generation (EmbeddingProvider)
4. Vector storage (BaseVectorStoreProvider)

Reference:
- RULE-3: Use interfaces, not concrete implementations
- Use BaseVectorStoreProvider instead of ChromaDB Collection directly
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from src.chunkers import Chunk, ChunkerRegistry
from src.indexer.scanner import FileScanner
from src.providers.vectorstore.base import BaseVectorStoreProvider

if TYPE_CHECKING:
    from src.providers.embedding.base import BaseEmbeddingProvider
    from src.utils.config import IndexerConfig

logger = logging.getLogger(__name__)


# File extension to language mapping
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".md": "markdown",
    ".vue": "vue",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".scala": "scala",
    ".lua": "lua",
    ".sh": "bash",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
}


@dataclass
class IndexResult:
    """Result of an indexing operation.

    Attributes:
        files_indexed: Number of files successfully indexed
        files_skipped: Number of files skipped
        chunks_created: Total number of chunks created
        errors: List of error messages
    """

    files_indexed: int = 0
    files_skipped: int = 0
    chunks_created: int = 0
    errors: list[str] = field(default_factory=list)


# Progress callback type: (current, total, message)
ProgressCallback = Callable[[int, int, str], None]


class Indexer:
    """Orchestrates the file indexing workflow.

    This class coordinates scanning, chunking, embedding, and storage:

    Workflow:
        1. FileScanner scans files from disk
        2. ChunkerRegistry selects appropriate chunker per file
        3. EmbeddingProvider generates vectors
        4. VectorStoreProvider stores vectors (via ChromaDB collection)

    Example:
        >>> from src.providers.factory import factory
        >>> from src.utils.config import IndexerConfig
        >>>
        >>> # Get vectorstore provider (RULE-3 compliant)
        >>> vectorstore = factory.get_vectorstore_provider()
        >>> collection = vectorstore.create_collection("code_index")
        >>>
        >>> config = IndexerConfig(chunk_size=500, chunk_overlap=50)
        >>> embedding = factory.get_embedding_provider()
        >>>
        >>> indexer = Indexer(config, embedding, collection)
        >>> result = indexer.index_directory("./src")
    """

    def __init__(
        self,
        config: IndexerConfig,
        embedding_provider: BaseEmbeddingProvider,
        vectorstore: BaseVectorStoreProvider,
        collection_name: str = "default",
    ) -> None:
        """Initialize the Indexer.

        Args:
            config: Indexer configuration (chunk_size, overlap, etc.)
            embedding_provider: Provider for generating embeddings
            vectorstore: VectorStore provider for storing vectors (RULE-3 compliant)
            collection_name: Collection name to use (default: "default")
        """
        self._config = config
        self._embedding_provider = embedding_provider
        self._vectorstore = vectorstore
        self._collection_name = collection_name
        self._scanner = FileScanner(config)
        self._chunker_registry = ChunkerRegistry()

    def _get_language(self, file_path: Path) -> str:
        """Get language identifier from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language identifier (e.g., "python", "typescript")
        """
        ext = file_path.suffix.lower()
        return EXTENSION_TO_LANGUAGE.get(ext, "text")

    def _chunk_file(self, file_path: Path) -> list[Chunk]:
        """Read and chunk a file.

        Args:
            file_path: Path to the file to chunk

        Returns:
            List of Chunk objects
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            try:
                content = file_path.read_text(encoding="latin-1")
            except Exception as e:
                logger.warning(f"Cannot read file {file_path}: {e}")
                return []
        except Exception as e:
            logger.warning(f"Cannot read file {file_path}: {e}")
            return []

        if not content.strip():
            return []

        # Get appropriate chunker for the language
        language = self._get_language(file_path)
        chunker_cls = self._chunker_registry.get_for_language(language)
        chunker = chunker_cls(
            chunk_size=self._config.chunk_size,
            overlap=self._config.chunk_overlap,
        )

        # Create metadata
        metadata = {
            "source": str(file_path),
            "language": language,
            "filename": file_path.name,
        }

        return chunker.chunk(content, metadata)

    def index_file(
        self,
        path: Path | str,
        on_progress: ProgressCallback | None = None,
    ) -> int:
        """Index a single file.

        Args:
            path: Path to the file to index
            on_progress: Optional progress callback

        Returns:
            Number of chunks created
        """
        file_path = Path(path).resolve()

        if on_progress:
            on_progress(0, 1, f"Reading {file_path.name}")

        # Chunk the file
        chunks = self._chunk_file(file_path)

        if not chunks:
            logger.debug(f"No chunks created for {file_path}")
            return 0

        # Index the chunks
        self._index_chunks(chunks, file_path)

        if on_progress:
            on_progress(1, 1, f"Indexed {file_path.name}")

        return len(chunks)

    def _index_chunks(self, chunks: list[Chunk], source_path: Path) -> None:
        """Index chunks into ChromaDB.

        Args:
            chunks: List of chunks to index
            source_path: Source file path (for ID generation)
        """
        if not chunks:
            return

        # Prepare data
        texts = [chunk.text for chunk in chunks]
        ids = [f"{source_path}:{chunk.start}:{chunk.end}" for chunk in chunks]

        # Merge metadata from chunks
        metadatas = []
        for chunk in chunks:
            meta = dict(chunk.metadata)
            meta["start"] = chunk.start
            meta["end"] = chunk.end
            metadatas.append(meta)

        # Generate embeddings
        embeddings = self._embedding_provider.embed_batch(texts)

        # Add to collection
        self._vectorstore.add(
            collection=self._collection_name,
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        logger.debug(f"Indexed {len(chunks)} chunks from {source_path}")

    def index_chunks(
        self,
        chunks: list[Chunk],
        batch_size: int = 32,
    ) -> None:
        """Index chunks into the collection.

        This method handles large batches by processing in sub-batches
        to avoid memory issues.

        Args:
            chunks: List of chunks to index
            batch_size: Maximum chunks per batch
        """
        if not chunks:
            return

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            texts = [chunk.text for chunk in batch]

            # Generate unique IDs
            ids = [f"chunk_{i + j}:{chunk.start}:{chunk.end}" for j, chunk in enumerate(batch)]

            # Prepare metadata
            metadatas = []
            for chunk in batch:
                meta = dict(chunk.metadata)
                meta["start"] = chunk.start
                meta["end"] = chunk.end
                metadatas.append(meta)

            # Generate embeddings for this batch
            embeddings = self._embedding_provider.embed_batch(texts, batch_size=batch_size)

            # Add to collection
            self._vectorstore.add(
                collection=self._collection_name,
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

        logger.info(
            f"Indexed {len(chunks)} chunks in {(len(chunks) + batch_size - 1) // batch_size} batches"
        )

    def index_directory(
        self,
        path: Path | str,
        recursive: bool = True,
        on_progress: ProgressCallback | None = None,
    ) -> IndexResult:
        """Index all files in a directory.

        Args:
            path: Root directory path
            recursive: Whether to scan recursively
            on_progress: Optional progress callback

        Returns:
            IndexResult with statistics
        """
        root = Path(path).resolve()
        result = IndexResult()

        # Scan files
        if on_progress:
            on_progress(0, 0, "Scanning directory...")

        files = self._scanner.scan(root)

        if not files:
            logger.info(f"No files found in {root}")
            return result

        total = len(files)
        logger.info(f"Found {total} files to index in {root}")

        # Index each file
        for current, file_info in enumerate(files, 1):
            try:
                if on_progress:
                    on_progress(current, total, f"Indexing {file_info.path.name}")

                chunks = self._chunk_file(file_info.path)

                if chunks:
                    self._index_chunks(chunks, file_info.path)
                    result.files_indexed += 1
                    result.chunks_created += len(chunks)
                else:
                    result.files_skipped += 1

            except Exception as e:
                error_msg = f"Error indexing {file_info.path}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                result.files_skipped += 1

        if on_progress:
            on_progress(
                total,
                total,
                f"Completed: {result.files_indexed} files, {result.chunks_created} chunks",
            )

        logger.info(
            f"Indexing complete: {result.files_indexed} files, "
            f"{result.chunks_created} chunks, {result.files_skipped} skipped"
        )

        return result

    def search(
        self,
        query: str,
        n_results: int = 5,
    ) -> list[dict]:
        """Search the indexed content.

        Args:
            query: Search query text
            n_results: Maximum number of results

        Returns:
            List of search results with documents, metadata, and distances
        """
        # Generate query embedding
        query_embedding = self._embedding_provider.embed_query(query)

        # Query the vectorstore
        query_result = self._vectorstore.query(
            collection=self._collection_name,
            query_embedding=query_embedding,
            n_results=n_results,
        )

        # Format results
        formatted = []
        for result in query_result.results:
            formatted.append(
                {
                    "document": result.document,
                    "metadata": result.metadata,
                    "distance": result.score,
                }
            )

        return formatted

    def clear(self) -> None:
        """Clear all indexed content from the collection."""
        # Get all items from vectorstore
        all_items = self._vectorstore.get(collection=self._collection_name)

        if all_items:
            ids = [item.id for item in all_items]
            deleted_count = self._vectorstore.delete(collection=self._collection_name, ids=ids)
            logger.info(f"Cleared {deleted_count} items from collection")
