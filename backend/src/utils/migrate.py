"""VectorStore migration utilities.

This module provides tools for migrating data between different vector store
providers, primarily supporting ChromaDB to Qdrant migration.

Features:
- Batch migration with configurable batch size
- Progress callback support for UI integration
- Data integrity verification
- Error recovery and reporting
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from providers.vectorstore import BaseVectorStoreProvider

logger = logging.getLogger(__name__)

# Default batch size for migration
DEFAULT_BATCH_SIZE = 100


class ProgressCallback(Protocol):
    """Protocol for progress callback during migration."""

    def __call__(self, current: int, total: int, message: str) -> None:
        """Report migration progress.

        Args:
            current: Current progress count
            total: Total count to complete
            message: Status message
        """
        ...


@dataclass
class MigrationResult:
    """Result of a migration operation.

    Attributes:
        success: Whether the migration completed successfully
        collections_migrated: Number of collections migrated
        documents_migrated: Total number of documents migrated
        collections: Details per collection
        errors: List of error messages
        warnings: List of warning messages
        duration_seconds: Total migration duration
    """

    success: bool = True
    collections_migrated: int = 0
    documents_migrated: int = 0
    collections: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "collections_migrated": self.collections_migrated,
            "documents_migrated": self.documents_migrated,
            "collections": self.collections,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_seconds": round(self.duration_seconds, 2),
        }


@dataclass
class CollectionMigrationResult:
    """Result of migrating a single collection.

    Attributes:
        name: Collection name
        documents_migrated: Number of documents migrated
        success: Whether the migration succeeded
        error: Error message if failed
    """

    name: str
    documents_migrated: int = 0
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "documents_migrated": self.documents_migrated,
            "success": self.success,
            "error": self.error,
        }


class VectorStoreMigrator:
    """Migrator for transferring data between vector stores.

    Supports migrating collections and documents from one vector store
    provider to another, with progress tracking and integrity verification.

    Example:
        >>> from providers.vectorstore import ChromaProvider, QdrantProvider
        >>> from utils.migrate import VectorStoreMigrator
        >>>
        >>> source = ChromaProvider(persist_dir="./data/chroma")
        >>> target = QdrantProvider(mode="local", path="./data/qdrant")
        >>>
        >>> migrator = VectorStoreMigrator(source, target)
        >>> result = migrator.migrate(progress_callback=print_progress)
    """

    def __init__(
        self,
        source: BaseVectorStoreProvider,
        target: BaseVectorStoreProvider,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """Initialize the migrator.

        Args:
            source: Source vector store provider
            target: Target vector store provider
            batch_size: Number of documents to process per batch
        """
        self.source = source
        self.target = target
        self.batch_size = batch_size

    def migrate(
        self,
        collections: list[str] | None = None,
        progress_callback: ProgressCallback | None = None,
        verify: bool = True,
    ) -> MigrationResult:
        """Migrate data from source to target vector store.

        Args:
            collections: List of collection names to migrate.
                        If None, migrates all collections from source.
            progress_callback: Optional callback for progress updates
            verify: Whether to verify data integrity after migration

        Returns:
            MigrationResult with migration details
        """
        start_time = time.perf_counter()
        result = MigrationResult()

        # Get collections to migrate
        if collections is None:
            try:
                collections = self.source.list_collections()
            except Exception as e:
                result.errors.append(f"Failed to list source collections: {e}")
                result.success = False
                result.duration_seconds = time.perf_counter() - start_time
                return result

        if not collections:
            result.warnings.append("No collections found to migrate")
            result.duration_seconds = time.perf_counter() - start_time
            return result

        total_collections = len(collections)

        # Migrate each collection
        for idx, collection_name in enumerate(collections):
            if progress_callback:
                progress_callback(
                    idx, total_collections, f"Migrating collection: {collection_name}"
                )

            collection_result = self._migrate_collection(collection_name, progress_callback)

            result.collections.append(collection_result.to_dict())

            if collection_result.success:
                result.collections_migrated += 1
                result.documents_migrated += collection_result.documents_migrated
            else:
                result.errors.append(
                    f"Collection '{collection_name}' failed: {collection_result.error}"
                )

        # Verify integrity if requested
        if verify and result.collections_migrated > 0:
            if progress_callback:
                progress_callback(
                    total_collections, total_collections, "Verifying data integrity..."
                )

            verify_result = self._verify_integrity(collections)
            if not verify_result["success"]:
                result.warnings.extend(verify_result.get("warnings", []))
                result.errors.extend(verify_result.get("errors", []))

        result.success = len(result.errors) == 0
        result.duration_seconds = time.perf_counter() - start_time

        logger.info(
            f"Migration completed: {result.collections_migrated} collections, "
            f"{result.documents_migrated} documents in {result.duration_seconds:.2f}s"
        )

        return result

    def _migrate_collection(
        self,
        collection_name: str,
        progress_callback: ProgressCallback | None = None,
    ) -> CollectionMigrationResult:
        """Migrate a single collection.

        Args:
            collection_name: Name of the collection to migrate
            progress_callback: Optional progress callback

        Returns:
            CollectionMigrationResult with details
        """
        result = CollectionMigrationResult(name=collection_name)

        try:
            # Check source collection exists
            if not self.source.collection_exists(collection_name):
                result.success = False
                result.error = f"Source collection '{collection_name}' does not exist"
                return result

            # Get source count
            source_count = self.source.count(collection_name)

            if source_count == 0:
                result.success = True
                result.documents_migrated = 0
                logger.info(f"Collection '{collection_name}' is empty, skipping")
                return result

            # Create target collection if not exists
            if not self.target.collection_exists(collection_name):
                self.target.create_collection(collection_name)

            # Migrate in batches
            offset = 0
            migrated_count = 0

            while offset < source_count:
                batch_data = self._read_batch(collection_name, offset, self.batch_size)

                if not batch_data["ids"]:
                    break

                # Write to target
                self.target.add(
                    collection=collection_name,
                    documents=batch_data["documents"],
                    ids=batch_data["ids"],
                    metadatas=batch_data["metadatas"],
                    embeddings=batch_data["embeddings"],
                )

                migrated_count += len(batch_data["ids"])
                offset += self.batch_size

                if progress_callback:
                    progress_callback(
                        min(offset, source_count),
                        source_count,
                        f"Migrating '{collection_name}': {min(offset, source_count)}/{source_count}",
                    )

            result.documents_migrated = migrated_count

        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Failed to migrate collection '{collection_name}': {e}")

        return result

    def _read_batch(
        self,
        collection_name: str,
        offset: int,
        limit: int,
    ) -> dict[str, Any]:
        """Read a batch of documents from source.

        Args:
            collection_name: Collection name
            offset: Starting offset
            limit: Maximum documents to read

        Returns:
            Dictionary with ids, documents, metadatas, and embeddings
        """
        # Use ChromaService directly to get embeddings
        if hasattr(self.source, "NAME") and self.source.NAME == "chroma":
            return self._read_chroma_batch(collection_name, offset, limit)
        else:
            # Fallback for other providers (without embeddings)
            results = self.source.get(
                collection=collection_name,
                limit=limit,
                offset=offset,
            )

            return {
                "ids": [r.id for r in results],
                "documents": [r.document for r in results],
                "metadatas": [r.metadata for r in results],
                "embeddings": None,  # Will need to be generated by target
            }

    def _read_chroma_batch(
        self,
        collection_name: str,
        offset: int,
        limit: int,
    ) -> dict[str, Any]:
        """Read a batch from ChromaDB including embeddings.

        Args:
            collection_name: Collection name
            offset: Starting offset
            limit: Maximum documents to read

        Returns:
            Dictionary with ids, documents, metadatas, and embeddings
        """
        # Get the underlying Chroma collection
        # Access private method via getattr to avoid type errors
        get_service = getattr(self.source, "_get_service", None)
        if get_service is None:
            raise RuntimeError("Source provider does not support _get_service")
        service = get_service()
        get_collection = getattr(service, "get_collection", None)
        if get_collection is None:
            raise RuntimeError("Service does not support get_collection")
        collection = get_collection(collection_name)

        # Fetch all data including embeddings
        result = collection.get(
            limit=limit,
            offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )

        return {
            "ids": result.get("ids", []),
            "documents": result.get("documents", []),
            "metadatas": result.get("metadatas", []),
            "embeddings": result.get("embeddings", []),
        }

    def _verify_integrity(self, collections: list[str]) -> dict[str, Any]:
        """Verify migration integrity.

        Args:
            collections: List of migrated collections to verify

        Returns:
            Dictionary with verification results
        """
        errors: list[str] = []
        warnings: list[str] = []

        for collection_name in collections:
            try:
                source_count = self.source.count(collection_name)
                target_count = self.target.count(collection_name)

                if source_count != target_count:
                    errors.append(
                        f"Count mismatch for '{collection_name}': "
                        f"source={source_count}, target={target_count}"
                    )
                else:
                    logger.debug(f"Verified '{collection_name}': {target_count} documents")

            except Exception as e:
                warnings.append(f"Could not verify '{collection_name}': {e}")

        return {
            "success": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


def migrate_chroma_to_qdrant(
    chroma_persist_dir: str = "./data/chroma",
    qdrant_mode: str = "local",
    qdrant_path: str = "./data/qdrant",
    collections: list[str] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    progress_callback: ProgressCallback | None = None,
    verify: bool = True,
) -> MigrationResult:
    """Convenience function for ChromaDB to Qdrant migration.

    Args:
        chroma_persist_dir: ChromaDB persistence directory
        qdrant_mode: Qdrant mode ("memory", "local", "remote", "cloud")
        qdrant_path: Qdrant storage path (for local mode)
        collections: Specific collections to migrate (None = all)
        batch_size: Batch size for migration
        progress_callback: Optional progress callback
        verify: Whether to verify data integrity

    Returns:
        MigrationResult with migration details

    Example:
        >>> result = migrate_chroma_to_qdrant(
        ...     chroma_persist_dir="./data/chroma",
        ...     qdrant_path="./data/qdrant",
        ... )
        >>> print(f"Migrated {result.documents_migrated} documents")
    """
    from providers.vectorstore import ChromaProvider, QdrantProvider

    source = ChromaProvider(persist_dir=chroma_persist_dir)
    target = QdrantProvider(mode=qdrant_mode, path=qdrant_path)

    migrator = VectorStoreMigrator(
        source=source,
        target=target,
        batch_size=batch_size,
    )

    return migrator.migrate(
        collections=collections,
        progress_callback=progress_callback,
        verify=verify,
    )
