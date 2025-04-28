"""
Query analyzer for identifying slow queries.

This module provides functions for analyzing query performance and identifying slow queries.
It logs slow queries and provides recommendations for optimization.
"""

import logging
import time
import re
import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from functools import wraps
from contextlib import contextmanager
from threading import local

# Configure logging
logger = logging.getLogger(__name__)

# Thread-local storage for query context
_local = local()

# Configuration
DEFAULT_SLOW_QUERY_THRESHOLD = 0.5  # seconds
DEFAULT_VERY_SLOW_QUERY_THRESHOLD = 2.0  # seconds
DEFAULT_MAX_QUERIES_TO_STORE = 100
DEFAULT_ENABLE_QUERY_ANALYSIS = True

# Query statistics
query_stats = {
    "total_queries": 0,
    "slow_queries": 0,
    "very_slow_queries": 0,
    "total_execution_time": 0.0,
    "max_execution_time": 0.0,
    "avg_execution_time": 0.0,
    "queries_by_table": {},
    "queries_by_type": {
        "SELECT": 0,
        "INSERT": 0,
        "UPDATE": 0,
        "DELETE": 0,
        "OTHER": 0
    }
}

# Store recent slow queries
recent_slow_queries = []

def get_query_type(query: str) -> str:
    """
    Get the type of a query (SELECT, INSERT, UPDATE, DELETE, OTHER).
    
    Args:
        query (str): The SQL query
        
    Returns:
        str: The query type
    """
    query = query.strip().upper()
    
    if query.startswith("SELECT"):
        return "SELECT"
    elif query.startswith("INSERT"):
        return "INSERT"
    elif query.startswith("UPDATE"):
        return "UPDATE"
    elif query.startswith("DELETE"):
        return "DELETE"
    else:
        return "OTHER"

def get_tables_from_query(query: str) -> List[str]:
    """
    Extract table names from a query.
    
    Args:
        query (str): The SQL query
        
    Returns:
        List[str]: List of table names
    """
    # This is a simple implementation that may not work for all queries
    # For a more robust solution, consider using a SQL parser
    
    # Convert to lowercase for case-insensitive matching
    query = query.lower()
    
    # Find tables in FROM clause
    from_tables = []
    from_match = re.search(r'from\s+([a-zA-Z0-9_,\s]+)', query)
    if from_match:
        tables_str = from_match.group(1)
        from_tables = [t.strip() for t in tables_str.split(',')]
    
    # Find tables in JOIN clauses
    join_tables = []
    join_matches = re.finditer(r'join\s+([a-zA-Z0-9_]+)', query)
    for match in join_matches:
        join_tables.append(match.group(1).strip())
    
    # Find tables in UPDATE clause
    update_tables = []
    update_match = re.search(r'update\s+([a-zA-Z0-9_]+)', query)
    if update_match:
        update_tables.append(update_match.group(1).strip())
    
    # Find tables in INSERT clause
    insert_tables = []
    insert_match = re.search(r'insert\s+into\s+([a-zA-Z0-9_]+)', query)
    if insert_match:
        insert_tables.append(insert_match.group(1).strip())
    
    # Find tables in DELETE clause
    delete_tables = []
    delete_match = re.search(r'delete\s+from\s+([a-zA-Z0-9_]+)', query)
    if delete_match:
        delete_tables.append(delete_match.group(1).strip())
    
    # Combine all tables
    all_tables = from_tables + join_tables + update_tables + insert_tables + delete_tables
    
    # Remove duplicates and return
    return list(set(all_tables))

def analyze_query(query: str, execution_time: float) -> Dict[str, Any]:
    """
    Analyze a query and provide recommendations.
    
    Args:
        query (str): The SQL query
        execution_time (float): The execution time in seconds
        
    Returns:
        Dict[str, Any]: Analysis results
    """
    analysis = {
        "query": query,
        "execution_time": execution_time,
        "is_slow": execution_time >= DEFAULT_SLOW_QUERY_THRESHOLD,
        "is_very_slow": execution_time >= DEFAULT_VERY_SLOW_QUERY_THRESHOLD,
        "query_type": get_query_type(query),
        "tables": get_tables_from_query(query),
        "recommendations": []
    }
    
    # Check for common issues and add recommendations
    
    # Check for SELECT *
    if "SELECT *" in query.upper():
        analysis["recommendations"].append(
            "Avoid using SELECT * and specify only the columns you need"
        )
    
    # Check for missing WHERE clause in SELECT
    if analysis["query_type"] == "SELECT" and "WHERE" not in query.upper():
        analysis["recommendations"].append(
            "Consider adding a WHERE clause to limit the results"
        )
    
    # Check for potential full table scans
    if "WHERE" in query.upper() and "LIKE" in query.upper() and "%" in query:
        analysis["recommendations"].append(
            "LIKE with leading wildcard (%) may cause full table scan"
        )
    
    # Check for JOIN without conditions
    if "JOIN" in query.upper() and "ON" not in query.upper():
        analysis["recommendations"].append(
            "JOIN without ON condition may cause cartesian product"
        )
    
    # Check for ORDER BY on non-indexed columns
    if "ORDER BY" in query.upper():
        analysis["recommendations"].append(
            "Ensure columns in ORDER BY clause are indexed"
        )
    
    # Check for GROUP BY on non-indexed columns
    if "GROUP BY" in query.upper():
        analysis["recommendations"].append(
            "Ensure columns in GROUP BY clause are indexed"
        )
    
    # Check for subqueries
    if "(" in query and "SELECT" in query.upper().split("(")[1]:
        analysis["recommendations"].append(
            "Consider replacing subqueries with JOINs"
        )
    
    # Check for multiple JOINs
    join_count = query.upper().count("JOIN")
    if join_count > 2:
        analysis["recommendations"].append(
            f"Query has {join_count} JOINs, consider simplifying"
        )
    
    return analysis

def record_query(query: str, params: Optional[Tuple] = None, execution_time: float = 0.0) -> None:
    """
    Record a query for analysis.
    
    Args:
        query (str): The SQL query
        params (Optional[Tuple], optional): Query parameters. Defaults to None.
        execution_time (float, optional): The execution time in seconds. Defaults to 0.0.
    """
    # Check if query analysis is enabled
    if not getattr(_local, "enable_query_analysis", DEFAULT_ENABLE_QUERY_ANALYSIS):
        return
    
    # Update query statistics
    query_stats["total_queries"] += 1
    query_stats["total_execution_time"] += execution_time
    
    if execution_time > query_stats["max_execution_time"]:
        query_stats["max_execution_time"] = execution_time
    
    query_stats["avg_execution_time"] = (
        query_stats["total_execution_time"] / query_stats["total_queries"]
    )
    
    # Update query type statistics
    query_type = get_query_type(query)
    query_stats["queries_by_type"][query_type] += 1
    
    # Update table statistics
    tables = get_tables_from_query(query)
    for table in tables:
        if table not in query_stats["queries_by_table"]:
            query_stats["queries_by_table"][table] = 0
        query_stats["queries_by_table"][table] += 1
    
    # Check if this is a slow query
    is_slow = execution_time >= DEFAULT_SLOW_QUERY_THRESHOLD
    is_very_slow = execution_time >= DEFAULT_VERY_SLOW_QUERY_THRESHOLD
    
    if is_slow:
        query_stats["slow_queries"] += 1
        
        # Analyze the query
        analysis = analyze_query(query, execution_time)
        
        # Add to recent slow queries
        recent_slow_queries.append(analysis)
        
        # Keep only the most recent slow queries
        if len(recent_slow_queries) > DEFAULT_MAX_QUERIES_TO_STORE:
            recent_slow_queries.pop(0)
        
        # Log the slow query
        log_message = f"Slow query ({execution_time:.2f}s): {query}"
        if params:
            log_message += f" with params: {params}"
        
        if analysis["recommendations"]:
            log_message += f"\nRecommendations: {', '.join(analysis['recommendations'])}"
        
        if is_very_slow:
            query_stats["very_slow_queries"] += 1
            logger.warning(log_message)
        else:
            logger.info(log_message)

@contextmanager
def query_analyzer(query: str, params: Optional[Tuple] = None) -> None:
    """
    Context manager for analyzing query performance.
    
    Args:
        query (str): The SQL query
        params (Optional[Tuple], optional): Query parameters. Defaults to None.
        
    Yields:
        None
    """
    start_time = time.time()
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        record_query(query, params, execution_time)

def analyze_query_decorator(func: Callable) -> Callable:
    """
    Decorator for analyzing query performance.
    
    Args:
        func (Callable): The function to decorate
        
    Returns:
        Callable: The decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
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
        
        # Use the query analyzer context manager
        with query_analyzer(query, params):
            return func(*args, **kwargs)
    
    return wrapper

def get_query_stats() -> Dict[str, Any]:
    """
    Get query statistics.
    
    Returns:
        Dict[str, Any]: Query statistics
    """
    return query_stats

def get_recent_slow_queries() -> List[Dict[str, Any]]:
    """
    Get recent slow queries.
    
    Returns:
        List[Dict[str, Any]]: Recent slow queries
    """
    return recent_slow_queries

def reset_query_stats() -> None:
    """
    Reset query statistics.
    """
    global query_stats
    global recent_slow_queries
    
    query_stats = {
        "total_queries": 0,
        "slow_queries": 0,
        "very_slow_queries": 0,
        "total_execution_time": 0.0,
        "max_execution_time": 0.0,
        "avg_execution_time": 0.0,
        "queries_by_table": {},
        "queries_by_type": {
            "SELECT": 0,
            "INSERT": 0,
            "UPDATE": 0,
            "DELETE": 0,
            "OTHER": 0
        }
    }
    
    recent_slow_queries = []

def enable_query_analysis() -> None:
    """
    Enable query analysis.
    """
    _local.enable_query_analysis = True

def disable_query_analysis() -> None:
    """
    Disable query analysis.
    """
    _local.enable_query_analysis = False

def is_query_analysis_enabled() -> bool:
    """
    Check if query analysis is enabled.
    
    Returns:
        bool: True if query analysis is enabled, False otherwise
    """
    return getattr(_local, "enable_query_analysis", DEFAULT_ENABLE_QUERY_ANALYSIS)

def set_slow_query_threshold(threshold: float) -> None:
    """
    Set the threshold for slow queries.
    
    Args:
        threshold (float): The threshold in seconds
    """
    global DEFAULT_SLOW_QUERY_THRESHOLD
    DEFAULT_SLOW_QUERY_THRESHOLD = threshold

def set_very_slow_query_threshold(threshold: float) -> None:
    """
    Set the threshold for very slow queries.
    
    Args:
        threshold (float): The threshold in seconds
    """
    global DEFAULT_VERY_SLOW_QUERY_THRESHOLD
    DEFAULT_VERY_SLOW_QUERY_THRESHOLD = threshold

def set_max_queries_to_store(max_queries: int) -> None:
    """
    Set the maximum number of queries to store.
    
    Args:
        max_queries (int): The maximum number of queries
    """
    global DEFAULT_MAX_QUERIES_TO_STORE
    DEFAULT_MAX_QUERIES_TO_STORE = max_queries

def get_slow_query_report() -> str:
    """
    Get a report of slow queries.
    
    Returns:
        str: The report
    """
    report = []
    report.append("Slow Query Report")
    report.append("=================")
    report.append("")
    
    report.append(f"Total queries: {query_stats['total_queries']}")
    report.append(f"Slow queries: {query_stats['slow_queries']} ({query_stats['slow_queries'] / query_stats['total_queries'] * 100:.2f}% of total)")
    report.append(f"Very slow queries: {query_stats['very_slow_queries']} ({query_stats['very_slow_queries'] / query_stats['total_queries'] * 100:.2f}% of total)")
    report.append(f"Average execution time: {query_stats['avg_execution_time']:.6f}s")
    report.append(f"Maximum execution time: {query_stats['max_execution_time']:.6f}s")
    report.append("")
    
    report.append("Queries by type:")
    for query_type, count in query_stats["queries_by_type"].items():
        if count > 0:
            report.append(f"  {query_type}: {count} ({count / query_stats['total_queries'] * 100:.2f}% of total)")
    report.append("")
    
    report.append("Queries by table:")
    for table, count in sorted(query_stats["queries_by_table"].items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {table}: {count} ({count / query_stats['total_queries'] * 100:.2f}% of total)")
    report.append("")
    
    report.append("Recent slow queries:")
    for i, query in enumerate(recent_slow_queries):
        report.append(f"  {i+1}. {query['execution_time']:.6f}s: {query['query']}")
        if query["recommendations"]:
            report.append(f"     Recommendations: {', '.join(query['recommendations'])}")
    
    return "\n".join(report)

def export_query_stats(file_path: str) -> None:
    """
    Export query statistics to a file.
    
    Args:
        file_path (str): The file path
    """
    data = {
        "stats": query_stats,
        "recent_slow_queries": recent_slow_queries
    }
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Query statistics exported to {file_path}")

def import_query_stats(file_path: str) -> None:
    """
    Import query statistics from a file.
    
    Args:
        file_path (str): The file path
    """
    global query_stats
    global recent_slow_queries
    
    with open(file_path, "r") as f:
        data = json.load(f)
    
    query_stats = data["stats"]
    recent_slow_queries = data["recent_slow_queries"]
    
    logger.info(f"Query statistics imported from {file_path}")
