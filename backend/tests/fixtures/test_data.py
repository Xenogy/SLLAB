"""
Test data fixtures for testing.
"""

import os
import json
import random
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

def get_test_users() -> List[Dict[str, Any]]:
    """
    Get test users.
    
    Returns:
        List[Dict[str, Any]]: A list of test users
    """
    return [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.now().timestamp()
        },
        {
            "id": 2,
            "username": "user1",
            "email": "user1@example.com",
            "role": "user",
            "is_active": True,
            "created_at": datetime.now().timestamp()
        },
        {
            "id": 3,
            "username": "user2",
            "email": "user2@example.com",
            "role": "user",
            "is_active": True,
            "created_at": datetime.now().timestamp()
        }
    ]

def get_test_accounts() -> List[Dict[str, Any]]:
    """
    Get test accounts.
    
    Returns:
        List[Dict[str, Any]]: A list of test accounts
    """
    return [
        {
            "acc_id": "76561199826722001",
            "acc_username": "admin_account1",
            "acc_password": "password123",
            "acc_email_address": "admin_account1@example.com",
            "acc_email_password": "email_password",
            "acc_created_at": datetime.now().timestamp(),
            "prime": True,
            "lock": False,
            "perm_lock": False,
            "owner_id": 1
        },
        {
            "acc_id": "76561199826722002",
            "acc_username": "user1_account1",
            "acc_password": "password123",
            "acc_email_address": "user1_account1@example.com",
            "acc_email_password": "email_password",
            "acc_created_at": datetime.now().timestamp(),
            "prime": False,
            "lock": False,
            "perm_lock": False,
            "owner_id": 2
        },
        {
            "acc_id": "76561199826722003",
            "acc_username": "user2_account1",
            "acc_password": "password123",
            "acc_email_address": "user2_account1@example.com",
            "acc_email_password": "email_password",
            "acc_created_at": datetime.now().timestamp(),
            "prime": True,
            "lock": True,
            "perm_lock": False,
            "owner_id": 3
        }
    ]

def get_test_hardware() -> List[Dict[str, Any]]:
    """
    Get test hardware.
    
    Returns:
        List[Dict[str, Any]]: A list of test hardware
    """
    return [
        {
            "id": 1,
            "acc_id": "76561199826722001",
            "hw_id": "hw_id_1",
            "hw_name": "Hardware 1",
            "hw_type": "Type 1",
            "hw_created_at": datetime.now().timestamp()
        },
        {
            "id": 2,
            "acc_id": "76561199826722002",
            "hw_id": "hw_id_2",
            "hw_name": "Hardware 2",
            "hw_type": "Type 2",
            "hw_created_at": datetime.now().timestamp()
        },
        {
            "id": 3,
            "acc_id": "76561199826722003",
            "hw_id": "hw_id_3",
            "hw_name": "Hardware 3",
            "hw_type": "Type 3",
            "hw_created_at": datetime.now().timestamp()
        }
    ]

def get_test_cards() -> List[Dict[str, Any]]:
    """
    Get test cards.
    
    Returns:
        List[Dict[str, Any]]: A list of test cards
    """
    return [
        {
            "id": 1,
            "acc_id": "76561199826722001",
            "card_id": "card_id_1",
            "card_name": "Card 1",
            "card_type": "Type 1",
            "card_created_at": datetime.now().timestamp(),
            "owner_id": 1
        },
        {
            "id": 2,
            "acc_id": "76561199826722002",
            "card_id": "card_id_2",
            "card_name": "Card 2",
            "card_type": "Type 2",
            "card_created_at": datetime.now().timestamp(),
            "owner_id": 2
        },
        {
            "id": 3,
            "acc_id": "76561199826722003",
            "card_id": "card_id_3",
            "card_name": "Card 3",
            "card_type": "Type 3",
            "card_created_at": datetime.now().timestamp(),
            "owner_id": 3
        }
    ]

def get_test_account_status() -> List[Dict[str, Any]]:
    """
    Get test account status.
    
    Returns:
        List[Dict[str, Any]]: A list of test account status
    """
    return [
        {
            "id": 1,
            "acc_id": "76561199826722001",
            "status": "active",
            "last_updated": datetime.now().timestamp()
        },
        {
            "id": 2,
            "acc_id": "76561199826722002",
            "status": "inactive",
            "last_updated": datetime.now().timestamp()
        },
        {
            "id": 3,
            "acc_id": "76561199826722003",
            "status": "suspended",
            "last_updated": datetime.now().timestamp()
        }
    ]

def get_test_user_credentials() -> List[Dict[str, Any]]:
    """
    Get test user credentials.
    
    Returns:
        List[Dict[str, Any]]: A list of test user credentials
    """
    return [
        {
            "username": "admin",
            "password": "admin_password"
        },
        {
            "username": "user1",
            "password": "user1_password"
        },
        {
            "username": "user2",
            "password": "user2_password"
        }
    ]

def get_test_account_list_params() -> Dict[str, Any]:
    """
    Get test account list parameters.
    
    Returns:
        Dict[str, Any]: Test account list parameters
    """
    return {
        "limit": 10,
        "offset": 0,
        "search": None,
        "sort_by": "acc_id",
        "sort_order": "asc",
        "filter_prime": None,
        "filter_lock": None,
        "filter_perm_lock": None
    }

def get_test_account_create_data() -> Dict[str, Any]:
    """
    Get test account create data.
    
    Returns:
        Dict[str, Any]: Test account create data
    """
    return {
        "acc_id": f"76561199{random_string(9, digits_only=True)}",
        "acc_username": f"test_account_{random_string(8)}",
        "acc_password": f"password_{random_string(8)}",
        "acc_email_address": f"test_account_{random_string(8)}@example.com",
        "acc_email_password": f"email_password_{random_string(8)}",
        "prime": False,
        "lock": False,
        "perm_lock": False
    }

def get_test_account_update_data() -> Dict[str, Any]:
    """
    Get test account update data.
    
    Returns:
        Dict[str, Any]: Test account update data
    """
    return {
        "acc_username": f"updated_account_{random_string(8)}",
        "acc_password": f"updated_password_{random_string(8)}",
        "acc_email_address": f"updated_account_{random_string(8)}@example.com",
        "acc_email_password": f"updated_email_password_{random_string(8)}",
        "prime": True,
        "lock": True,
        "perm_lock": False
    }

def random_string(length: int = 8, digits_only: bool = False) -> str:
    """
    Generate a random string.
    
    Args:
        length (int, optional): The length of the string. Defaults to 8.
        digits_only (bool, optional): Whether to use only digits. Defaults to False.
        
    Returns:
        str: A random string
    """
    if digits_only:
        return ''.join(random.choices(string.digits, k=length))
    else:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
