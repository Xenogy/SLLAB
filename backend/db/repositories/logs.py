"""
Log repository for database operations related to logs.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from db.repositories.base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class LogRepository(BaseRepository):
    """Repository for log operations."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the LogRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "logs"
        self.id_column = "id"
        self.default_columns = """
            l.id, l.timestamp, lc.name as category, ls.name as source,
            ll.name as level, l.message, l.details, l.entity_type,
            l.entity_id, l.user_id, l.owner_id, l.trace_id,
            l.span_id, l.parent_span_id, l.created_at
        """
        self.default_order_by = "l.timestamp DESC"
        self.search_columns = ["l.message", "l.entity_id", "lc.name", "ls.name"]

        # Define joins for retrieving log data with related information
        self.default_joins = """
            LEFT JOIN logs_categories lc ON l.category_id = lc.id
            LEFT JOIN logs_sources ls ON l.source_id = ls.id
            LEFT JOIN logs_levels ll ON l.level_id = ll.id
        """

    def add_log(self,
                message: str,
                level: str = "INFO",
                category: Optional[str] = None,
                source: Optional[str] = None,
                details: Optional[Dict[str, Any]] = None,
                entity_type: Optional[str] = None,
                entity_id: Optional[str] = None,
                user_id: Optional[int] = None,
                owner_id: Optional[int] = None,
                trace_id: Optional[str] = None,
                span_id: Optional[str] = None,
                parent_span_id: Optional[str] = None,
                timestamp: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """
        Add a log entry to the database.

        Args:
            message (str): The log message
            level (str, optional): The log level. Defaults to "INFO".
            category (Optional[str], optional): The log category. Defaults to None.
            source (Optional[str], optional): The log source. Defaults to None.
            details (Optional[Dict[str, Any]], optional): Additional details. Defaults to None.
            entity_type (Optional[str], optional): The entity type. Defaults to None.
            entity_id (Optional[str], optional): The entity ID. Defaults to None.
            user_id (Optional[int], optional): The user ID. Defaults to None.
            owner_id (Optional[int], optional): The owner ID. Defaults to None.
            trace_id (Optional[str], optional): The trace ID. Defaults to None.
            span_id (Optional[str], optional): The span ID. Defaults to None.
            parent_span_id (Optional[str], optional): The parent span ID. Defaults to None.
            timestamp (Optional[datetime], optional): The timestamp. Defaults to None.

        Returns:
            Optional[Dict[str, Any]]: The inserted log entry or None if insertion failed
        """
        try:
            # Use the add_log_entry function to insert the log
            query = """
                SELECT add_log_entry(
                    %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
                ) as log_id
            """

            # Convert details to JSON string if provided
            details_json = json.dumps(details) if details else None

            # Set owner_id to user_id if not provided
            if owner_id is None and self.user_id:
                owner_id = self.user_id

            # Set user_id to current user if not provided
            if user_id is None and self.user_id:
                user_id = self.user_id

            # Ensure all parameters are properly formatted
            # Convert any string parameters to proper format
            if isinstance(source, str):
                source = source.strip()

            if isinstance(category, str):
                category = category.strip()

            # Ensure params is a tuple
            params = (
                timestamp,
                category,
                source,
                level,
                message,
                details_json,
                entity_type,
                entity_id,
                user_id,
                owner_id,
                trace_id,
                span_id,
                parent_span_id
            )

            # Use execute_insert instead of execute_query_single to ensure the transaction is committed
            with self.get_connection(True) as conn:
                if not conn:
                    logger.error("No database connection available")
                    return None

                cursor = conn.cursor()
                try:
                    cursor.execute(query, params)

                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        result_row = cursor.fetchone()

                        if result_row:
                            result = dict(zip(columns, result_row))
                            conn.commit()
                        else:
                            result = None
                    else:
                        conn.commit()
                        result = None
                except Exception as e:
                    logger.error(f"Error executing add_log_entry: {e}")
                    conn.rollback()
                    return None
                finally:
                    cursor.close()

            if result and 'log_id' in result:
                log_id = result['log_id']
                # Get the full log entry with RLS bypassed
                return self.get_log_by_id(log_id, with_rls=False)

            return None
        except Exception as e:
            logger.error(f"Error adding log entry: {e}")
            return None

    def get_logs(self,
                 limit: int = 100,
                 offset: int = 0,
                 start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None,
                 levels: Optional[List[str]] = None,
                 categories: Optional[List[str]] = None,
                 sources: Optional[List[str]] = None,
                 entity_type: Optional[str] = None,
                 entity_id: Optional[str] = None,
                 user_id: Optional[int] = None,
                 trace_id: Optional[str] = None,
                 search_query: Optional[str] = None,
                 with_rls: bool = True) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get logs with filtering and pagination.

        Args:
            limit (int, optional): Maximum number of logs to return. Defaults to 100.
            offset (int, optional): Offset for pagination. Defaults to 0.
            start_time (Optional[datetime], optional): Filter logs after this time. Defaults to None.
            end_time (Optional[datetime], optional): Filter logs before this time. Defaults to None.
            levels (Optional[List[str]], optional): Filter by log levels. Defaults to None.
            categories (Optional[List[str]], optional): Filter by categories. Defaults to None.
            sources (Optional[List[str]], optional): Filter by sources. Defaults to None.
            entity_type (Optional[str], optional): Filter by entity type. Defaults to None.
            entity_id (Optional[str], optional): Filter by entity ID. Defaults to None.
            user_id (Optional[int], optional): Filter by user ID. Defaults to None.
            trace_id (Optional[str], optional): Filter by trace ID. Defaults to None.
            search_query (Optional[str], optional): Search in message text. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Tuple[List[Dict[str, Any]], int]: A tuple containing the list of logs and the total count
        """
        try:
            # Log RLS context information
            logger.info(f"Getting logs with RLS context: user_id={self.user_id}, user_role={self.user_role}, with_rls={with_rls}")

            # Build the query
            query_parts = [f"SELECT {self.default_columns}"]

            # Add FROM clause with joins for the main query
            from_clause = f"FROM {self.table_name} l {self.default_joins}"
            query_parts.append(from_clause)

            # Use a simpler count query
            count_query = "SELECT COUNT(*) as count FROM logs"

            # Initialize WHERE conditions and parameters
            conditions = []
            params = []

            # Add time range filters
            if start_time:
                conditions.append("l.timestamp >= %s")
                params.append(start_time)

            if end_time:
                conditions.append("l.timestamp <= %s")
                params.append(end_time)

            # Add level filter
            if levels and len(levels) > 0:
                placeholders = ", ".join(["%s"] * len(levels))
                conditions.append(f"ll.name IN ({placeholders})")
                params.extend(levels)

            # Add category filter
            if categories and len(categories) > 0:
                placeholders = ", ".join(["%s"] * len(categories))
                conditions.append(f"lc.name IN ({placeholders})")
                params.extend(categories)

            # Add source filter
            if sources and len(sources) > 0:
                placeholders = ", ".join(["%s"] * len(sources))
                conditions.append(f"ls.name IN ({placeholders})")
                params.extend(sources)

            # Add entity filters
            if entity_type:
                conditions.append("l.entity_type = %s")
                params.append(entity_type)

            if entity_id:
                conditions.append("l.entity_id = %s")
                params.append(entity_id)

            # Add user filter
            if user_id:
                conditions.append("l.user_id = %s")
                params.append(user_id)

            # Add trace filter
            if trace_id:
                conditions.append("l.trace_id = %s")
                params.append(trace_id)

            # Add search query
            if search_query:
                conditions.append("to_tsvector('english', l.message) @@ plainto_tsquery('english', %s)")
                params.append(search_query)

            # Add WHERE clause if there are conditions
            if conditions:
                where_clause = "WHERE " + " AND ".join(conditions)
                query_parts.append(where_clause)
                # Update count query with the same conditions
                count_query += " WHERE " + " AND ".join(conditions)

            # Add ORDER BY, LIMIT, and OFFSET
            query_parts.append(f"ORDER BY {self.default_order_by}")
            query_parts.append("LIMIT %s OFFSET %s")

            # Add limit and offset parameters
            params.append(limit)
            params.append(offset)

            # Build the final query
            query = " ".join(query_parts)

            # Log the queries
            logger.info(f"Logs query: {query}")
            logger.info(f"Logs count query: {count_query}")
            logger.info(f"Logs query params: {params}")

            # Execute the main query
            logs = self.execute_query(query, params, with_rls)

            # Execute the count query to get the total count
            count_result = self.execute_query_single(count_query, params[:-2], with_rls)
            total_count = count_result['count'] if count_result and 'count' in count_result else 0

            # Log the count for debugging
            logger.info(f"Count query returned total_count: {total_count}")

            # Log the results
            logger.info(f"Logs query returned {len(logs)} logs, total count: {total_count}")

            # Process the results
            for log in logs:
                # Convert details from JSON string to dict if it exists
                if log.get('details'):
                    try:
                        if isinstance(log['details'], str):
                            log['details'] = json.loads(log['details'])
                    except:
                        # If JSON parsing fails, keep as is
                        pass

            return logs, total_count
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            logger.exception("Exception details:")
            return [], 0

    def get_log_by_id(self, log_id: int, with_rls: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a log entry by ID.

        Args:
            log_id (int): The log ID
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: The log entry or None if not found
        """
        try:
            query = f"""
                SELECT {self.default_columns}
                FROM {self.table_name} l
                {self.default_joins}
                WHERE l.id = %s
            """

            log = self.execute_query_single(query, (log_id,), with_rls)

            if log and log.get('details'):
                try:
                    if isinstance(log['details'], str):
                        log['details'] = json.loads(log['details'])
                except:
                    # If JSON parsing fails, keep as is
                    pass

            return log
        except Exception as e:
            logger.error(f"Error getting log by ID: {e}")
            return None

    def get_log_categories(self) -> List[Dict[str, Any]]:
        """
        Get all log categories.

        Returns:
            List[Dict[str, Any]]: List of log categories
        """
        try:
            query = """
                SELECT id, name, description, created_at, updated_at
                FROM logs_categories
                ORDER BY name
            """

            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting log categories: {e}")
            return []

    def get_log_sources(self) -> List[Dict[str, Any]]:
        """
        Get all log sources.

        Returns:
            List[Dict[str, Any]]: List of log sources
        """
        try:
            query = """
                SELECT id, name, description, created_at, updated_at
                FROM logs_sources
                ORDER BY name
            """

            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting log sources: {e}")
            return []

    def get_log_levels(self) -> List[Dict[str, Any]]:
        """
        Get all log levels.

        Returns:
            List[Dict[str, Any]]: List of log levels
        """
        try:
            query = """
                SELECT id, name, severity, color, created_at, updated_at
                FROM logs_levels
                ORDER BY severity
            """

            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting log levels: {e}")
            return []

    def get_retention_policies(self) -> List[Dict[str, Any]]:
        """
        Get all log retention policies.

        Returns:
            List[Dict[str, Any]]: List of retention policies
        """
        try:
            query = """
                SELECT
                    rp.id,
                    rp.category_id,
                    lc.name as category_name,
                    rp.source_id,
                    ls.name as source_name,
                    rp.level_id,
                    ll.name as level_name,
                    rp.retention_days,
                    rp.created_at,
                    rp.updated_at
                FROM logs_retention_policies rp
                LEFT JOIN logs_categories lc ON rp.category_id = lc.id
                LEFT JOIN logs_sources ls ON rp.source_id = ls.id
                LEFT JOIN logs_levels ll ON rp.level_id = ll.id
                ORDER BY rp.retention_days DESC
            """

            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting retention policies: {e}")
            return []

    def get_logs_to_delete_count(self) -> List[Dict[str, Any]]:
        """
        Get count of logs that would be deleted based on retention policies.

        Returns:
            List[Dict[str, Any]]: Count of logs to delete by level
        """
        try:
            # Get retention policies
            policies = self.get_retention_policies()

            # Initialize result
            result = []

            # Process each policy
            for policy in policies:
                level_name = policy.get('level_name')
                retention_days = policy.get('retention_days')
                category_id = policy.get('category_id')
                source_id = policy.get('source_id')
                level_id = policy.get('level_id')

                # Skip if no level_id (shouldn't happen, but just in case)
                if not level_id:
                    continue

                # Build query to count logs that would be deleted
                query = """
                    SELECT COUNT(*) as count
                    FROM logs
                    WHERE timestamp < (CURRENT_TIMESTAMP - (%s || ' days')::INTERVAL)
                """
                params = [retention_days]

                # Add conditions based on policy
                if category_id:
                    query += " AND category_id = %s"
                    params.append(category_id)

                if source_id:
                    query += " AND source_id = %s"
                    params.append(source_id)

                query += " AND level_id = %s"
                params.append(level_id)

                # Execute query
                count_result = self.execute_query_single(query, params)

                if count_result and 'count' in count_result:
                    result.append({
                        "level": level_name,
                        "retention_days": retention_days,
                        "count": count_result['count']
                    })

            return result
        except Exception as e:
            logger.error(f"Error getting logs to delete count: {e}")
            return []

    def cleanup_old_logs(self) -> int:
        """
        Clean up old logs based on retention policies.

        Returns:
            int: Number of deleted log entries
        """
        try:
            query = "SELECT cleanup_old_logs() as deleted_count"
            result = self.execute_query_single(query)

            if result and 'deleted_count' in result:
                return result['deleted_count']

            return 0
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            return 0

    def get_log_statistics(self,
                          days: int = 7,
                          group_by: str = "day") -> List[Dict[str, Any]]:
        """
        Get log statistics for the specified time period.

        Args:
            days (int, optional): Number of days to include. Defaults to 7.
            group_by (str, optional): Grouping interval ('hour', 'day', 'week', 'month'). Defaults to "day".

        Returns:
            List[Dict[str, Any]]: Log statistics
        """
        try:
            # Determine the date trunc function based on group_by
            if group_by == 'hour':
                trunc_function = "date_trunc('hour', l.timestamp)"
            elif group_by == 'day':
                trunc_function = "date_trunc('day', l.timestamp)"
            elif group_by == 'week':
                trunc_function = "date_trunc('week', l.timestamp)"
            elif group_by == 'month':
                trunc_function = "date_trunc('month', l.timestamp)"
            else:
                trunc_function = "date_trunc('day', l.timestamp)"

            query = f"""
                SELECT
                    {trunc_function} as time_period,
                    ll.name as level,
                    COUNT(*) as count,
                    MAX(ll.severity) as severity
                FROM logs l
                JOIN logs_levels ll ON l.level_id = ll.id
                WHERE l.timestamp >= NOW() - INTERVAL '%s days'
                GROUP BY time_period, ll.name
                ORDER BY time_period, severity
            """

            return self.execute_query(query, (days,))
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return []
