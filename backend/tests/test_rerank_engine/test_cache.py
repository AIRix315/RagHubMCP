"""Tests for rerank_engine cache.

Test cases:
- QueryCache basic operations (get, set, delete)
- TTL expiration
- LRU eviction
- Cache statistics
- Thread safety
"""

from __future__ import annotations

import time

import pytest

from raghub_mcp.rerank_engine.cache import QueryCache, get_cache, reset_cache


class TestQueryCache:
    """Tests for QueryCache."""

    def test_basic_set_get(self):
        """Test basic set and get operations."""
        cache = QueryCache(max_size=10)

        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")

        assert result == {"data": "value1"}

    def test_get_missing_key(self):
        """Test getting a missing key returns None."""
        cache = QueryCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_delete(self):
        """Test deleting a cache entry."""
        cache = QueryCache()

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        deleted = cache.delete("key1")

        assert deleted is True
        assert cache.get("key1") is None

    def test_delete_nonexistent(self):
        """Test deleting a nonexistent key."""
        cache = QueryCache()

        deleted = cache.delete("nonexistent")

        assert deleted is False

    def test_clear(self):
        """Test clearing the cache."""
        cache = QueryCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        cache = QueryCache(default_ttl=0.1)  # 100ms TTL

        cache.set("key1", "value1")

        # Should be available immediately
        assert cache.get("key1") == "value1"

        # Wait for expiration
        time.sleep(0.15)

        # Should be expired
        assert cache.get("key1") is None

    def test_custom_ttl(self):
        """Test custom TTL for individual entries."""
        cache = QueryCache(default_ttl=10.0)  # 10 seconds default

        cache.set("key1", "value1", ttl=0.1)  # 100ms custom TTL

        time.sleep(0.15)

        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """Test LRU eviction when max_size is reached."""
        cache = QueryCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        cache.set("key4", "value4")  # Should evict key1 (oldest)

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_lru_access_updates_order(self):
        """Test that accessing an entry updates its position."""
        cache = QueryCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1 to make it most recently used
        cache.get("key1")

        # Add new entry - should evict key2 (now oldest)
        cache.set("key4", "value4")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted

    def test_cache_statistics(self):
        """Test cache statistics."""
        cache = QueryCache()

        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("nonexistent")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == pytest.approx(2 / 3)

    def test_hash_query(self):
        """Test query hashing."""
        hash1 = QueryCache.hash_query("test query", ["doc1", "doc2"])
        hash2 = QueryCache.hash_query("test query", ["doc1", "doc2"])
        hash3 = QueryCache.hash_query("different query", ["doc1", "doc2"])

        assert hash1 == hash2  # Same input = same hash
        assert hash1 != hash3  # Different input = different hash

    def test_hash_query_with_kwargs(self):
        """Test query hashing with additional parameters."""
        hash1 = QueryCache.hash_query("query", ["doc1"], top_k=10)
        hash2 = QueryCache.hash_query("query", ["doc1"], top_k=20)

        assert hash1 != hash2  # Different kwargs = different hash

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = QueryCache(default_ttl=0.1)

        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=10.0)  # Long TTL

        time.sleep(0.15)

        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_thread_safety(self):
        """Test concurrent access is safe."""
        import threading

        cache = QueryCache()
        errors = []

        def writer():
            try:
                for i in range(100):
                    cache.set(f"key{i}", f"value{i}")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(100):
                    cache.get(f"key{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=writer),
            threading.Thread(target=writer),
            threading.Thread(target=reader),
            threading.Thread(target=reader),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestGlobalCache:
    """Tests for global cache instance."""

    def setup_method(self):
        """Reset global cache before each test."""
        reset_cache()

    def test_get_cache_returns_singleton(self):
        """Test get_cache returns the same instance."""
        cache1 = get_cache()
        cache2 = get_cache()

        assert cache1 is cache2

    def test_reset_cache(self):
        """Test reset_cache clears the instance."""
        cache = get_cache()
        cache.set("key1", "value1")

        reset_cache()

        new_cache = get_cache()
        assert new_cache.get("key1") is None