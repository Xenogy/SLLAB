"""
Utility functions for testing.
"""

import os
import json
import random
import string
import psycopg2
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from psycopg2.extensions import connection as PsycopgConnection

from config import Config

def create_test_user(
    db_connection: PsycopgConnection,
    username: Optional[str] = None,
    email: Optional[str] = None,
    role: str = "user",
    is_active: bool = True
) -> Dict[str, Any]:
    """
    Create a test user in the database.
    
    Args:
        db_connection (PsycopgConnection): A database connection
        username (Optional[str], optional): The username. Defaults to None.
        email (Optional[str], optional): The email. Defaults to None.
        role (str, optional): The role. Defaults to "user".
        is_active (bool, optional): Whether the user is active. Defaults to True.
        
    Returns:
        Dict[str, Any]: The created user
    """
    # Generate random values if not provided
    if username is None:
        username = f"test_user_{random_string(8)}"
    if email is None:
        email = f"{username}@example.com"
    
    # Hash the password
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    password_hash = pwd_context.hash("password123")
    
    # Create the user
    cursor = db_connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, username, email, role, is_active, created_at
            """,
            (username, email, password_hash, role, is_active, datetime.now().timestamp())
        )
        
        # Get the created user
        user_data = cursor.fetchone()
        
        # Create a user dictionary
        user = {
            "id": user_data[0],
            "username": user_data[1],
            "email": user_data[2],
            "role": user_data[3],
            "is_active": user_data[4],
            "created_at": user_data[5]
        }
        
        return user
    finally:
        cursor.close()

def create_test_account(
    db_connection: PsycopgConnection,
    owner_id: int,
    acc_id: Optional[str] = None,
    acc_username: Optional[str] = None,
    prime: bool = False,
    lock: bool = False,
    perm_lock: bool = False
) -> Dict[str, Any]:
    """
    Create a test account in the database.
    
    Args:
        db_connection (PsycopgConnection): A database connection
        owner_id (int): The owner ID
        acc_id (Optional[str], optional): The account ID. Defaults to None.
        acc_username (Optional[str], optional): The account username. Defaults to None.
        prime (bool, optional): Whether the account has prime. Defaults to False.
        lock (bool, optional): Whether the account is locked. Defaults to False.
        perm_lock (bool, optional): Whether the account is permanently locked. Defaults to False.
        
    Returns:
        Dict[str, Any]: The created account
    """
    # Generate random values if not provided
    if acc_id is None:
        acc_id = f"76561199{random_string(9, digits_only=True)}"
    if acc_username is None:
        acc_username = f"test_account_{random_string(8)}"
    
    # Create the account
    cursor = db_connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO accounts (
                acc_id, acc_username, acc_password, acc_email_address, acc_email_password,
                acc_created_at, prime, lock, perm_lock, owner_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING acc_id, acc_username, acc_password, acc_email_address, acc_email_password,
                acc_created_at, prime, lock, perm_lock, owner_id
            """,
            (
                acc_id, acc_username, f"password_{random_string(8)}",
                f"{acc_username}@example.com", f"email_password_{random_string(8)}",
                datetime.now().timestamp(), prime, lock, perm_lock, owner_id
            )
        )
        
        # Get the created account
        account_data = cursor.fetchone()
        
        # Create an account dictionary
        account = {
            "acc_id": account_data[0],
            "acc_username": account_data[1],
            "acc_password": account_data[2],
            "acc_email_address": account_data[3],
            "acc_email_password": account_data[4],
            "acc_created_at": account_data[5],
            "prime": account_data[6],
            "lock": account_data[7],
            "perm_lock": account_data[8],
            "owner_id": account_data[9]
        }
        
        return account
    finally:
        cursor.close()

def create_test_token(
    user_id: int,
    username: str,
    role: str = "user",
    expires_in: int = 30
) -> str:
    """
    Create a test JWT token.
    
    Args:
        user_id (int): The user ID
        username (str): The username
        role (str, optional): The role. Defaults to "user".
        expires_in (int, optional): The expiration time in minutes. Defaults to 30.
        
    Returns:
        str: The JWT token
    """
    from jose import jwt
    
    # Create a token that expires in the specified time
    expires = datetime.now() + timedelta(minutes=expires_in)
    
    # Create the token payload
    payload = {
        "sub": username,
        "user_id": user_id,
        "user_role": role,
        "exp": expires.timestamp()
    }
    
    # Create the token
    token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)
    
    return token

def clean_test_data(db_connection: PsycopgConnection) -> None:
    """
    Clean test data from the database.
    
    Args:
        db_connection (PsycopgConnection): A database connection
    """
    cursor = db_connection.cursor()
    try:
        # Delete test accounts
        cursor.execute("DELETE FROM accounts WHERE acc_username LIKE 'test_account_%'")
        
        # Delete test users
        cursor.execute("DELETE FROM users WHERE username LIKE 'test_user_%' OR username LIKE 'test_admin_%'")
    finally:
        cursor.close()

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

def get_auth_headers(token: str) -> Dict[str, str]:
    """
    Get authentication headers.
    
    Args:
        token (str): The JWT token
        
    Returns:
        Dict[str, str]: The authentication headers
    """
    return {"Authorization": f"Bearer {token}"}

def compare_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any], keys: List[str]) -> bool:
    """
    Compare two dictionaries based on specific keys.
    
    Args:
        dict1 (Dict[str, Any]): The first dictionary
        dict2 (Dict[str, Any]): The second dictionary
        keys (List[str]): The keys to compare
        
    Returns:
        bool: Whether the dictionaries match
    """
    for key in keys:
        if key not in dict1 or key not in dict2 or dict1[key] != dict2[key]:
            return False
    return True
