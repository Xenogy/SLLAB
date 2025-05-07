# BanCheck API Performance Tuning

This document outlines the performance tuning process and recommended configuration for the BanCheck API.

## Benchmark Results

We conducted extensive benchmarking to find the optimal parameter settings for the BanCheck API. The benchmarks were run with:
- 50 Steam accounts to check
- Various combinations of concurrency and retry parameters
- Proxy support enabled

### Top 5 Configurations by Performance

| Rank | Time (s) | Success Rate | Logical Batch Size | Max Concurrent Batches | Max Workers Per Batch | Inter-Request Delay | Max Retries | Retry Delay |
|------|----------|--------------|--------------------|-----------------------|----------------------|---------------------|-------------|------------|
| 1    | 10.23    | 100%         | 10                 | 6                     | 3                    | 0.2                 | 3           | 5          |
| 2    | 12.24    | 100%         | 20                 | 6                     | 5                    | 0.1                 | 2           | 7          |
| 3    | 15.19    | 100%         | 10                 | 4                     | 2                    | 0.3                 | 2           | 7          |
| 4    | 17.26    | 100%         | 20                 | 2                     | 4                    | 0.05                | 2           | 3          |
| 5    | 18.31    | 100%         | 20                 | 3                     | 3                    | 0.1                 | 2           | 5          |

## Recommended Configuration

Based on the benchmark results, we recommend the following configuration:

```python
class ScriptConfig:
    MIN_URLS_PER_LOGICAL_BATCH = 10
    MAX_URLS_PER_LOGICAL_BATCH = 100 
    DEFAULT_MAX_CONCURRENT_BATCHES = 6  # Increased from 3 to 6 for better parallelism
    DEFAULT_MAX_WORKERS_PER_BATCH = 3   # Kept at 3 as it provides good balance
    MIN_WORKERS = 1
    MAX_WORKERS_CAP_TOTAL = 50 
    DEFAULT_INTER_REQUEST_SUBMIT_DELAY_S = 0.2  # Increased from 0.1 to 0.2 to reduce rate limiting
    DEFAULT_MAX_RETRIES_PER_URL = 3     # Increased from 2 to 3 for better reliability
    DEFAULT_RETRY_DELAY_SECONDS = 5     # Kept at 5 seconds as it works well
```

## Parameter Explanation

### Logical Batch Size (10)
- **What it does**: Determines how many URLs are processed in a single batch
- **Why this value**: Smaller batch sizes (10) allow for more efficient distribution of work and better parallelism
- **Impact**: Reduces overall processing time by allowing more batches to run concurrently

### Max Concurrent Batches (6)
- **What it does**: Controls how many batches can run in parallel
- **Why this value**: Higher concurrency (6) allows for better utilization of system resources
- **Impact**: Significantly improves throughput by processing more batches simultaneously

### Max Workers Per Batch (3)
- **What it does**: Determines how many threads are used within each batch
- **Why this value**: 3 workers per batch provides a good balance between parallelism and overhead
- **Impact**: Optimizes resource usage within each batch without overwhelming the system

### Inter-Request Submit Delay (0.2s)
- **What it does**: Controls the delay between submitting requests within a batch
- **Why this value**: 0.2 seconds provides enough spacing to avoid rate limiting while maintaining good throughput
- **Impact**: Reduces the chance of being rate-limited by Steam's API

### Max Retries Per URL (3)
- **What it does**: Determines how many times a failed request will be retried
- **Why this value**: 3 retries provides good reliability without wasting time on consistently failing requests
- **Impact**: Improves success rate by handling transient failures

### Retry Delay Seconds (5)
- **What it does**: Controls how long to wait before retrying a failed request
- **Why this value**: 5 seconds gives enough time for transient issues to resolve
- **Impact**: Balances between quick retries and not overwhelming the target server

## Scaling Considerations

For larger workloads (more than 100 accounts), consider:
1. Increasing the `MAX_URLS_PER_LOGICAL_BATCH` to 150-200
2. Keeping `DEFAULT_MAX_CONCURRENT_BATCHES` at 6 to avoid overwhelming the system
3. Potentially increasing `DEFAULT_MAX_WORKERS_PER_BATCH` to 4 for larger batches

For systems with limited resources:
1. Reduce `DEFAULT_MAX_CONCURRENT_BATCHES` to 4
2. Keep `DEFAULT_MAX_WORKERS_PER_BATCH` at 3
3. Increase `DEFAULT_INTER_REQUEST_SUBMIT_DELAY_S` to 0.3 to reduce resource contention

## Proxy Considerations

When using proxies:
1. Ensure you have at least as many proxies as `DEFAULT_MAX_CONCURRENT_BATCHES`
2. For optimal performance, have at least 10-15 proxies available
3. If using fewer proxies, consider reducing `DEFAULT_MAX_CONCURRENT_BATCHES` to match your proxy count

## Conclusion

The optimized configuration provides a good balance between:
- Fast processing of individual tasks
- High throughput for multiple tasks
- Reliability through appropriate retry mechanisms
- Resource efficiency

These settings should work well for most use cases, but can be further tuned based on specific requirements and system capabilities.
