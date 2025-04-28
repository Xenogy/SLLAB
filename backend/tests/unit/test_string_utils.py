"""
Unit tests for string utilities.
"""

import pytest
from utils.string_utils import (
    is_valid_uuid, is_valid_email, is_valid_username, is_valid_password,
    is_valid_steam_id, sanitize_string, truncate_string, mask_sensitive_data
)

class TestStringUtils:
    """Tests for string utilities."""
    
    @pytest.mark.unit
    def test_is_valid_uuid(self):
        """Test is_valid_uuid function."""
        # Valid UUIDs
        assert is_valid_uuid("123e4567-e89b-12d3-a456-426614174000") is True
        assert is_valid_uuid("123e4567-e89b-12d3-a456-426614174000".upper()) is True
        
        # Invalid UUIDs
        assert is_valid_uuid("not-a-uuid") is False
        assert is_valid_uuid("123e4567-e89b-12d3-a456-42661417400") is False  # Too short
        assert is_valid_uuid("123e4567-e89b-12d3-a456-4266141740000") is False  # Too long
        assert is_valid_uuid("123e4567-e89b-12d3-a456-42661417400g") is False  # Invalid character
        assert is_valid_uuid(None) is False
        assert is_valid_uuid(123) is False
    
    @pytest.mark.unit
    def test_is_valid_email(self):
        """Test is_valid_email function."""
        # Valid emails
        assert is_valid_email("user@example.com") is True
        assert is_valid_email("user.name@example.com") is True
        assert is_valid_email("user+tag@example.com") is True
        assert is_valid_email("user@subdomain.example.com") is True
        
        # Invalid emails
        assert is_valid_email("not-an-email") is False
        assert is_valid_email("user@") is False
        assert is_valid_email("@example.com") is False
        assert is_valid_email("user@.com") is False
        assert is_valid_email("user@example.") is False
        assert is_valid_email(None) is False
        assert is_valid_email(123) is False
    
    @pytest.mark.unit
    def test_is_valid_username(self):
        """Test is_valid_username function."""
        # Valid usernames
        assert is_valid_username("user123") is True
        assert is_valid_username("user_123") is True
        assert is_valid_username("user-123") is True
        assert is_valid_username("a" * 32) is True  # Maximum length
        
        # Invalid usernames
        assert is_valid_username("ab") is False  # Too short
        assert is_valid_username("a" * 33) is False  # Too long
        assert is_valid_username("user@123") is False  # Invalid character
        assert is_valid_username("user 123") is False  # Invalid character
        assert is_valid_username(None) is False
        assert is_valid_username(123) is False
    
    @pytest.mark.unit
    def test_is_valid_password(self):
        """Test is_valid_password function."""
        # Valid passwords
        assert is_valid_password("password123") is True
        assert is_valid_password("Password123!") is True
        assert is_valid_password("a" * 8) is True  # Minimum length
        assert is_valid_password("a" * 64) is True  # Maximum length
        
        # Invalid passwords
        assert is_valid_password("pass") is False  # Too short
        assert is_valid_password("a" * 65) is False  # Too long
        assert is_valid_password(None) is False
        assert is_valid_password(123) is False
    
    @pytest.mark.unit
    def test_is_valid_steam_id(self):
        """Test is_valid_steam_id function."""
        # Valid Steam IDs
        assert is_valid_steam_id("76561198123456789") is True
        
        # Invalid Steam IDs
        assert is_valid_steam_id("7656119812345678") is False  # Too short
        assert is_valid_steam_id("765611981234567890") is False  # Too long
        assert is_valid_steam_id("7656119812345678a") is False  # Invalid character
        assert is_valid_steam_id(None) is False
        assert is_valid_steam_id(123) is False
    
    @pytest.mark.unit
    def test_sanitize_string(self):
        """Test sanitize_string function."""
        # Test with HTML
        assert sanitize_string("<script>alert('XSS')</script>") == "alert('XSS')"
        assert sanitize_string("<b>Bold</b>") == "Bold"
        
        # Test with HTML allowed
        assert sanitize_string("<b>Bold</b>", allow_html=True) == "<b>Bold</b>"
        
        # Test with control characters
        assert sanitize_string("Hello\x00World") == "HelloWorld"
        assert sanitize_string("Hello\x1FWorld") == "HelloWorld"
        assert sanitize_string("Hello\x7FWorld") == "HelloWorld"
        
        # Test with non-string input
        assert sanitize_string(None) == ""
        assert sanitize_string(123) == ""
    
    @pytest.mark.unit
    def test_truncate_string(self):
        """Test truncate_string function."""
        # Test with short string
        assert truncate_string("Hello", 10) == "Hello"
        
        # Test with long string
        assert truncate_string("Hello World", 5) == "He..."
        
        # Test with custom suffix
        assert truncate_string("Hello World", 5, suffix="...more") == "H...more"
        
        # Test with non-string input
        assert truncate_string(None, 10) == ""
        assert truncate_string(123, 10) == ""
    
    @pytest.mark.unit
    def test_mask_sensitive_data(self):
        """Test mask_sensitive_data function."""
        # Test with short string
        assert mask_sensitive_data("1234") == "1234"
        
        # Test with long string
        assert mask_sensitive_data("1234567890") == "12******90"
        
        # Test with custom mask character
        assert mask_sensitive_data("1234567890", mask_char="#") == "12######90"
        
        # Test with custom visible prefix and suffix
        assert mask_sensitive_data("1234567890", visible_prefix=3, visible_suffix=3) == "123****890"
        assert mask_sensitive_data("1234567890", visible_prefix=0, visible_suffix=0) == "**********"
        
        # Test with non-string input
        assert mask_sensitive_data(None) == ""
        assert mask_sensitive_data(123) == ""
