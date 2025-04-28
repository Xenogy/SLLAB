"""
Cryptography utility functions for the AccountDB application.

This module provides utility functions for cryptography operations.
"""

import os
import base64
import hashlib
import hmac
import secrets
import string
import time
import jwt
from typing import Optional, Dict, Any, Tuple, Union

from config import Config

def generate_random_string(length: int = 32, include_special: bool = False) -> str:
    """
    Generate a random string of the specified length.

    Args:
        length: The length of the string to generate
        include_special: Whether to include special characters

    Returns:
        str: The random string
    """
    if length <= 0:
        return ""

    # Define the character set
    chars = string.ascii_letters + string.digits
    if include_special:
        chars += string.punctuation

    # Generate the random string
    return ''.join(secrets.choice(chars) for _ in range(length))

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2.

    Args:
        password: The password to hash
        salt: The salt to use, or None to generate a new salt

    Returns:
        Tuple[str, str]: The hashed password and the salt
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    # Generate a salt if not provided
    if salt is None:
        salt = secrets.token_hex(16)

    # Hash the password
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,
        dklen=32
    )

    # Return the hashed password and salt
    return base64.b64encode(key).decode('utf-8'), salt

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        password: The password to verify
        hashed_password: The hashed password to verify against
        salt: The salt used to hash the password

    Returns:
        bool: True if the password is correct, False otherwise
    """
    if not isinstance(password, str) or not isinstance(hashed_password, str) or not isinstance(salt, str):
        return False

    # Hash the password with the provided salt
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000,
        dklen=32
    )

    # Compare the hashed passwords
    return base64.b64encode(key).decode('utf-8') == hashed_password

def encrypt_data(data: str, key: Optional[str] = None) -> Optional[str]:
    """
    Encrypt data using a key.

    Args:
        data: The data to encrypt
        key: The key to use for encryption, or None to use the default key

    Returns:
        Optional[str]: The encrypted data, or None if encryption fails
    """
    # This is a placeholder for a proper encryption function
    # In a real application, you would use a library like cryptography
    try:
        if key is None:
            key = getattr(Config, 'ENCRYPTION_KEY', 'default_key')

        # Simple XOR encryption (NOT SECURE, FOR DEMONSTRATION ONLY)
        key_bytes = key.encode('utf-8')
        data_bytes = data.encode('utf-8')
        key_len = len(key_bytes)

        encrypted = bytearray()
        for i, b in enumerate(data_bytes):
            encrypted.append(b ^ key_bytes[i % key_len])

        return base64.b64encode(encrypted).decode('utf-8')
    except Exception:
        return None

def decrypt_data(encrypted_data: str, key: Optional[str] = None) -> Optional[str]:
    """
    Decrypt data using a key.

    Args:
        encrypted_data: The data to decrypt
        key: The key to use for decryption, or None to use the default key

    Returns:
        Optional[str]: The decrypted data, or None if decryption fails
    """
    # This is a placeholder for a proper decryption function
    # In a real application, you would use a library like cryptography
    try:
        if key is None:
            key = getattr(Config, 'ENCRYPTION_KEY', 'default_key')

        # Simple XOR decryption (NOT SECURE, FOR DEMONSTRATION ONLY)
        key_bytes = key.encode('utf-8')
        data_bytes = base64.b64decode(encrypted_data)
        key_len = len(key_bytes)

        decrypted = bytearray()
        for i, b in enumerate(data_bytes):
            decrypted.append(b ^ key_bytes[i % key_len])

        return decrypted.decode('utf-8')
    except Exception:
        return None

def generate_token(payload: Dict[str, Any], expiration: int = 3600, secret: Optional[str] = None) -> Optional[str]:
    """
    Generate a JWT token.

    Args:
        payload: The payload to include in the token
        expiration: The expiration time in seconds
        secret: The secret to use for signing, or None to use the default secret

    Returns:
        Optional[str]: The JWT token, or None if token generation fails
    """
    try:
        if secret is None:
            secret = getattr(Config, 'JWT_SECRET', 'default_secret')

        # Add expiration time to the payload
        payload['exp'] = int(time.time()) + expiration

        # Generate the token
        return jwt.encode(payload, secret, algorithm='HS256')
    except Exception:
        return None

def verify_token(token: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token.

    Args:
        token: The token to verify
        secret: The secret to use for verification, or None to use the default secret

    Returns:
        Optional[Dict[str, Any]]: The token payload if verification succeeds, or None if verification fails
    """
    try:
        if secret is None:
            secret = getattr(Config, 'JWT_SECRET', 'default_secret')

        # Verify the token
        return jwt.decode(token, secret, algorithms=['HS256'])
    except jwt.PyJWTError:
        return None
