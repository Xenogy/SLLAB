"""
Base repository class for database access.

This module provides a base repository class that extends DatabaseAccess and provides
common methods for database operations on a specific entity.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from ..access import DatabaseAccess

# Configure logging
logger = logging.getLogger(__name__)

class BaseRepository(DatabaseAccess):
    """Base repository class for database access."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the BaseRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = ""
        self.id_column = "id"
        self.default_columns = "*"
        self.default_order_by = "id"

    def get_connection(self, with_rls: bool = True):
        """
        Get a database connection with or without RLS context.

        Args:
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            A database connection with or without RLS context.
        """
        return super().get_connection(with_rls)

    def get_by_id(self, id_value: Any, columns: str = None, with_rls: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get an entity by its ID.

        Args:
            id_value (Any): The ID value.
            columns (str, optional): The columns to select. Defaults to None (use default_columns).
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the entity or None if not found.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return None

        columns = columns or self.default_columns
        return super().get_by_id(self.table_name, self.id_column, id_value, columns, with_rls)

    def get_all(self, condition: str = "", params: Tuple = None, columns: str = None,
                order_by: str = None, limit: int = 0, offset: int = 0, with_rls: bool = True) -> List[Dict[str, Any]]:
        """
        Get all entities.

        Args:
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            columns (str, optional): The columns to select. Defaults to None (use default_columns).
            order_by (str, optional): The ORDER BY clause. Defaults to None (use default_order_by).
            limit (int, optional): The LIMIT clause. Defaults to 0 (no limit).
            offset (int, optional): The OFFSET clause. Defaults to 0.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the entities.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return []

        columns = columns or self.default_columns
        order_by = order_by or self.default_order_by
        return super().get_all(self.table_name, condition, params, columns, order_by, limit, offset, with_rls)

    def get_count(self, condition: str = "", params: Tuple = None, with_rls: bool = True) -> int:
        """
        Get the count of entities.

        Args:
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            int: The count of entities.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return 0

        return super().get_count(self.table_name, condition, params, with_rls)

    def create(self, data: Dict[str, Any], returning: bool = True, with_rls: bool = True) -> Optional[Dict[str, Any]]:
        """
        Create a new entity.

        Args:
            data (Dict[str, Any]): The data to insert.
            returning (bool, optional): Whether to return the inserted entity. Defaults to True.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the inserted entity or None if not returning.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return None

        # If owner_id is not set and user_id is available, set owner_id to user_id
        if "owner_id" not in data and self.user_id:
            data["owner_id"] = self.user_id

        return super().insert(self.table_name, data, returning, with_rls)

    def update(self, id_value: Any, data: Dict[str, Any], returning: bool = False, with_rls: bool = True) -> Union[int, Optional[Dict[str, Any]]]:
        """
        Update an entity.

        Args:
            id_value (Any): The ID value.
            data (Dict[str, Any]): The data to update.
            returning (bool, optional): Whether to return the updated entity. Defaults to False.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Union[int, Optional[Dict[str, Any]]]: The number of affected rows or a dictionary with the updated entity.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return 0 if not returning else None

        condition = f"{self.id_column} = %s"
        return super().update(self.table_name, data, condition, (id_value,), returning, with_rls)

    def delete(self, id_value: Any, with_rls: bool = True) -> int:
        """
        Delete an entity.

        Args:
            id_value (Any): The ID value.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            int: The number of affected rows.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return 0

        condition = f"{self.id_column} = %s"
        return super().delete(self.table_name, condition, (id_value,), with_rls)

    def exists(self, id_value: Any, with_rls: bool = True) -> bool:
        """
        Check if an entity exists.

        Args:
            id_value (Any): The ID value.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            bool: True if the entity exists, False otherwise.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return False

        query = f"SELECT 1 FROM {self.table_name} WHERE {self.id_column} = %s"
        result = self.execute_query_single(query, (id_value,), with_rls)
        return result is not None

    def get_paginated(self, page: int = 1, page_size: int = 10, condition: str = "", params: Tuple = None,
                      columns: str = None, order_by: str = None, with_rls: bool = True) -> Dict[str, Any]:
        """
        Get paginated entities.

        Args:
            page (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The page size. Defaults to 10.
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            columns (str, optional): The columns to select. Defaults to None (use default_columns).
            order_by (str, optional): The ORDER BY clause. Defaults to None (use default_order_by).
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Dict[str, Any]: A dictionary with the paginated entities and pagination info.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "pages": 0}

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total = self.get_count(condition, params, with_rls)

        # Calculate total pages
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        # Get items
        items = self.get_all(condition, params, columns, order_by, page_size, offset, with_rls)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }

    def get_with_search(self, search: str = "", search_columns: List[str] = None, condition: str = "",
                        params: Tuple = None, columns: str = None, order_by: str = None,
                        limit: int = 0, offset: int = 0, with_rls: bool = True) -> List[Dict[str, Any]]:
        """
        Get entities with search.

        Args:
            search (str, optional): The search term. Defaults to "".
            search_columns (List[str], optional): The columns to search in. Defaults to None.
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            columns (str, optional): The columns to select. Defaults to None (use default_columns).
            order_by (str, optional): The ORDER BY clause. Defaults to None (use default_order_by).
            limit (int, optional): The LIMIT clause. Defaults to 0 (no limit).
            offset (int, optional): The OFFSET clause. Defaults to 0.
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries with the entities.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return []

        if not search or not search_columns:
            return self.get_all(condition, params, columns, order_by, limit, offset, with_rls)

        # Build search condition
        search_condition = " OR ".join([f"{column} ILIKE %s" for column in search_columns])
        search_params = tuple([f"%{search}%"] * len(search_columns))

        # Combine with existing condition
        if condition:
            combined_condition = f"({condition}) AND ({search_condition})"
            combined_params = (params or ()) + search_params
        else:
            combined_condition = search_condition
            combined_params = search_params

        return self.get_all(combined_condition, combined_params, columns, order_by, limit, offset, with_rls)

    def get_paginated_with_search(self, search: str = "", search_columns: List[str] = None,
                                 page: int = 1, page_size: int = 10, condition: str = "",
                                 params: Tuple = None, columns: str = None, order_by: str = None,
                                 with_rls: bool = True) -> Dict[str, Any]:
        """
        Get paginated entities with search.

        Args:
            search (str, optional): The search term. Defaults to "".
            search_columns (List[str], optional): The columns to search in. Defaults to None.
            page (int, optional): The page number. Defaults to 1.
            page_size (int, optional): The page size. Defaults to 10.
            condition (str, optional): The WHERE condition. Defaults to "".
            params (Tuple, optional): The parameters for the condition. Defaults to None.
            columns (str, optional): The columns to select. Defaults to None (use default_columns).
            order_by (str, optional): The ORDER BY clause. Defaults to None (use default_order_by).
            with_rls (bool, optional): Whether to use RLS context. Defaults to True.

        Returns:
            Dict[str, Any]: A dictionary with the paginated entities and pagination info.
        """
        if not self.table_name:
            logger.error("Table name not set")
            return {"items": [], "total": 0, "page": page, "page_size": page_size, "pages": 0}

        if not search or not search_columns:
            return self.get_paginated(page, page_size, condition, params, columns, order_by, with_rls)

        # Build search condition
        search_condition = " OR ".join([f"{column} ILIKE %s" for column in search_columns])
        search_params = tuple([f"%{search}%"] * len(search_columns))

        # Combine with existing condition
        if condition:
            combined_condition = f"({condition}) AND ({search_condition})"
            combined_params = (params or ()) + search_params
        else:
            combined_condition = search_condition
            combined_params = search_params

        # Calculate offset
        offset = (page - 1) * page_size

        # Get total count
        total = self.get_count(combined_condition, combined_params, with_rls)

        # Calculate total pages
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        # Get items
        items = self.get_all(combined_condition, combined_params, columns, order_by, page_size, offset, with_rls)

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages
        }
