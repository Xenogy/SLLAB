# BanCheck API Optimized Parameters

This document explains the optimized parameters implemented in the BanCheck API.

## Overview

The BanCheck API now uses optimized parameters that are automatically adjusted based on the size of the account list being processed. This ensures optimal performance for all types of workloads without requiring manual configuration.

## Adaptive Parameter System

The API automatically selects the optimal parameters based on the number of accounts being processed:

### Small Lists (< 50 accounts)
```
logical_batch_size: 10
max_concurrent_batches: 6
max_workers_per_batch: 3
inter_request_submit_delay: 0.2
max_retries_per_url: 3
retry_delay_seconds: 5
```

### Medium Lists (50-200 accounts)
```
logical_batch_size: 20
max_concurrent_batches: 6
max_workers_per_batch: 3
inter_request_submit_delay: 0.2
max_retries_per_url: 3
retry_delay_seconds: 5
```

### Large Lists (200-500 accounts)
```
logical_batch_size: 30
max_concurrent_batches: 8
max_workers_per_batch: 4
inter_request_submit_delay: 0.3
max_retries_per_url: 3
retry_delay_seconds: 5
```

### Very Large Lists (500+ accounts)
```
logical_batch_size: 50
max_concurrent_batches: 10
max_workers_per_batch: 5
inter_request_submit_delay: 0.5
max_retries_per_url: 3
retry_delay_seconds: 5
```

## Parameter Explanation

### Logical Batch Size
- **What it does**: Determines how many URLs are processed in a single batch
- **Why it scales**: Larger account lists benefit from larger batch sizes to reduce overhead
- **Impact**: Affects overall processing efficiency and resource utilization

### Max Concurrent Batches
- **What it does**: Controls how many batches can run in parallel
- **Why it scales**: Larger account lists benefit from more concurrent batches for better throughput
- **Impact**: Affects overall processing speed and system resource utilization

### Max Workers Per Batch
- **What it does**: Determines how many threads are used within each batch
- **Why it scales**: Larger batches benefit from more workers to maintain good parallelism
- **Impact**: Affects how quickly each batch is processed

### Inter-Request Submit Delay
- **What it does**: Controls the delay between submitting requests within a batch
- **Why it scales**: Larger account lists need longer delays to avoid rate limiting
- **Impact**: Affects reliability and success rate by preventing rate limiting

### Max Retries Per URL
- **What it does**: Determines how many times a failed request will be retried
- **Why it's fixed**: Retry behavior is not dependent on account list size
- **Impact**: Affects reliability by handling transient failures

### Retry Delay Seconds
- **What it does**: Controls how long to wait before retrying a failed request
- **Why it's fixed**: Optimal retry delay is not dependent on account list size
- **Impact**: Balances between quick retries and not overwhelming the target server

## Implementation Details

The optimized parameters are implemented in the `ScriptConfig` class in `app/utils.py`:

```python
@staticmethod
def get_optimized_params(account_count: int) -> Dict[str, any]:
    """
    Get optimized parameters based on account list size.
    
    Args:
        account_count: Number of accounts to check
        
    Returns:
        Dictionary with optimized parameters
    """
    # Default parameters (optimized for small lists < 50 accounts)
    params = {
        "logical_batch_size": 10,
        "max_concurrent_batches": 6,
        "max_workers_per_batch": 3,
        "inter_request_submit_delay": 0.2,
        "max_retries_per_url": 3,
        "retry_delay_seconds": 5
    }
    
    # Medium list (50-200 accounts)
    if 50 <= account_count < 200:
        params["logical_batch_size"] = 20
        
    # Large list (200-500 accounts)
    elif 200 <= account_count < 500:
        params["logical_batch_size"] = 30
        params["max_concurrent_batches"] = 8
        params["max_workers_per_batch"] = 4
        params["inter_request_submit_delay"] = 0.3
        
    # Very large list (500+ accounts)
    elif account_count >= 500:
        params["logical_batch_size"] = 50
        params["max_concurrent_batches"] = 10
        params["max_workers_per_batch"] = 5
        params["inter_request_submit_delay"] = 0.5
        
    return params
```

## Benefits

1. **Simplified API**: Users no longer need to specify complex configuration parameters
2. **Optimal Performance**: Parameters are automatically tuned for the specific workload
3. **Adaptive Scaling**: Performance scales appropriately with account list size
4. **Balanced Resource Usage**: Prevents overloading the system with too many concurrent requests
5. **Improved Reliability**: Parameters are set to values that have been proven to work well

## Conclusion

The optimized parameter system significantly improves the usability and performance of the BanCheck API by automatically selecting the best configuration for each task. This ensures that all users get optimal performance without needing to understand the complex interactions between different parameters.
