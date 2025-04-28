"""
Account repository for database access.

This module provides a repository class for accessing account data in the database.
"""

import logging
import time
from typing import Optional, Dict, Any, List, Tuple, Union
from .base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class AccountRepository(BaseRepository):
    """Repository for account data."""
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the AccountRepository instance.
        
        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "accounts"
        self.id_column = "acc_id"
        self.default_columns = """
            acc_id, acc_username, acc_email_address, prime, lock, perm_lock, acc_created_at
        """
        self.default_order_by = "acc_id"
        self.search_columns = ["acc_id", "acc_username", "acc_email_address"]
    
    def get_accounts(self, limit: int = 100, offset: int = 0, search: Optional[str] = None,
                    sort_by: str = "acc_id", sort_order: str = "asc",
                    filter_prime: Optional[bool] = None, filter_lock: Optional[bool] = None,
                    filter_perm_lock: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get a list of accounts with pagination, sorting, and filtering.
        
        Args:
            limit (int, optional): Maximum number of accounts to return. Defaults to 100.
            offset (int, optional): Number of accounts to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter accounts. Defaults to None.
            sort_by (str, optional): Field to sort by. Defaults to "acc_id".
            sort_order (str, optional): Sort order (asc or desc). Defaults to "asc".
            filter_prime (Optional[bool], optional): Filter by prime status. Defaults to None.
            filter_lock (Optional[bool], optional): Filter by lock status. Defaults to None.
            filter_perm_lock (Optional[bool], optional): Filter by permanent lock status. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary with accounts and pagination info.
        """
        # Validate sort_by field
        valid_sort_fields = [
            "acc_id", "acc_username", "acc_email_address",
            "prime", "lock", "perm_lock", "acc_created_at"
        ]
        
        if sort_by not in valid_sort_fields:
            sort_by = "acc_id"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "asc"
        
        # Build filter conditions
        condition = "1=1"
        params = []
        
        if filter_prime is not None:
            condition += " AND prime = %s"
            params.append(filter_prime)
        
        if filter_lock is not None:
            condition += " AND lock = %s"
            params.append(filter_lock)
        
        if filter_perm_lock is not None:
            condition += " AND perm_lock = %s"
            params.append(filter_perm_lock)
        
        # Add search condition if provided
        if search:
            search_condition = " OR ".join([f"{column} ILIKE %s" for column in self.search_columns])
            condition += f" AND ({search_condition})"
            search_term = f"%{search}%"
            params.extend([search_term] * len(self.search_columns))
        
        # Get total count
        total = self.get_count(condition, tuple(params) if params else None)
        
        # Get accounts
        order_by = f"{sort_by} {sort_order}"
        accounts = self.get_all(condition, tuple(params) if params else None, 
                               self.default_columns, order_by, limit, offset)
        
        return {
            "accounts": accounts,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_account_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get an account by its username.
        
        Args:
            username (str): The username of the account.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the account or None if not found.
        """
        condition = "acc_username = %s"
        accounts = self.get_all(condition, (username,), self.default_columns)
        return accounts[0] if accounts else None
    
    def get_account_by_id(self, acc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an account by its ID.
        
        Args:
            acc_id (str): The ID of the account.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the account or None if not found.
        """
        return self.get_by_id(acc_id)
    
    def create_account(self, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new account.
        
        Args:
            account_data (Dict[str, Any]): The account data.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created account or None if creation failed.
        """
        # Set created_at if not provided
        if "acc_created_at" not in account_data or not account_data["acc_created_at"]:
            account_data["acc_created_at"] = time.time()
        
        # Set owner_id if not provided
        if "owner_id" not in account_data and self.user_id:
            account_data["owner_id"] = self.user_id
        
        return self.create(account_data)
    
    def update_account(self, acc_id: str, account_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an account.
        
        Args:
            acc_id (str): The ID of the account.
            account_data (Dict[str, Any]): The account data to update.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated account or None if update failed.
        """
        return self.update(acc_id, account_data, returning=True)
    
    def delete_account(self, acc_id: str) -> bool:
        """
        Delete an account.
        
        Args:
            acc_id (str): The ID of the account.
            
        Returns:
            bool: True if the account was deleted, False otherwise.
        """
        return self.delete(acc_id) > 0
    
    def get_account_info(self, acc_id: str, fields: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get specific account information by field names.
        
        Args:
            acc_id (str): The ID of the account.
            fields (List[str]): The fields to retrieve.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the requested fields or None if not found.
        """
        # Validate fields
        valid_fields = [
            "acc_id", "acc_username", "acc_password", "acc_email_address",
            "acc_email_password", "acc_vault_address", "acc_vault_password",
            "acc_created_at", "acc_session_start", "acc_steamguard_account_name",
            "acc_confirm_type", "acc_device_id", "acc_identity_secret",
            "acc_revocation_code", "acc_secret_1", "acc_serial_number",
            "acc_server_time", "acc_shared_secret", "acc_status",
            "acc_token_gid", "acc_uri", "id", "prime", "lock", "perm_lock",
            "farmlabs_upload"
        ]
        
        # Filter out invalid fields
        valid_field_list = [field for field in fields if field in valid_fields]
        
        if not valid_field_list:
            return None
        
        # Build and execute the query
        columns = ", ".join(valid_field_list)
        return self.get_by_id(acc_id, columns)
    
    def get_accounts_with_cursor(self, cursor_value: Optional[Any] = None, cursor_column: str = "acc_id",
                               sort_order: str = "asc", limit: int = 100, filter_conditions: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get accounts using cursor-based pagination.
        
        Args:
            cursor_value (Optional[Any], optional): The cursor value. Defaults to None.
            cursor_column (str, optional): The cursor column. Defaults to "acc_id".
            sort_order (str, optional): Sort order (asc or desc). Defaults to "asc".
            limit (int, optional): Maximum number of accounts to return. Defaults to 100.
            filter_conditions (Dict[str, Any], optional): Filter conditions. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary with accounts and pagination info.
        """
        # Validate cursor_column
        valid_cursor_columns = [
            "acc_id", "acc_username", "acc_email_address",
            "prime", "lock", "perm_lock", "acc_created_at"
        ]
        
        if cursor_column not in valid_cursor_columns:
            cursor_column = "acc_id"
        
        # Validate sort_order
        if sort_order.lower() not in ["asc", "desc"]:
            sort_order = "asc"
        
        # Build filter conditions
        condition = "1=1"
        params = []
        
        if filter_conditions:
            for key, value in filter_conditions.items():
                condition += f" AND {key} = %s"
                params.append(value)
        
        # Add cursor condition if provided
        if cursor_value is not None:
            operator = ">" if sort_order.lower() == "asc" else "<"
            condition += f" AND {cursor_column} {operator} %s"
            params.append(cursor_value)
        
        # Get accounts
        order_by = f"{cursor_column} {sort_order}"
        accounts = self.get_all(condition, tuple(params) if params else None, 
                               self.default_columns, order_by, limit + 1)  # Request one more to check if there are more pages
        
        # Check if there are more pages
        has_more = len(accounts) > limit
        
        # Limit accounts to requested limit
        accounts = accounts[:limit]
        
        # Get total count
        total_condition = "1=1"
        total_params = []
        
        if filter_conditions:
            for key, value in filter_conditions.items():
                total_condition += f" AND {key} = %s"
                total_params.append(value)
        
        total = self.get_count(total_condition, tuple(total_params) if total_params else None)
        
        return {
            "accounts": accounts,
            "total": total,
            "limit": limit,
            "has_more": has_more
        }
