"""
Prediction Cache Module
=======================
Thread-safe in-memory LRU/TTL cache for optimizing geographic predictions.
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Optional, Tuple
import logging


class LRUCache:
    """
    Thread-safe LRU cache with TTL (Time To Live) support.

    Features:
    - LRU eviction when max size is reached
    - TTL-based automatic expiration
    - Thread-safe using RLock
    - Lazy expiration cleanup
    - Resistant to cache stampede (though not implemented for simplicity)
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of entries before LRU eviction
            default_ttl: Default time to live in seconds
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()
        self._logger = logging.getLogger(__name__)

    def _is_expired(self, timestamp: float) -> bool:
        """Check if a cache entry has expired."""
        return time.time() >= timestamp

    def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        now = time.time()
        expired_keys = []

        for key, (_, expiry) in self._cache.items():
            if now >= expiry:
                expired_keys.append(key)
            else:
                # Since we're using OrderedDict and inserting in order,
                # once we find a non-expired entry, we can break
                break

        for key in expired_keys:
            self._cache.pop(key, None)
            self._logger.debug(f"Removed expired cache key: {key}")

    def get(self, key: str) -> Optional[Any]:
        """
        Get an item from the cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self._lock:
            # Clean up expired entries on access
            self._cleanup_expired()

            if key in self._cache:
                value, expiry = self._cache[key]
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                self._logger.debug(f"Cache miss for key: {key}")
                return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set an item in the cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)
        """
        with self._lock:
            # Use provided TTL or default
            ttl = ttl if ttl is not None else self._default_ttl
            expiry = time.time() + ttl

            # If key exists, update it and move to end
            if key in self._cache:
                self._cache[key] = (value, expiry)
                self._cache.move_to_end(key)
            else:
                # Check if we need to evict LRU item
                if len(self._cache) >= self._max_size:
                    # Remove least recently used item
                    lru_key, _ = self._cache.popitem(last=False)
                    self._logger.debug(f"Evicted LRU cache key: {lru_key}")

                # Add new item
                self._cache[key] = (value, expiry)

            self._logger.debug(f"Set cache key: {key} with TTL {ttl}s")

    def delete(self, key: str) -> bool:
        """
        Delete an item from the cache.

        Args:
            key: Cache key

        Returns:
            True if key was found and deleted, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._logger.debug(f"Deleted cache key: {key}")
                return True
            return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._logger.debug("Cleared all cache entries")

    def contains(self, key: str) -> bool:
        """
        Check if key exists in cache and is not expired.

        Args:
            key: Cache key

        Returns:
            True if key exists and is not expired
        """
        with self._lock:
            self._cleanup_expired()
            return key in self._cache

    def size(self) -> int:
        """
        Get current number of entries in cache.

        Returns:
            Number of non-expired entries
        """
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)

    def max_size(self) -> int:
        """Get maximum cache size."""
        return self._max_size


# Global cache instance
_prediction_cache: Optional[LRUCache] = None


def get_prediction_cache() -> LRUCache:
    """
    Get or create the global prediction cache instance.

    Returns:
        LRUCache instance
    """
    global _prediction_cache
    if _prediction_cache is None:
        # Import settings here to avoid circular imports
        from .config import settings
        _prediction_cache = LRUCache(
            max_size=getattr(settings, 'CACHE_MAX_ENTRIES', 1000),
            default_ttl=getattr(settings, 'CACHE_TTL_SECONDS', 300)
        )
    return _prediction_cache


def initialize_cache() -> None:
    """Initialize the global cache instance."""
    get_prediction_cache()


def shutdown_cache() -> None:
    """Shutdown and clear the global cache."""
    global _prediction_cache
    if _prediction_cache is not None:
        _prediction_cache.clear()
        _prediction_cache = None