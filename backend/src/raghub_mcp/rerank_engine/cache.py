"""Query cache for performance optimization.

This module provides an LRU cache for query results to avoid
repeated computation for identical queries.

Reference: Docs/20-RerankEngine-Architecture.md Section 4.4
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""

    value: Any
    created_at: float
    ttl: float
    hits: int = 0


class QueryCache:
    """LRU cache for query results.

    Thread-safe implementation with TTL support.

    Attributes:
        max_size: Maximum number of entries.
        default_ttl: Default time-to-live in seconds.

    Example:
        >>> cache = QueryCache(max_size=100, default_ttl=300)
        >>> cache.set("query_hash", {"results": [...]})
        >>> results = cache.get("query_hash")
    """

    def __init__(self, max_size: int = 100, default_ttl: float = 300.0) -> None:
        """Initialize query cache.

        Args:
            max_size: Maximum number of cached entries.
            default_ttl: Default TTL in seconds (5 minutes).
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._max_size = max_size
        self._default_ttl = default_ttl

        # Statistics
        self._hits = 0
        self._misses = 0

    @staticmethod
    def hash_query(query: str, documents: list[str], **kwargs) -> str:
        """Generate cache key from query and documents.

        Args:
            query: Query string.
            documents: Document list.
            **kwargs: Additional parameters.

        Returns:
            Cache key hash.
        """
        content = f"{query}||{'||'.join(documents[:10])}||{kwargs.get('top_k', 10)}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get cached value.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if not found/expired.
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry.created_at > entry.ttl:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._hits += 1

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set cached value.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time-to-live in seconds (uses default if None).
        """
        with self._lock:
            # Remove oldest if at capacity
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._cache.popitem(last=False)

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl or self._default_ttl,
            )

    def delete(self, key: str) -> bool:
        """Delete cached value.

        Args:
            key: Cache key.

        Returns:
            True if deleted, False if not found.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached values."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "total_entries": len(self._cache),
            }

    def cleanup_expired(self) -> int:
        """Remove expired entries.

        Returns:
            Number of entries removed.
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if now - entry.created_at > entry.ttl
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

            return len(expired_keys)


# Global cache instance
_cache: QueryCache | None = None


def get_cache() -> QueryCache:
    """Get global cache instance.

    Returns:
        Global QueryCache instance.
    """
    global _cache
    if _cache is None:
        _cache = QueryCache()
    return _cache


def reset_cache() -> None:
    """Reset global cache instance."""
    global _cache
    if _cache:
        _cache.clear()
    _cache = None