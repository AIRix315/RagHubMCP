"""Indexer module.

This module provides file indexing capabilities:
- FileScanner: Scans directories for files
- Indexer: Orchestrates scanning, chunking, embedding, and storage
"""

from .indexer import Indexer, IndexResult, ProgressCallback
from .scanner import FileInfo, FileScanner

__all__ = [
    "Indexer",
    "IndexResult",
    "ProgressCallback",
    "FileInfo",
    "FileScanner",
]
