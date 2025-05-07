"""
Settings repository module.

This module provides database operations for user settings and API keys.
"""
import logging
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from db import get_user_db_connection

# Configure logging
logger = logging.getLogger(__name__)

class SettingsRepository:
    """Repository for user settings and API keys."""

    def __init__(self, user_id: int, user_role: str):
        """
        Initialize the settings repository.

        Args:
            user_id: The ID of the current user
            user_role: The role of the current user
        """
        self.user_id = user_id
        self.user_role = user_role

    def get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a user's settings.

        Args:
            user_id: The ID of the user

        Returns:
            The user's settings or None if not found
        """
        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT * FROM user_settings
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None

    def create_user_settings(self, user_id: int) -> Dict[str, Any]:
        """
        Create default settings for a user.

        Args:
            user_id: The ID of the user

        Returns:
            The created user settings
        """
        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO user_settings (
                        user_id, theme, language, timezone, date_format, time_format,
                        notifications_enabled, email_notifications, auto_refresh_interval, items_per_page
                    )
                    VALUES (
                        %s, 'light', 'en', 'UTC', 'YYYY-MM-DD', '24h',
                        TRUE, TRUE, 60, 10
                    )
                    RETURNING *
                    """,
                    (user_id,)
                )
                conn.commit()
                result = cursor.fetchone()
                return dict(result)

    def update_user_settings(self, user_id: int, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a user's settings.

        Args:
            user_id: The ID of the user
            settings: The settings to update

        Returns:
            The updated user settings
        """
        # Check if settings exist, create if not
        existing_settings = self.get_user_settings(user_id)
        if not existing_settings:
            return self.create_user_settings(user_id)

        # Build the SQL query dynamically based on the provided settings
        query_parts = []
        query_values = []

        for key, value in settings.items():
            if value is not None and key in [
                "theme", "language", "timezone", "date_format", "time_format",
                "notifications_enabled", "email_notifications", "auto_refresh_interval", "items_per_page"
            ]:
                query_parts.append(sql.Identifier(key))
                query_values.append(value)

        if not query_parts:
            # No valid settings to update
            return existing_settings

        # Add updated_at to the query
        query_parts.append(sql.Identifier("updated_at"))
        query_values.append(datetime.now())

        # Add user_id to the values
        query_values.append(user_id)

        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build the SET part of the query
                set_clause = sql.SQL(", ").join(
                    sql.SQL("{} = %s").format(part) for part in query_parts
                )

                # Build the complete query
                query = sql.SQL("""
                    UPDATE user_settings
                    SET {}
                    WHERE user_id = %s
                    RETURNING *
                """).format(set_clause)

                cursor.execute(query, query_values)
                conn.commit()
                result = cursor.fetchone()
                return dict(result)

    def list_api_keys(
        self, user_id: int, limit: int = 10, offset: int = 0, include_revoked: bool = False,
        key_type: Optional[str] = None, resource_id: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List a user's API keys.

        Args:
            user_id: The ID of the user
            limit: Maximum number of keys to return
            offset: Offset for pagination
            include_revoked: Whether to include revoked keys
            key_type: Filter by key type (user, proxmox_node, windows_vm)
            resource_id: Filter by resource ID

        Returns:
            A tuple of (list of API keys, total count)
        """
        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build the WHERE clause based on parameters
                where_clause = "user_id = %s"
                where_values = [user_id]

                if not include_revoked:
                    where_clause += " AND revoked = FALSE"

                if key_type:
                    where_clause += " AND key_type = %s"
                    where_values.append(key_type)

                if resource_id is not None:
                    where_clause += " AND resource_id = %s"
                    where_values.append(resource_id)

                # Get the total count
                cursor.execute(
                    f"SELECT COUNT(*) FROM api_keys WHERE {where_clause}",
                    where_values
                )
                total = cursor.fetchone()["count"]

                # Get the API keys
                cursor.execute(
                    f"""
                    SELECT
                        id, user_id, key_name, api_key_prefix, scopes,
                        expires_at, last_used_at, created_at, revoked,
                        key_type, resource_id
                    FROM api_keys
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """,
                    where_values + [limit, offset]
                )
                results = cursor.fetchall()
                return [dict(row) for row in results], total

    def get_api_key(self, key_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an API key by ID.

        Args:
            key_id: The ID of the API key

        Returns:
            The API key or None if not found
        """
        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, user_id, key_name, api_key_prefix, scopes,
                        expires_at, last_used_at, created_at, revoked,
                        key_type, resource_id
                    FROM api_keys
                    WHERE id = %s
                    """,
                    (key_id,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None

    def create_api_key(
        self, user_id: int, key_name: str, api_key: str,
        scopes: List[str] = None, expires_at: Optional[datetime] = None,
        key_type: str = 'user', resource_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new API key.

        Args:
            user_id: The ID of the user
            key_name: Name/description of the API key
            api_key: The generated API key
            scopes: Permission scopes for the API key
            expires_at: Expiration timestamp
            key_type: Type of API key (user, proxmox_node, windows_vm)
            resource_id: ID of the associated resource (proxmox node ID or VM ID)

        Returns:
            The created API key
        """
        if scopes is None:
            scopes = []

        # Hash the API key for storage
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store the first 8 characters for display
        api_key_prefix = api_key[:8]

        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO api_keys (
                        user_id, key_name, api_key, api_key_prefix, scopes, expires_at, key_type, resource_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, key_name, api_key_prefix, scopes, expires_at, last_used_at, created_at, revoked, key_type, resource_id
                    """,
                    (user_id, key_name, api_key_hash, api_key_prefix, scopes, expires_at, key_type, resource_id)
                )
                conn.commit()
                result = cursor.fetchone()
                return dict(result)

    def revoke_api_key(self, key_id: int) -> Dict[str, Any]:
        """
        Revoke an API key.

        Args:
            key_id: The ID of the API key

        Returns:
            The revoked API key
        """
        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET revoked = TRUE
                    WHERE id = %s
                    RETURNING id, user_id, key_name, api_key_prefix, scopes, expires_at, last_used_at, created_at, revoked
                    """,
                    (key_id,)
                )
                conn.commit()
                result = cursor.fetchone()
                return dict(result)

    def validate_api_key(self, api_key: str, key_type: Optional[str] = None, resource_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and update last_used_at if valid.

        Args:
            api_key: The API key to validate
            key_type: Type of API key to validate (user, proxmox_node, windows_vm)
            resource_id: ID of the associated resource (proxmox node ID or VM ID)

        Returns:
            The API key information if valid, None otherwise
        """
        # Hash the API key for comparison
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Build the WHERE clause based on parameters
                where_clause = "api_key = %s AND revoked = FALSE"
                where_values = [api_key_hash]

                if key_type:
                    where_clause += " AND key_type = %s"
                    where_values.append(key_type)

                if resource_id is not None:
                    where_clause += " AND resource_id = %s"
                    where_values.append(resource_id)

                cursor.execute(
                    f"""
                    SELECT
                        id, user_id, key_name, api_key_prefix, scopes,
                        expires_at, last_used_at, created_at, revoked,
                        key_type, resource_id
                    FROM api_keys
                    WHERE {where_clause}
                    """,
                    where_values
                )
                result = cursor.fetchone()

                if not result:
                    return None

                # Check if the key has expired
                if result["expires_at"] and result["expires_at"] < datetime.now():
                    return None

                # Update last_used_at
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET last_used_at = NOW()
                    WHERE id = %s
                    """,
                    (result["id"],)
                )
                conn.commit()

                return dict(result)

    def get_api_key_by_resource(self, key_type: str, resource_id: int) -> Optional[Dict[str, Any]]:
        """
        Get an API key by resource type and ID.

        Args:
            key_type: Type of API key (proxmox_node, windows_vm)
            resource_id: ID of the associated resource

        Returns:
            The API key or None if not found
        """
        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        id, user_id, key_name, api_key_prefix, scopes,
                        expires_at, last_used_at, created_at, revoked,
                        key_type, resource_id
                    FROM api_keys
                    WHERE key_type = %s AND resource_id = %s AND revoked = FALSE
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (key_type, resource_id)
                )
                result = cursor.fetchone()
                return dict(result) if result else None

    def regenerate_api_key_for_resource(self, key_type: str, resource_id: int, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Regenerate an API key for a resource.

        Args:
            key_type: Type of API key (proxmox_node, windows_vm)
            resource_id: ID of the associated resource
            api_key: The new API key

        Returns:
            The updated API key or None if not found
        """
        # Hash the API key for storage
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store the first 8 characters for display
        api_key_prefix = api_key[:8]

        with get_user_db_connection(user_id=self.user_id, user_role=self.user_role) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # First, revoke any existing API keys for this resource
                cursor.execute(
                    """
                    UPDATE api_keys
                    SET revoked = TRUE
                    WHERE key_type = %s AND resource_id = %s AND revoked = FALSE
                    """,
                    (key_type, resource_id)
                )

                # Get the resource owner
                if key_type == 'proxmox_node':
                    cursor.execute(
                        """
                        SELECT owner_id FROM proxmox_nodes WHERE id = %s
                        """,
                        (resource_id,)
                    )
                elif key_type == 'windows_vm':
                    cursor.execute(
                        """
                        SELECT owner_id FROM vms WHERE id = %s
                        """,
                        (resource_id,)
                    )
                else:
                    return None

                owner_result = cursor.fetchone()
                if not owner_result:
                    return None

                owner_id = owner_result['owner_id']

                # Create a new API key
                cursor.execute(
                    """
                    INSERT INTO api_keys (
                        user_id, key_name, api_key, api_key_prefix, scopes,
                        key_type, resource_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, key_name, api_key_prefix, scopes,
                        expires_at, last_used_at, created_at, revoked,
                        key_type, resource_id
                    """,
                    (
                        owner_id,
                        f"{key_type.replace('_', ' ').title()} {resource_id}",
                        api_key_hash,
                        api_key_prefix,
                        ['read', 'write'],
                        key_type,
                        resource_id
                    )
                )
                conn.commit()
                result = cursor.fetchone()
                return dict(result)