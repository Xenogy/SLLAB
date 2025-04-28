"""
Hardware repository for database access.

This module provides a repository class for accessing hardware data in the database.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from .base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class HardwareRepository(BaseRepository):
    """Repository for hardware data."""
    
    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the HardwareRepository instance.
        
        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "hardware"
        self.id_column = "id"
        self.default_columns = """
            id, name, type, specs, account_id, owner_id,
            created_at, updated_at
        """
        self.default_order_by = "id DESC"
        self.search_columns = ["name", "type", "specs"]
    
    def get_hardware(self, limit: int = 10, offset: int = 0, search: Optional[str] = None,
                    type: Optional[str] = None, account_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a list of hardware with pagination and filtering.
        
        Args:
            limit (int, optional): Maximum number of hardware items to return. Defaults to 10.
            offset (int, optional): Number of hardware items to skip. Defaults to 0.
            search (Optional[str], optional): Search term to filter hardware. Defaults to None.
            type (Optional[str], optional): Filter by type. Defaults to None.
            account_id (Optional[int], optional): Filter by account ID. Defaults to None.
            
        Returns:
            Dict[str, Any]: A dictionary with hardware items and pagination info.
        """
        # Build filter conditions
        condition = "1=1"
        params = []
        
        if type:
            condition += " AND type = %s"
            params.append(type)
        
        if account_id:
            condition += " AND account_id = %s"
            params.append(account_id)
        
        # Add search condition if provided
        if search:
            search_condition = " OR ".join([f"{column} ILIKE %s" for column in self.search_columns])
            condition += f" AND ({search_condition})"
            search_term = f"%{search}%"
            params.extend([search_term] * len(self.search_columns))
        
        # Get total count
        total = self.get_count(condition, tuple(params) if params else None)
        
        # Get hardware
        hardware = self.get_all(condition, tuple(params) if params else None, 
                               self.default_columns, self.default_order_by, limit, offset)
        
        return {
            "hardware": hardware,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    def get_hardware_by_id(self, hardware_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific hardware item by ID.
        
        Args:
            hardware_id (int): The ID of the hardware item.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the hardware item or None if not found.
        """
        return self.get_by_id(hardware_id)
    
    def create_hardware(self, hardware_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a new hardware item.
        
        Args:
            hardware_data (Dict[str, Any]): The hardware data.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created hardware item or None if creation failed.
        """
        return self.create(hardware_data)
    
    def update_hardware(self, hardware_id: int, hardware_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a hardware item.
        
        Args:
            hardware_id (int): The ID of the hardware item.
            hardware_data (Dict[str, Any]): The hardware data to update.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated hardware item or None if update failed.
        """
        return self.update(hardware_id, hardware_data, returning=True)
    
    def delete_hardware(self, hardware_id: int) -> bool:
        """
        Delete a hardware item.
        
        Args:
            hardware_id (int): The ID of the hardware item.
            
        Returns:
            bool: True if the hardware item was deleted, False otherwise.
        """
        return self.delete(hardware_id) > 0
    
    def get_hardware_by_account(self, account_id: int) -> List[Dict[str, Any]]:
        """
        Get all hardware items for a specific account.
        
        Args:
            account_id (int): The ID of the account.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries with hardware items.
        """
        condition = "account_id = %s"
        return self.get_all(condition, (account_id,), self.default_columns)
    
    def get_hardware_by_owner(self, owner_id: int) -> List[Dict[str, Any]]:
        """
        Get all hardware items for a specific owner.
        
        Args:
            owner_id (int): The ID of the owner.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries with hardware items.
        """
        condition = "owner_id = %s"
        return self.get_all(condition, (owner_id,), self.default_columns)
    
    def get_hardware_by_type(self, type: str) -> List[Dict[str, Any]]:
        """
        Get all hardware items of a specific type.
        
        Args:
            type (str): The type of hardware.
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries with hardware items.
        """
        condition = "type = %s"
        return self.get_all(condition, (type,), self.default_columns)
    
    def get_hardware_with_account(self, hardware_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a hardware item with its associated account.
        
        Args:
            hardware_id (int): The ID of the hardware item.
            
        Returns:
            Optional[Dict[str, Any]]: A dictionary with the hardware item and its account or None if not found.
        """
        query = """
            SELECT 
                h.id, h.name, h.type, h.specs, h.account_id, h.owner_id,
                h.created_at, h.updated_at,
                a.acc_id, a.acc_username, a.acc_email_address
            FROM hardware h
            LEFT JOIN accounts a ON h.account_id = a.id
            WHERE h.id = %s
        """
        result = self.execute_query(query, (hardware_id,))
        
        if not result:
            return None
        
        hardware = result[0]
        
        # Restructure the result to separate hardware and account
        account = {
            "id": hardware.pop("acc_id", None),
            "username": hardware.pop("acc_username", None),
            "email_address": hardware.pop("acc_email_address", None)
        }
        
        hardware["account"] = account
        
        return hardware
