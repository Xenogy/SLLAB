"""
Query cache for caching database query results.

This module provides functions for caching database query results to improve performance.
It supports time-based and size-based cache invalidation.
"""

import logging
import time
import hashlib
import json
import threading
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from functools import wraps
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL = 60  # seconds
DEFAULT_CACHE_SIZE = 100  # items
DEFAULT_ENABLE_CACHE = True

# Cache storage
_cache = {}
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "inserts": 0,
    "evictions": 0,
    "invalidations": 0,
    "size": 0
}

# Cache lock
_cache_lock = threading.RLock()

def generate_cache_key(query: str, params: Optional[Tuple] = None) -> str:
    """
    Generate a cache key for a query and parameters.

    Args:
        query (str): The SQL query
        params (Optional[Tuple], optional): Query parameters. Defaults to None.

    Returns:
        str: The cache key
    """
    # Create a string representation of the query
    key_str = str(query)

    # If params is provided, add a hash of the params
    if params:
        try:
            # Check if params is actually a tuple or list
            if not isinstance(params, (tuple, list)):
                # Convert string or other single value to a tuple with one element
                if isinstance(params, (str, int, float, bool)):
                    params = (params,)
                    logger.debug(f"Converted single value param to tuple: {params}")
                else:
                    logger.warning(f"Params is not a tuple or list: {type(params)}")
                    # Try to convert to a tuple if possible
                    try:
                        params = tuple([params])
                        logger.debug(f"Converted non-standard param to tuple: {params}")
                    except:
                        # Use a random hash for non-tuple/list params
                        import random
                        random_suffix = "_random_" + str(random.getrandbits(32))
                        key_str = str(key_str) + random_suffix
                        # Skip the rest of the param processing
                        return hashlib.md5(key_str.encode()).hexdigest()
            else:
                # Convert params to a JSON-serializable format
                serializable_params = []
                for param in params:
                    if isinstance(param, (str, int, float, bool, type(None))):
                        serializable_params.append(param)
                    else:
                        # For complex objects, use their class name and id
                        param_repr = f"<{param.__class__.__name__}_{id(param)}>"
                        serializable_params.append(param_repr)

                # Create a hash of the serialized params
                params_str = json.dumps(serializable_params, sort_keys=True)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()
                key_str = str(key_str) + "_params_" + params_hash
        except Exception as e:
            logger.warning(f"Error serializing params for cache key: {e}")
            # Use a random hash as fallback
            import random
            random_suffix = "_random_" + str(random.getrandbits(32))
            key_str = str(key_str) + random_suffix

    # Generate a hash of the final key string
    return hashlib.md5(key_str.encode()).hexdigest()

def get_from_cache(key: str) -> Optional[Tuple[Any, float]]:
    """
    Get a value from the cache.

    Args:
        key (str): The cache key

    Returns:
        Optional[Tuple[Any, float]]: The cached value and timestamp, or None if not found
    """
    with _cache_lock:
        if key in _cache:
            value, timestamp = _cache[key]

            # Check if the value has expired
            if time.time() - timestamp > DEFAULT_CACHE_TTL:
                # Remove the expired value
                del _cache[key]
                _cache_stats["evictions"] += 1
                _cache_stats["size"] = len(_cache)
                return None

            # Update cache statistics
            _cache_stats["hits"] += 1

            return value, timestamp

        # Update cache statistics
        _cache_stats["misses"] += 1

        return None

def put_in_cache(key: str, value: Any) -> None:
    """
    Put a value in the cache.

    Args:
        key (str): The cache key
        value (Any): The value to cache
    """
    with _cache_lock:
        # Check if the cache is full
        if len(_cache) >= DEFAULT_CACHE_SIZE:
            # Remove the oldest item
            oldest_key = min(_cache.items(), key=lambda x: x[1][1])[0]
            del _cache[oldest_key]
            _cache_stats["evictions"] += 1

        # Add the new item
        _cache[key] = (value, time.time())
        _cache_stats["inserts"] += 1
        _cache_stats["size"] = len(_cache)

def invalidate_cache(key: Optional[str] = None) -> None:
    """
    Invalidate the cache.

    Args:
        key (Optional[str], optional): The cache key to invalidate. Defaults to None.
    """
    with _cache_lock:
        if key:
            # Invalidate a specific key
            if key in _cache:
                del _cache[key]
                _cache_stats["invalidations"] += 1
                _cache_stats["size"] = len(_cache)
        else:
            # Invalidate the entire cache
            _cache.clear()
            _cache_stats["invalidations"] += 1
            _cache_stats["size"] = 0

def invalidate_cache_by_prefix(prefix: str) -> None:
    """
    Invalidate cache entries with keys starting with a prefix.

    Args:
        prefix (str): The prefix
    """
    with _cache_lock:
        # Find keys that start with the prefix
        keys_to_remove = [k for k in _cache.keys() if k.startswith(prefix)]

        # Remove the keys
        for key in keys_to_remove:
            del _cache[key]
            _cache_stats["invalidations"] += 1

        _cache_stats["size"] = len(_cache)

def invalidate_cache_by_table(table: str) -> None:
    """
    Invalidate cache entries for a specific table.

    Args:
        table (str): The table name
    """
    # This is a simple implementation that invalidates all cache entries
    # For a more sophisticated implementation, you would need to parse the queries
    # and determine which tables they affect
    invalidate_cache()

def get_cache_stats() -> Dict[str, int]:
    """
    Get cache statistics.

    Returns:
        Dict[str, int]: Cache statistics
    """
    with _cache_lock:
        return _cache_stats.copy()

def reset_cache_stats() -> None:
    """
    Reset cache statistics.
    """
    with _cache_lock:
        global _cache_stats
        _cache_stats = {
            "hits": 0,
            "misses": 0,
            "inserts": 0,
            "evictions": 0,
            "invalidations": 0,
            "size": len(_cache)
        }

def enable_cache() -> None:
    """
    Enable the cache.
    """
    global DEFAULT_ENABLE_CACHE
    DEFAULT_ENABLE_CACHE = True

def disable_cache() -> None:
    """
    Disable the cache.
    """
    global DEFAULT_ENABLE_CACHE
    DEFAULT_ENABLE_CACHE = False

def is_cache_enabled() -> bool:
    """
    Check if the cache is enabled.

    Returns:
        bool: True if the cache is enabled, False otherwise
    """
    return DEFAULT_ENABLE_CACHE

def set_cache_ttl(ttl: int) -> None:
    """
    Set the cache TTL.

    Args:
        ttl (int): The TTL in seconds
    """
    global DEFAULT_CACHE_TTL
    DEFAULT_CACHE_TTL = ttl

def set_cache_size(size: int) -> None:
    """
    Set the cache size.

    Args:
        size (int): The cache size
    """
    global DEFAULT_CACHE_SIZE
    DEFAULT_CACHE_SIZE = size

def cached_query(ttl: Optional[int] = None) -> Callable:
    """
    Decorator for caching query results.

    Args:
        ttl (Optional[int], optional): The TTL in seconds. Defaults to None.

    Returns:
        Callable: The decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if the cache is enabled
            if not DEFAULT_ENABLE_CACHE:
                return func(*args, **kwargs)

            # Get query and params from args or kwargs
            query = None
            params = None

            # Try to find query and params in args
            if len(args) > 0:
                query = args[0]
            if len(args) > 1:
                params = args[1]

            # Try to find query and params in kwargs
            if "query" in kwargs:
                query = kwargs["query"]
            if "params" in kwargs:
                params = kwargs["params"]

            # If query is not found, just call the function
            if not query:
                return func(*args, **kwargs)

            # Generate a cache key with error handling
            try:
                key = generate_cache_key(query, params)

                # Try to get the value from the cache
                cached_value = get_from_cache(key)

                if cached_value:
                    value, _ = cached_value
                    return value

                # Call the function
                result = func(*args, **kwargs)

                # Cache the result
                put_in_cache(key, result)

                return result
            except Exception as e:
                logger.warning(f"Error in cache handling, bypassing cache: {e}")
                # If there's any error in the caching logic, just call the function directly
                return func(*args, **kwargs)

        return wrapper

    return decorator

@contextmanager
def cache_context(enable: bool = True) -> None:
    """
    Context manager for controlling cache behavior.

    Args:
        enable (bool, optional): Whether to enable the cache. Defaults to True.

    Yields:
        None
    """
    global DEFAULT_ENABLE_CACHE
    old_value = DEFAULT_ENABLE_CACHE
    try:
        DEFAULT_ENABLE_CACHE = enable
        yield
    finally:
        DEFAULT_ENABLE_CACHE = old_value

def get_cache_report() -> str:
    """
    Get a report of cache statistics.

    Returns:
        str: The report
    """
    stats = get_cache_stats()

    report = []
    report.append("Cache Report")
    report.append("============")
    report.append("")

    report.append(f"Cache enabled: {is_cache_enabled()}")
    report.append(f"Cache TTL: {DEFAULT_CACHE_TTL} seconds")
    report.append(f"Cache size: {DEFAULT_CACHE_SIZE} items")
    report.append(f"Current size: {stats['size']} items")
    report.append("")

    report.append(f"Hits: {stats['hits']}")
    report.append(f"Misses: {stats['misses']}")
    report.append(f"Inserts: {stats['inserts']}")
    report.append(f"Evictions: {stats['evictions']}")
    report.append(f"Invalidations: {stats['invalidations']}")

    total_requests = stats["hits"] + stats["misses"]
    if total_requests > 0:
        hit_ratio = stats["hits"] / total_requests * 100
        report.append(f"Hit ratio: {hit_ratio:.2f}%")

    return "\n".join(report)

def export_cache_stats(file_path: str) -> None:
    """
    Export cache statistics to a file.

    Args:
        file_path (str): The file path
    """
    with _cache_lock:
        data = {
            "stats": _cache_stats,
            "config": {
                "ttl": DEFAULT_CACHE_TTL,
                "size": DEFAULT_CACHE_SIZE,
                "enabled": DEFAULT_ENABLE_CACHE
            }
        }

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Cache statistics exported to {file_path}")

def import_cache_stats(file_path: str) -> None:
    """
    Import cache statistics from a file.

    Args:
        file_path (str): The file path
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    with _cache_lock:
        global _cache_stats
        global DEFAULT_CACHE_TTL
        global DEFAULT_CACHE_SIZE
        global DEFAULT_ENABLE_CACHE

        _cache_stats = data["stats"]
        DEFAULT_CACHE_TTL = data["config"]["ttl"]
        DEFAULT_CACHE_SIZE = data["config"]["size"]
        DEFAULT_ENABLE_CACHE = data["config"]["enabled"]

    logger.info(f"Cache statistics imported from {file_path}")
