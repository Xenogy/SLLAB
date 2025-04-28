"""
Database utility functions for the AccountDB application.

This module provides utility functions for database operations.
"""

import logging
import time
from typing import Optional, List, Dict, Any, Tuple, Union, Generator
from contextlib import contextmanager
import psycopg2
import psycopg2.extensions
from psycopg2 import sql

# Configure logging
logger = logging.getLogger(__name__)

def build_where_clause(
    conditions: Dict[str, Any],
    operator: str = "AND"
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL WHERE clause from a dictionary of conditions.
    
    Args:
        conditions: A dictionary of field names and values
        operator: The operator to use between conditions ("AND" or "OR")
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL WHERE clause and the parameters
    """
    if not conditions:
        return sql.SQL(""), []
    
    clauses = []
    params = []
    
    for field, value in conditions.items():
        if value is None:
            clauses.append(sql.SQL("{} IS NULL").format(sql.Identifier(field)))
        else:
            clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
            params.append(value)
    
    op = sql.SQL(" {} ").format(sql.SQL(operator))
    where_clause = sql.SQL("WHERE ") + op.join(clauses)
    
    return where_clause, params

def build_set_clause(
    fields: Dict[str, Any]
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL SET clause from a dictionary of fields.
    
    Args:
        fields: A dictionary of field names and values
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL SET clause and the parameters
    """
    if not fields:
        return sql.SQL(""), []
    
    clauses = []
    params = []
    
    for field, value in fields.items():
        clauses.append(sql.SQL("{} = %s").format(sql.Identifier(field)))
        params.append(value)
    
    set_clause = sql.SQL("SET ") + sql.SQL(", ").join(clauses)
    
    return set_clause, params

def build_insert_clause(
    fields: Dict[str, Any]
) -> Tuple[sql.Composed, sql.Composed, List[Any]]:
    """
    Build SQL INSERT clauses from a dictionary of fields.
    
    Args:
        fields: A dictionary of field names and values
        
    Returns:
        Tuple[sql.Composed, sql.Composed, List[Any]]: The SQL column names, placeholders, and parameters
    """
    if not fields:
        return sql.SQL(""), sql.SQL(""), []
    
    columns = []
    placeholders = []
    params = []
    
    for field, value in fields.items():
        columns.append(sql.Identifier(field))
        placeholders.append(sql.Placeholder())
        params.append(value)
    
    column_clause = sql.SQL(", ").join(columns)
    placeholder_clause = sql.SQL(", ").join(placeholders)
    
    return column_clause, placeholder_clause, params

def build_order_by_clause(
    sort_by: str,
    sort_order: str = "ASC"
) -> sql.Composed:
    """
    Build a SQL ORDER BY clause.
    
    Args:
        sort_by: The field to sort by
        sort_order: The sort order ("ASC" or "DESC")
        
    Returns:
        sql.Composed: The SQL ORDER BY clause
    """
    if not sort_by:
        return sql.SQL("")
    
    return sql.SQL("ORDER BY {} {}").format(
        sql.Identifier(sort_by),
        sql.SQL(sort_order.upper())
    )

def build_limit_offset_clause(
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL LIMIT/OFFSET clause.
    
    Args:
        limit: The limit
        offset: The offset
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL LIMIT/OFFSET clause and the parameters
    """
    clauses = []
    params = []
    
    if limit is not None:
        clauses.append(sql.SQL("LIMIT %s"))
        params.append(limit)
    
    if offset is not None:
        clauses.append(sql.SQL("OFFSET %s"))
        params.append(offset)
    
    return sql.SQL(" ").join(clauses), params

def build_select_query(
    table: str,
    columns: List[str] = None,
    conditions: Dict[str, Any] = None,
    sort_by: str = None,
    sort_order: str = "ASC",
    limit: int = None,
    offset: int = None
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL SELECT query.
    
    Args:
        table: The table name
        columns: The columns to select
        conditions: The WHERE conditions
        sort_by: The field to sort by
        sort_order: The sort order
        limit: The limit
        offset: The offset
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL query and the parameters
    """
    # Build the SELECT clause
    if columns:
        select_clause = sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(", ").join(sql.Identifier(col) for col in columns),
            sql.Identifier(table)
        )
    else:
        select_clause = sql.SQL("SELECT * FROM {}").format(sql.Identifier(table))
    
    # Build the WHERE clause
    where_clause, where_params = build_where_clause(conditions or {})
    
    # Build the ORDER BY clause
    order_by_clause = build_order_by_clause(sort_by, sort_order) if sort_by else sql.SQL("")
    
    # Build the LIMIT/OFFSET clause
    limit_offset_clause, limit_offset_params = build_limit_offset_clause(limit, offset)
    
    # Combine the clauses
    query = sql.SQL(" ").join([
        select_clause,
        where_clause,
        order_by_clause,
        limit_offset_clause
    ])
    
    # Combine the parameters
    params = where_params + limit_offset_params
    
    return query, params

def build_insert_query(
    table: str,
    fields: Dict[str, Any],
    returning: List[str] = None
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL INSERT query.
    
    Args:
        table: The table name
        fields: The fields to insert
        returning: The columns to return
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL query and the parameters
    """
    # Build the INSERT clause
    column_clause, placeholder_clause, params = build_insert_clause(fields)
    
    # Build the RETURNING clause
    if returning:
        returning_clause = sql.SQL("RETURNING {}").format(
            sql.SQL(", ").join(sql.Identifier(col) for col in returning)
        )
    else:
        returning_clause = sql.SQL("")
    
    # Combine the clauses
    query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) {}").format(
        sql.Identifier(table),
        column_clause,
        placeholder_clause,
        returning_clause
    )
    
    return query, params

def build_update_query(
    table: str,
    fields: Dict[str, Any],
    conditions: Dict[str, Any],
    returning: List[str] = None
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL UPDATE query.
    
    Args:
        table: The table name
        fields: The fields to update
        conditions: The WHERE conditions
        returning: The columns to return
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL query and the parameters
    """
    # Build the SET clause
    set_clause, set_params = build_set_clause(fields)
    
    # Build the WHERE clause
    where_clause, where_params = build_where_clause(conditions)
    
    # Build the RETURNING clause
    if returning:
        returning_clause = sql.SQL("RETURNING {}").format(
            sql.SQL(", ").join(sql.Identifier(col) for col in returning)
        )
    else:
        returning_clause = sql.SQL("")
    
    # Combine the clauses
    query = sql.SQL("UPDATE {} {} {} {}").format(
        sql.Identifier(table),
        set_clause,
        where_clause,
        returning_clause
    )
    
    # Combine the parameters
    params = set_params + where_params
    
    return query, params

def build_delete_query(
    table: str,
    conditions: Dict[str, Any],
    returning: List[str] = None
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL DELETE query.
    
    Args:
        table: The table name
        conditions: The WHERE conditions
        returning: The columns to return
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL query and the parameters
    """
    # Build the WHERE clause
    where_clause, where_params = build_where_clause(conditions)
    
    # Build the RETURNING clause
    if returning:
        returning_clause = sql.SQL("RETURNING {}").format(
            sql.SQL(", ").join(sql.Identifier(col) for col in returning)
        )
    else:
        returning_clause = sql.SQL("")
    
    # Combine the clauses
    query = sql.SQL("DELETE FROM {} {} {}").format(
        sql.Identifier(table),
        where_clause,
        returning_clause
    )
    
    return query, where_params

def build_count_query(
    table: str,
    conditions: Dict[str, Any] = None
) -> Tuple[sql.Composed, List[Any]]:
    """
    Build a SQL COUNT query.
    
    Args:
        table: The table name
        conditions: The WHERE conditions
        
    Returns:
        Tuple[sql.Composed, List[Any]]: The SQL query and the parameters
    """
    # Build the COUNT clause
    count_clause = sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table))
    
    # Build the WHERE clause
    where_clause, where_params = build_where_clause(conditions or {})
    
    # Combine the clauses
    query = sql.SQL(" ").join([count_clause, where_clause])
    
    return query, where_params
