"""
User repository for database access.

This module provides a repository class for accessing user data in the database.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from .base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    """Repository for user data."""
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the UserRepository instance.
        
        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "users"
        self.id_column = "id"
        self.default_columns = """
            id, username, email, is_admin, created_at, updated_at
        """
        self.default_order_by = "id"
        self.search_columns = ["username", "email"]
    
    def get_users(self, limit: int = 10, offset: int = 0, search: Optional[str] = None,
                 is_admin: Optional[bool] = None) -> Dict[str, Any]:
        """
        Get a list of users with pagination and filtering.
        
        Args:
            limit (int, optional): Maximum number of users to return. Defaults to 10.
            offset (int, optional): Number of users to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter users. Defaults to None.
            is_admin (Optional[bool], optional): Filter by admin status. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary with users and pagination info.
        """
        # Build filter conditions
        condition = "1=1"
        params = []
        
        if is_admin is not None:
            condition += " AND is_admin = %s"
            params.append(is_admin)
        
        # Add search condition if provided
        if search:
            search_condition = " OR ".join([f"{column} ILIKE %s" for column in self.search_columns])
            condition += f" AND ({search_condition})"
            search_term = f"%{search}%"
            params.extend([search_term] * len(self.search_columns))
        
        # Get total count
        total = self.get_count(condition, tuple(params) if params else None)
        
        # Get users
        users = self.get_all(condition, tuple(params) if params else None, 
                            self.default_columns, self.default_order_by, limit, offset)
        
        return {
            "users": users,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by ID.
        
        Args:
            user_id (int): The ID of the user.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the user or None if not found.
        """
        return self.get_by_id(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by username.
        
        Args:
            username (str): The username of the user.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the user or None if not found.
        """
        condition = "username = %s"
        users = self.get_all(condition, (username,), self.default_columns)
        return users[0] if users else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by email.
        
        Args:
            email (str): The email of the user.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the user or None if not found.
        """
        condition = "email = %s"
        users = self.get_all(condition, (email,), self.default_columns)
        return users[0] if users else None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new user.
        
        Args:
            user_data (Dict[str, Any]): The user data.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created user or None if creation failed.
        """
        # Check if username already exists
        if self.get_user_by_username(user_data.get("username")):
            logger.warning(f"Username already exists: {user_data.get('username')}")
            return None
        
        # Check if email already exists
        if "email" in user_data and user_data["email"] and self.get_user_by_email(user_data["email"]):
            logger.warning(f"Email already exists: {user_data.get('email')}")
            return None
        
        return self.create(user_data)
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a user.
        
        Args:
            user_id (int): The ID of the user.
            user_data (Dict[str, Any]): The user data to update.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated user or None if update failed.
        """
        # Check if username already exists
        if "username" in user_data:
            existing_user = self.get_user_by_username(user_data["username"])
            if existing_user and existing_user["id"] != user_id:
                logger.warning(f"Username already exists: {user_data.get('username')}")
                return None
        
        # Check if email already exists
        if "email" in user_data and user_data["email"]:
            existing_user = self.get_user_by_email(user_data["email"])
            if existing_user and existing_user["id"] != user_id:
                logger.warning(f"Email already exists: {user_data.get('email')}")
                return None
        
        return self.update(user_id, user_data, returning=True)
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id (int): The ID of the user.
            
        Returns:
            bool: True if the user was deleted, False otherwise.
        """
        return self.delete(user_id) > 0
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.
        
        Args:
            username (str): The username of the user.
            password (str): The password of the user.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the user or None if authentication failed.
        """
        query = """
            SELECT id, username, email, is_admin, created_at, updated_at
            FROM users
            WHERE username = %s AND password_hash = crypt(%s, password_hash)
        """
        result = self.execute_query(query, (username, password))
        return result[0] if result else None
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        
        Args:
            user_id (int): The ID of the user.
            current_password (str): The current password.
            new_password (str): The new password.
            
        Returns:
            bool: True if the password was changed, False otherwise.
        """
        # Verify current password
        verify_query = """
            SELECT 1 FROM users
            WHERE id = %s AND password_hash = crypt(%s, password_hash)
        """
        verify_result = self.execute_query(verify_query, (user_id, current_password))
        
        if not verify_result:
            return False
        
        # Update password
        update_query = """
            UPDATE users
            SET password_hash = crypt(%s, gen_salt('bf'))
            WHERE id = %s
        """
        result = self.execute_command(update_query, (new_password, user_id))
        return result > 0
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """
        Reset a user's password.
        
        Args:
            user_id (int): The ID of the user.
            new_password (str): The new password.
            
        Returns:
            bool: True if the password was reset, False otherwise.
        """
        update_query = """
            UPDATE users
            SET password_hash = crypt(%s, gen_salt('bf'))
            WHERE id = %s
        """
        result = self.execute_command(update_query, (new_password, user_id))
        return result > 0
