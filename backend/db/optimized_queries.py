"""
Optimized database queries module.

This module provides optimized query functions for common database operations,
including search, pagination, and batch operations.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

def build_optimized_search_query(
    table_name: str,
    search_term: Optional[str],
    filter_conditions: Dict[str, Any],
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int
) -> Tuple[str, List[Any]]:
    """
    Build an optimized search query using trigram similarity.
    
    Args:
        table_name (str): The name of the table to query
        search_term (Optional[str]): The search term to use
        filter_conditions (Dict[str, Any]): Filter conditions to apply
        sort_by (str): The column to sort by
        sort_order (str): The sort order (asc or desc)
        limit (int): The maximum number of rows to return
        offset (int): The number of rows to skip
        
    Returns:
        Tuple[str, List[Any]]: The query string and parameters
    """
    # Start building the query
    query = f"""
    WITH filtered_data AS (
        SELECT
            *,
            COUNT(*) OVER() as total_count
        FROM {table_name}
        WHERE 1=1
    """
    
    # Initialize parameters list
    params = []
    
    # Add search condition if provided
    if search_term:
        # Use trigram similarity for better text search performance
        if table_name == 'accounts':
            query += """
            AND (
                acc_id % %s > 0.3 OR
                acc_username % %s > 0.3 OR
                acc_email_address % %s > 0.3
            )
            """
            params.extend([search_term, search_term, search_term])
        elif table_name == 'accounts_normalized':
            query += """
            AND (
                account_id % %s > 0.3 OR
                username % %s > 0.3
            )
            """
            params.extend([search_term, search_term])
    
    # Add filter conditions
    for key, value in filter_conditions.items():
        if value is not None:
            query += f" AND {key} = %s"
            params.append(value)
    
    # Add sorting
    query += f" ORDER BY {sort_by} {sort_order}"
    
    # Close the CTE
    query += """
    )
    SELECT * FROM filtered_data
    LIMIT %s OFFSET %s
    """
    
    # Add limit and offset parameters
    params.extend([limit, offset])
    
    return query, params

def build_batch_fetch_query(
    table_name: str,
    id_column: str,
    ids: List[str],
    columns: Optional[List[str]] = None
) -> Tuple[str, List[Any]]:
    """
    Build a query to fetch multiple records by ID.
    
    Args:
        table_name (str): The name of the table to query
        id_column (str): The name of the ID column
        ids (List[str]): The list of IDs to fetch
        columns (Optional[List[str]]): The columns to select (defaults to all)
        
    Returns:
        Tuple[str, List[Any]]: The query string and parameters
    """
    # Determine columns to select
    select_columns = "*" if not columns else ", ".join(columns)
    
    # Build the query
    query = f"""
    SELECT {select_columns}
    FROM {table_name}
    WHERE {id_column} IN %s
    """
    
    # Convert IDs list to tuple for IN clause
    params = [tuple(ids)]
    
    return query, params

def build_cursor_pagination_query(
    table_name: str,
    cursor_column: str,
    cursor_value: Optional[Any],
    sort_order: str,
    limit: int,
    filter_conditions: Dict[str, Any] = None
) -> Tuple[str, List[Any]]:
    """
    Build a query using cursor-based pagination.
    
    Args:
        table_name (str): The name of the table to query
        cursor_column (str): The column to use for the cursor
        cursor_value (Optional[Any]): The cursor value
        sort_order (str): The sort order (asc or desc)
        limit (int): The maximum number of rows to return
        filter_conditions (Dict[str, Any], optional): Filter conditions to apply
        
    Returns:
        Tuple[str, List[Any]]: The query string and parameters
    """
    # Start building the query
    query = f"""
    SELECT *
    FROM {table_name}
    WHERE 1=1
    """
    
    # Initialize parameters list
    params = []
    
    # Add cursor condition if provided
    if cursor_value is not None:
        operator = ">" if sort_order.lower() == "asc" else "<"
        query += f" AND {cursor_column} {operator} %s"
        params.append(cursor_value)
    
    # Add filter conditions if provided
    if filter_conditions:
        for key, value in filter_conditions.items():
            if value is not None:
                query += f" AND {key} = %s"
                params.append(value)
    
    # Add sorting and limit
    query += f" ORDER BY {cursor_column} {sort_order} LIMIT %s"
    params.append(limit)
    
    return query, params

def build_projection_query(
    table_name: str,
    columns: List[str],
    filter_conditions: Dict[str, Any],
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int
) -> Tuple[str, List[Any]]:
    """
    Build a query with projection (field selection).
    
    Args:
        table_name (str): The name of the table to query
        columns (List[str]): The columns to select
        filter_conditions (Dict[str, Any]): Filter conditions to apply
        sort_by (str): The column to sort by
        sort_order (str): The sort order (asc or desc)
        limit (int): The maximum number of rows to return
        offset (int): The number of rows to skip
        
    Returns:
        Tuple[str, List[Any]]: The query string and parameters
    """
    # Validate and sanitize column names to prevent SQL injection
    valid_columns = []
    for col in columns:
        # Simple validation - column name should only contain alphanumeric chars, underscore
        if col.replace('_', '').isalnum():
            valid_columns.append(col)
    
    if not valid_columns:
        valid_columns = ["*"]  # Default to all columns if none are valid
    
    # Build the select clause
    select_clause = ", ".join(valid_columns)
    
    # Start building the query
    query = f"""
    WITH filtered_data AS (
        SELECT
            {select_clause},
            COUNT(*) OVER() as total_count
        FROM {table_name}
        WHERE 1=1
    """
    
    # Initialize parameters list
    params = []
    
    # Add filter conditions
    for key, value in filter_conditions.items():
        if value is not None:
            query += f" AND {key} = %s"
            params.append(value)
    
    # Add sorting
    query += f" ORDER BY {sort_by} {sort_order}"
    
    # Close the CTE
    query += """
    )
    SELECT * FROM filtered_data
    LIMIT %s OFFSET %s
    """
    
    # Add limit and offset parameters
    params.extend([limit, offset])
    
    return query, params

def build_combined_count_query(
    table_name: str,
    search_term: Optional[str],
    filter_conditions: Dict[str, Any],
    sort_by: str,
    sort_order: str,
    limit: int,
    offset: int
) -> Tuple[str, List[Any]]:
    """
    Build a query that returns both results and count in a single query.
    
    Args:
        table_name (str): The name of the table to query
        search_term (Optional[str]): The search term to use
        filter_conditions (Dict[str, Any]): Filter conditions to apply
        sort_by (str): The column to sort by
        sort_order (str): The sort order (asc or desc)
        limit (int): The maximum number of rows to return
        offset (int): The number of rows to skip
        
    Returns:
        Tuple[str, List[Any]]: The query string and parameters
    """
    # Start building the query
    query = f"""
    WITH filtered_data AS (
        SELECT *
        FROM {table_name}
        WHERE 1=1
    """
    
    # Initialize parameters list
    params = []
    
    # Add search condition if provided
    if search_term:
        if table_name == 'accounts':
            query += """
            AND (
                acc_id ILIKE %s OR
                acc_username ILIKE %s OR
                acc_email_address ILIKE %s
            )
            """
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern, search_pattern])
        elif table_name == 'accounts_normalized':
            query += """
            AND (
                account_id ILIKE %s OR
                username ILIKE %s
            )
            """
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern, search_pattern])
    
    # Add filter conditions
    for key, value in filter_conditions.items():
        if value is not None:
            query += f" AND {key} = %s"
            params.append(value)
    
    # Close the CTE
    query += """
    )
    SELECT 
        fd.*,
        (SELECT COUNT(*) FROM filtered_data) AS total_count
    FROM filtered_data fd
    ORDER BY {sort_by} {sort_order}
    LIMIT %s OFFSET %s
    """.format(sort_by=sort_by, sort_order=sort_order)
    
    # Add limit and offset parameters
    params.extend([limit, offset])
    
    return query, params
