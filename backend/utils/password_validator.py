"""
Password validation module.

This module provides functions for validating password strength and generating password strength feedback.
"""

import re
import logging
from typing import Dict, Any, List, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Password strength requirements
MIN_LENGTH = 8
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_NUMBERS = True
REQUIRE_SPECIAL_CHARS = True

def validate_password_strength(password: str) -> Tuple[bool, int, List[str]]:
    """
    Validate password strength.
    
    Args:
        password (str): The password to validate
        
    Returns:
        Tuple[bool, int, List[str]]: A tuple containing:
            - bool: Whether the password is strong enough
            - int: The password strength score (0-5)
            - List[str]: A list of feedback messages
    """
    if not password:
        return False, 0, ["Password cannot be empty"]
    
    score = 0
    feedback = []
    
    # Check length
    if len(password) < MIN_LENGTH:
        feedback.append(f"Password must be at least {MIN_LENGTH} characters long")
    else:
        score += 1
    
    # Check for uppercase letters
    if REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
        feedback.append("Password must contain at least one uppercase letter")
    else:
        score += 1
    
    # Check for lowercase letters
    if REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
        feedback.append("Password must contain at least one lowercase letter")
    else:
        score += 1
    
    # Check for numbers
    if REQUIRE_NUMBERS and not re.search(r'[0-9]', password):
        feedback.append("Password must contain at least one number")
    else:
        score += 1
    
    # Check for special characters
    if REQUIRE_SPECIAL_CHARS and not re.search(r'[^A-Za-z0-9]', password):
        feedback.append("Password must contain at least one special character")
    else:
        score += 1
    
    # Check for common patterns
    if re.search(r'(.)\1{2,}', password):  # Repeated characters
        feedback.append("Password contains repeated characters")
        score -= 1
    
    if re.search(r'(123|234|345|456|567|678|789|987|876|765|654|543|432|321)', password):  # Sequential numbers
        feedback.append("Password contains sequential numbers")
        score -= 1
    
    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password, re.IGNORECASE):  # Sequential letters
        feedback.append("Password contains sequential letters")
        score -= 1
    
    # Ensure score is between 0 and 5
    score = max(0, min(5, score))
    
    # Determine if password is strong enough
    is_strong = score >= 3 and len(feedback) <= 2
    
    # Add positive feedback if password is strong
    if is_strong and not feedback:
        feedback.append("Password is strong")
    
    return is_strong, score, feedback

def get_password_strength_feedback(password: str) -> Dict[str, Any]:
    """
    Get password strength feedback.
    
    Args:
        password (str): The password to validate
        
    Returns:
        Dict[str, Any]: A dictionary containing:
            - is_strong (bool): Whether the password is strong enough
            - score (int): The password strength score (0-5)
            - feedback (List[str]): A list of feedback messages
    """
    is_strong, score, feedback = validate_password_strength(password)
    
    return {
        "is_strong": is_strong,
        "score": score,
        "feedback": feedback
    }

def configure_password_requirements(
    min_length: int = None,
    require_uppercase: bool = None,
    require_lowercase: bool = None,
    require_numbers: bool = None,
    require_special_chars: bool = None
) -> None:
    """
    Configure password strength requirements.
    
    Args:
        min_length (int, optional): Minimum password length. Defaults to None.
        require_uppercase (bool, optional): Require uppercase letters. Defaults to None.
        require_lowercase (bool, optional): Require lowercase letters. Defaults to None.
        require_numbers (bool, optional): Require numbers. Defaults to None.
        require_special_chars (bool, optional): Require special characters. Defaults to None.
    """
    global MIN_LENGTH, REQUIRE_UPPERCASE, REQUIRE_LOWERCASE, REQUIRE_NUMBERS, REQUIRE_SPECIAL_CHARS
    
    if min_length is not None:
        MIN_LENGTH = min_length
    
    if require_uppercase is not None:
        REQUIRE_UPPERCASE = require_uppercase
    
    if require_lowercase is not None:
        REQUIRE_LOWERCASE = require_lowercase
    
    if require_numbers is not None:
        REQUIRE_NUMBERS = require_numbers
    
    if require_special_chars is not None:
        REQUIRE_SPECIAL_CHARS = require_special_chars
    
    logger.info(f"Password requirements configured: min_length={MIN_LENGTH}, uppercase={REQUIRE_UPPERCASE}, lowercase={REQUIRE_LOWERCASE}, numbers={REQUIRE_NUMBERS}, special_chars={REQUIRE_SPECIAL_CHARS}")

def get_password_requirements() -> Dict[str, Any]:
    """
    Get password strength requirements.
    
    Returns:
        Dict[str, Any]: A dictionary containing the password requirements
    """
    return {
        "min_length": MIN_LENGTH,
        "require_uppercase": REQUIRE_UPPERCASE,
        "require_lowercase": REQUIRE_LOWERCASE,
        "require_numbers": REQUIRE_NUMBERS,
        "require_special_chars": REQUIRE_SPECIAL_CHARS
    }
