"""
Test script for the password validator module.

This script tests the password validator module by:
1. Testing password strength validation
2. Testing password strength feedback
3. Testing configuring password requirements
"""

import logging
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly from the module to avoid import issues
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.utils.password_validator import validate_password_strength, get_password_strength_feedback, configure_password_requirements, get_password_requirements

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestPasswordValidator(unittest.TestCase):
    """Test the password validator module."""

    def setUp(self):
        """Set up the test case."""
        # Reset password requirements to defaults
        configure_password_requirements(
            min_length=8,
            require_uppercase=True,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=True
        )

    def test_validate_password_strength(self):
        """Test password strength validation."""
        # Test empty password
        is_strong, score, feedback = validate_password_strength("")
        self.assertFalse(is_strong)
        self.assertEqual(score, 0)
        self.assertIn("Password cannot be empty", feedback)

        # Test password that's too short
        is_strong, score, feedback = validate_password_strength("abc123")
        self.assertFalse(is_strong)
        self.assertLess(score, 3)
        self.assertIn("Password must be at least 8 characters long", feedback)

        # Test password without uppercase
        is_strong, score, feedback = validate_password_strength("abcdefg123!")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password must contain at least one uppercase letter", feedback)

        # Test password without lowercase
        is_strong, score, feedback = validate_password_strength("ABCDEFG123!")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password must contain at least one lowercase letter", feedback)

        # Test password without numbers
        is_strong, score, feedback = validate_password_strength("ABCDefgh!")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password must contain at least one number", feedback)

        # Test password without special characters
        is_strong, score, feedback = validate_password_strength("ABCDefgh123")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password must contain at least one special character", feedback)

        # Test password with repeated characters
        is_strong, score, feedback = validate_password_strength("ABCDefggg123!")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password contains repeated characters", feedback)

        # Test password with sequential numbers
        is_strong, score, feedback = validate_password_strength("ABCDefg123!")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password contains sequential numbers", feedback)

        # Test password with sequential letters
        is_strong, score, feedback = validate_password_strength("ABCDefg1!")
        self.assertFalse(is_strong)
        self.assertLess(score, 5)
        self.assertIn("Password contains sequential letters", feedback)

        # Test strong password
        is_strong, score, feedback = validate_password_strength("P@ssw0rd!X")
        self.assertTrue(is_strong)
        self.assertGreaterEqual(score, 3)

    def test_get_password_strength_feedback(self):
        """Test password strength feedback."""
        # Test strong password
        feedback = get_password_strength_feedback("P@ssw0rd!X")
        self.assertTrue(feedback["is_strong"])
        self.assertGreaterEqual(feedback["score"], 3)

        # Test weak password
        feedback = get_password_strength_feedback("password")
        self.assertFalse(feedback["is_strong"])
        self.assertLess(feedback["score"], 3)

    def test_configure_password_requirements(self):
        """Test configuring password requirements."""
        # Configure password requirements
        configure_password_requirements(
            min_length=6,
            require_uppercase=False,
            require_lowercase=True,
            require_numbers=True,
            require_special_chars=False
        )

        # Test that the requirements were updated
        requirements = get_password_requirements()
        self.assertEqual(requirements["min_length"], 6)
        self.assertFalse(requirements["require_uppercase"])
        self.assertTrue(requirements["require_lowercase"])
        self.assertTrue(requirements["require_numbers"])
        self.assertFalse(requirements["require_special_chars"])

        # Test password that meets the new requirements
        is_strong, score, feedback = validate_password_strength("abcde1")
        self.assertTrue(is_strong)

        # Test password that doesn't meet the new requirements
        is_strong, score, feedback = validate_password_strength("ABCDE1")
        self.assertFalse(is_strong)
        self.assertIn("Password must contain at least one lowercase letter", feedback)

if __name__ == "__main__":
    unittest.main()
