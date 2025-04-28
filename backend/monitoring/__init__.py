"""
Monitoring package.

This package provides modules for monitoring, logging, tracing, and alerting.
"""

from .config import monitoring_config, get_monitoring_config, log_monitoring_config
from .metrics import (
    init_metrics, shutdown_metrics, record_request, record_active_request,
    record_error, record_db_connection, record_db_query, record_system_metrics
)
from .tracing import (
    init_tracing, shutdown_tracing, start_trace, start_span, end_span,
    add_span_attribute, get_trace_id, get_span_id, get_parent_span_id,
    get_trace, get_span, clear_traces, TracingMiddleware
)
from .logging_config import (
    init_logging, shutdown_logging, configure_logging, configure_json_logging,
    add_trace_context_to_logging, JsonFormatter, TraceContextFilter
)
from .health import (
    init_health_check, shutdown_health_check, check_health, get_health_status,
    check_database, check_memory, check_cpu, check_disk, check_network
)
from .alerting import (
    init_alerting, shutdown_alerting, send_alert, check_alerts, get_alert_status
)

def init_monitoring() -> None:
    """
    Initialize monitoring.
    """
    if not monitoring_config["enabled"]:
        print("Monitoring disabled")
        return
    
    try:
        # Log monitoring configuration
        log_monitoring_config()
        
        # Initialize logging first
        init_logging()
        
        # Initialize other components
        init_metrics()
        init_tracing()
        init_health_check()
        init_alerting()
        
        # Log initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Monitoring initialized")
    except Exception as e:
        print(f"Error initializing monitoring: {e}")

def shutdown_monitoring() -> None:
    """
    Shutdown monitoring.
    """
    if not monitoring_config["enabled"]:
        return
    
    try:
        # Log shutdown
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Monitoring shutdown")
        
        # Shutdown components
        shutdown_alerting()
        shutdown_health_check()
        shutdown_tracing()
        shutdown_metrics()
        
        # Shutdown logging last
        shutdown_logging()
    except Exception as e:
        print(f"Error shutting down monitoring: {e}")

__all__ = [
    # Configuration
    'monitoring_config', 'get_monitoring_config', 'log_monitoring_config',
    
    # Metrics
    'init_metrics', 'shutdown_metrics', 'record_request', 'record_active_request',
    'record_error', 'record_db_connection', 'record_db_query', 'record_system_metrics',
    
    # Tracing
    'init_tracing', 'shutdown_tracing', 'start_trace', 'start_span', 'end_span',
    'add_span_attribute', 'get_trace_id', 'get_span_id', 'get_parent_span_id',
    'get_trace', 'get_span', 'clear_traces', 'TracingMiddleware',
    
    # Logging
    'init_logging', 'shutdown_logging', 'configure_logging', 'configure_json_logging',
    'add_trace_context_to_logging', 'JsonFormatter', 'TraceContextFilter',
    
    # Health
    'init_health_check', 'shutdown_health_check', 'check_health', 'get_health_status',
    'check_database', 'check_memory', 'check_cpu', 'check_disk', 'check_network',
    
    # Alerting
    'init_alerting', 'shutdown_alerting', 'send_alert', 'check_alerts', 'get_alert_status',
    
    # Initialization
    'init_monitoring', 'shutdown_monitoring'
]
