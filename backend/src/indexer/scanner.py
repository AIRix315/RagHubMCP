"""File scanner for indexing code files.

Scans directories and returns file information based on configuration.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.config import IndexerConfig

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a scanned file.

    Attributes:
        path: Absolute path to the file.
        size: File size in bytes.
        modified_time: Last modification timestamp (Unix timestamp).
        content_hash: MD5 hash of file content (optional).
    """

    path: Path
    size: int
    modified_time: float
    content_hash: str | None = None


class FileScanner:
    """Scans directories for files to index.

    Supports:
    - Recursive directory scanning
    - File type filtering by extension
    - Directory exclusion patterns
    - Maximum file size limits
    - Content hashing (optional)
    """

    def __init__(self, config: IndexerConfig | None = None):
        """Initialize the scanner.

        Args:
            config: Indexer configuration. If None, uses global config.
        """
        if config is None:
            from src.utils.config import get_config

            config = get_config().indexer

        self._config: IndexerConfig = config
        self._skipped_files: list[tuple[Path, str]] = []  # (path, reason)

    @property
    def skipped_files(self) -> list[tuple[Path, str]]:
        """List of files skipped during the last scan with reasons."""
        return self._skipped_files.copy()

    def scan(self, root_path: Path | str, compute_hash: bool = False) -> list[FileInfo]:
        """Scan a directory or single file.

        Args:
            root_path: Root directory or file to scan.
            compute_hash: Whether to compute content hash for each file.

        Returns:
            List of FileInfo objects for valid files.
        """
        self._skipped_files = []
        root = Path(root_path).resolve()

        if not root.exists():
            logger.warning(f"Path does not exist: {root}")
            return []

        if root.is_file():
            return self._scan_file(root, compute_hash)

        if not root.is_dir():
            logger.warning(f"Path is neither file nor directory: {root}")
            return []

        return self._scan_directory(root, compute_hash)

    def _scan_file(self, file_path: Path, compute_hash: bool) -> list[FileInfo]:
        """Scan a single file.

        Args:
            file_path: Path to the file.
            compute_hash: Whether to compute content hash.

        Returns:
            List containing single FileInfo if valid, empty list otherwise.
        """
        if not self._is_valid_file(file_path):
            return []

        return [self._create_file_info(file_path, compute_hash)]

    def _scan_directory(self, root: Path, compute_hash: bool) -> list[FileInfo]:
        """Scan a directory recursively.

        Args:
            root: Root directory to scan.
            compute_hash: Whether to compute content hash.

        Returns:
            List of FileInfo objects for valid files.
        """
        results: list[FileInfo] = []

        # Use rglob for recursive scanning
        for path in root.rglob("*"):
            if not path.is_file():
                continue

            if self._should_exclude(path):
                continue

            if not self._is_valid_file(path):
                continue

            results.append(self._create_file_info(path, compute_hash))

        return results

    def _should_exclude(self, path: Path) -> bool:
        """Check if path should be excluded.

        Args:
            path: File path to check.

        Returns:
            True if path should be excluded.
        """
        # Check if any parent directory is in exclude list
        for part in path.parts:
            if part in self._config.exclude_dirs:
                return True
        return False

    def _is_valid_file(self, path: Path) -> bool:
        """Check if file is valid for indexing.

        Args:
            path: File path to check.

        Returns:
            True if file is valid for indexing.
        """
        # Check file extension
        suffix = path.suffix.lower()
        if suffix not in self._config.file_types:
            self._skipped_files.append((path, f"File type not allowed: {suffix}"))
            return False

        # Check file size
        try:
            size = path.stat().st_size
        except OSError as e:
            logger.warning(f"Cannot stat file {path}: {e}")
            self._skipped_files.append((path, f"Cannot read file stats: {e}"))
            return False

        if size > self._config.max_file_size:
            self._skipped_files.append(
                (path, f"File too large: {size} > {self._config.max_file_size}")
            )
            return False

        return True

    def _create_file_info(self, path: Path, compute_hash: bool) -> FileInfo:
        """Create FileInfo for a file.

        Args:
            path: File path.
            compute_hash: Whether to compute content hash.

        Returns:
            FileInfo object.
        """
        stat = path.stat()

        content_hash = None
        if compute_hash:
            content_hash = self._compute_hash(path)

        return FileInfo(
            path=path, size=stat.st_size, modified_time=stat.st_mtime, content_hash=content_hash
        )

    def _compute_hash(self, path: Path) -> str:
        """Compute MD5 hash of file content.

        Args:
            path: File path.

        Returns:
            Hexadecimal hash string.
        """
        hasher = hashlib.md5()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            logger.warning(f"Cannot compute hash for {path}: {e}")
            return ""
