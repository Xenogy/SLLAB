"""
Timeseries package.

This package provides modules for collecting, storing, and retrieving timeseries data.
"""

from .collector import (
    init_collector, shutdown_collector, collect_system_metrics,
    collect_vm_metrics, collect_account_metrics, collect_job_metrics,
    start_collector_thread, stop_collector_thread
)
from .storage import (
    store_metric, store_metrics_batch, get_metric_data, get_metric_aggregates,
    get_latest_metric_value, get_metric_statistics
)
from .aggregator import (
    init_aggregator, shutdown_aggregator, aggregate_metrics,
    start_aggregator_thread, stop_aggregator_thread
)
from .config import (
    timeseries_config, get_timeseries_config, log_timeseries_config
)

__all__ = [
    # Configuration
    'timeseries_config', 'get_timeseries_config', 'log_timeseries_config',
    
    # Collector
    'init_collector', 'shutdown_collector', 'collect_system_metrics',
    'collect_vm_metrics', 'collect_account_metrics', 'collect_job_metrics',
    'start_collector_thread', 'stop_collector_thread',
    
    # Storage
    'store_metric', 'store_metrics_batch', 'get_metric_data', 'get_metric_aggregates',
    'get_latest_metric_value', 'get_metric_statistics',
    
    # Aggregator
    'init_aggregator', 'shutdown_aggregator', 'aggregate_metrics',
    'start_aggregator_thread', 'stop_aggregator_thread'
]
