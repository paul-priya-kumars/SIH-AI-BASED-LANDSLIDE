"""
Unit tests for the prediction cache module.
"""
import time
import threading
from backend.app.cache import LRUCache, get_prediction_cache, initialize_cache, shutdown_cache
from backend.app.config import settings


def test_cache_service_integration():
    """Test that cache integrates properly with services."""
    # Temporarily enable cache for this test
    original_cache_enabled = settings.CACHE_ENABLED
    settings.CACHE_ENABLED = True

    try:
        # Initialize cache
        initialize_cache()
        cache = get_prediction_cache()

        # Test that we can store and retrieve a mock service result
        test_key = "risk:11.41:76.69"
        test_value = {"risk_probability": 0.75, "risk_level": "HIGH"}

        # Store in cache
        cache.set(test_key, test_value)

        # Retrieve from cache
        cached_value = cache.get(test_key)
        assert cached_value == test_value

        # Test cache miss
        assert cache.get("nonexistent_key") is None

    finally:
        # Restore original setting
        settings.CACHE_ENABLED = original_cache_enabled
        # Clean up
        shutdown_cache()


def test_cache_initialization():
    """Test cache initialization with default and custom parameters."""
    # Test default initialization
    cache = LRUCache()
    assert cache.max_size() == 1000  # default
    # Note: default_ttl is not exposed as a property, but we can infer from behavior

    # Test custom initialization
    cache_custom = LRUCache(max_size=500, default_ttl=600)
    assert cache_custom.max_size() == 500


def test_cache_set_and_get():
    """Test basic set and get operations."""
    cache = LRUCache(max_size=10)

    # Test setting and getting a value
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Test getting non-existent key
    assert cache.get("nonexistent") is None

    # Test overwriting a value
    cache.set("key1", "updated_value")
    assert cache.get("key1") == "updated_value"


def test_cache_ttl_expiration():
    """Test that entries expire after TTL."""
    cache = LRUCache(max_size=10, default_ttl=0.1)  # 100ms TTL

    # Set a value
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    # Wait for expiration
    time.sleep(0.15)  # Wait 150ms

    # Value should be expired
    assert cache.get("key1") is None


def test_cache_lru_eviction():
    """Test LRU eviction when cache exceeds max size."""
    cache = LRUCache(max_size=3)

    # Fill cache to capacity
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    # All should be present
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"

    # Add one more to trigger eviction
    cache.set("key4", "value4")

    # First key should be evicted (LRU)
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"

    # Access key2 to make it recently used
    cache.get("key2")

    # Add another key - key3 should be evicted now (least recently used)
    cache.set("key5", "value5")
    assert cache.get("key3") is None
    assert cache.get("key2") == "value2"  # Recently used
    assert cache.get("key4") == "value4"
    assert cache.get("key5") == "value5"


def test_cache_delete_and_clear():
    """Test delete and clear operations."""
    cache = LRUCache(max_size=10)

    # Set some values
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Test delete
    assert cache.delete("key1") is True
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"

    # Test deleting non-existent key
    assert cache.delete("nonexistent") is False

    # Test clear
    cache.clear()
    assert cache.get("key2") is None
    assert cache.size() == 0


def test_cache_contains():
    """Test contains method."""
    cache = LRUCache(max_size=10)

    # Empty cache
    assert cache.contains("key1") is False

    # Add a value
    cache.set("key1", "value1")
    assert cache.contains("key1") is True

    # Expired value should not be contained
    cache_short_ttl = LRUCache(max_size=10, default_ttl=0.1)
    cache_short_ttl.set("key1", "value1")
    time.sleep(0.15)
    assert cache_short_ttl.contains("key1") is False


def test_cache_size():
    """Test size method."""
    cache = LRUCache(max_size=10)

    assert cache.size() == 0

    cache.set("key1", "value1")
    assert cache.size() == 1

    cache.set("key2", "value2")
    assert cache.size() == 2

    # Add expired entry, size should not count it
    cache_short_ttl = LRUCache(max_size=10, default_ttl=0.1)
    cache_short_ttl.set("key1", "value1")
    time.sleep(0.15)
    assert cache_short_ttl.size() == 0


def test_cache_thread_safety():
    """Test thread safety of cache operations."""
    cache = LRUCache(max_size=1000)
    errors = []

    def worker(thread_id):
        try:
            # Each thread sets and gets unique keys
            for i in range(100):
                key = f"thread{thread_id}_key{i}"
                value = f"value{thread_id}_{i}"
                cache.set(key, value)
                retrieved = cache.get(key)
                if retrieved != value:
                    errors.append(f"Thread {thread_id}: mismatch for {key}")
        except Exception as e:
            errors.append(f"Thread {thread_id}: {str(e)}")

    # Create and start threads
    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # Check for errors
    assert len(errors) == 0, f"Thread safety errors: {errors}"


def test_global_cache_functions():
    """Test global cache initialization and shutdown functions."""
    # Initialize global cache
    initialize_cache()
    cache = get_prediction_cache()
    assert isinstance(cache, LRUCache)

    # Test that we get the same instance
    cache2 = get_prediction_cache()
    assert cache is cache2

    # Shutdown cache
    shutdown_cache()

    # Getting cache after shutdown should create a new instance
    cache3 = get_prediction_cache()
    assert cache3 is not cache  # Should be a new instance

    # Clean up
    shutdown_cache()


def test_cache_with_different_value_types():
    """Test cache with various value types."""
    cache = LRUCache(max_size=10)

    # Test with string
    cache.set("str_key", "string_value")
    assert cache.get("str_key") == "string_value"

    # Test with integer
    cache.set("int_key", 42)
    assert cache.get("int_key") == 42

    # Test with list
    cache.set("list_key", [1, 2, 3])
    assert cache.get("list_key") == [1, 2, 3]

    # Test with dictionary
    cache.set("dict_key", {"a": 1, "b": 2})
    assert cache.get("dict_key") == {"a": 1, "b": 2}

    # Test with None
    cache.set("none_key", None)
    assert cache.get("none_key") is None

    # Test with boolean
    cache.set("bool_key", True)
    assert cache.get("bool_key") is True