# BanCheck API Proxy Management

This document explains the proxy management system implemented in the BanCheck API.

## Overview

The BanCheck API now includes a robust proxy management system that ensures proxies are not reused while they're still in use by another task. This prevents issues such as rate limiting, reduced performance, and increased failures that can occur when proxies are overloaded.

## How It Works

### ProxyManager Class

The core of the proxy management system is the `ProxyManager` class in `app/proxy_manager.py`. This class:

1. Tracks which proxies are available and which are in use
2. Ensures thread-safety with a lock mechanism
3. Provides methods to get and release proxies
4. Tracks proxy usage statistics

```python
class ProxyManager:
    def __init__(self, proxies: List[str]):
        self.all_proxies = list(proxies) if proxies else []
        self.available_proxies = list(proxies) if proxies else []
        self.in_use_proxies: Set[str] = set()
        self.lock = threading.Lock()
        self.proxy_usage_count: Dict[str, int] = {proxy: 0 for proxy in self.all_proxies}
```

### Task-Specific Proxy Managers

Each task gets its own `ProxyManager` instance, stored in a global dictionary:

```python
# Global dictionary to store proxy managers for each task
proxy_managers: Dict[str, ProxyManager] = {}
```

This ensures that proxies are managed independently for each task, preventing cross-task interference.

### Proxy Allocation and Release

When a batch needs a proxy, it requests one from the proxy manager:

```python
proxy_for_this_outer_batch = proxy_manager.get_proxy()
```

When a batch completes, it releases the proxy back to the pool:

```python
if proxy_used:
    proxy_manager.release_proxy(proxy_used)
```

### Automatic Concurrency Adjustment

If the number of concurrent batches exceeds the number of available proxies, the system automatically reduces the concurrency to match the proxy count:

```python
if proxies_list and params['max_concurrent_batches'] > len(proxies_list):
    print(f"[API Task {task_id}] Warning: max_concurrent_batches ({params['max_concurrent_batches']}) exceeds proxy count ({len(proxies_list)})")
    print(f"[API Task {task_id}] Reducing max_concurrent_batches to match proxy count")
    params['max_concurrent_batches'] = len(proxies_list)
```

## Benefits

1. **Prevents Proxy Overuse**: Each proxy is used by only one batch at a time
2. **Reduces Rate Limiting**: Prevents multiple batches from overwhelming a single proxy
3. **Improves Reliability**: Fewer proxy errors due to better load distribution
4. **Optimizes Performance**: Automatically adjusts concurrency based on available proxies
5. **Provides Transparency**: Includes proxy usage statistics in task results

## Proxy Statistics

The API now includes proxy usage statistics in the task status response:

```json
{
  "task_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "COMPLETED",
  "message": "Processing complete.",
  "progress": 100,
  "results": [...],
  "proxy_stats": {
    "total_proxies": 5,
    "available_proxies": 5,
    "in_use_proxies": 0,
    "usage_counts": {
      "http://proxy1.example.com:8080": 3,
      "http://proxy2.example.com:8080": 2,
      "http://proxy3.example.com:8080": 2,
      "http://proxy4.example.com:8080": 1,
      "http://proxy5.example.com:8080": 1
    }
  }
}
```

## Best Practices

1. **Provide Enough Proxies**: For optimal performance, provide at least as many proxies as the `max_concurrent_batches` parameter
2. **Monitor Proxy Usage**: Check the proxy statistics to identify overused or problematic proxies
3. **Balance Concurrency**: Set `max_concurrent_batches` based on the number of available proxies
4. **Rotate Proxies**: Regularly rotate your proxy list to prevent IP bans

## Implementation Details

The proxy management system is implemented in the following files:

- `app/proxy_manager.py`: Contains the `ProxyManager` class
- `app/tasks.py`: Uses the proxy manager to allocate and release proxies
- `app/models.py`: Includes proxy statistics in the task status model

## Conclusion

The new proxy management system significantly improves the reliability and efficiency of the BanCheck API when using proxies. It ensures that proxies are used optimally and prevents common issues associated with proxy overuse.
