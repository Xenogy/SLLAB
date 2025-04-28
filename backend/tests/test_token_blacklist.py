"""
Test script for the token blacklist module.

This script tests the token blacklist module by:
1. Testing adding tokens to the blacklist
2. Testing checking if tokens are blacklisted
3. Testing cleaning up expired tokens
4. Testing getting blacklist statistics
"""

import logging
import sys
import os
import time
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.token_blacklist import add_to_blacklist, is_blacklisted, cleanup_blacklist, get_blacklist_size, get_blacklist_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestTokenBlacklist(unittest.TestCase):
    """Test the token blacklist module."""
    
    def setUp(self):
        """Set up the test case."""
        # Clear the blacklist
        from db.token_blacklist import _token_blacklist
        _token_blacklist.clear()
    
    def test_add_to_blacklist(self):
        """Test adding tokens to the blacklist."""
        # Test adding a token
        token_jti = "test_token"
        expires_at = time.time() + 3600  # 1 hour from now
        result = add_to_blacklist(token_jti, expires_at)
        
        # Test that the token was added
        self.assertTrue(result)
        
        # Test that the token is in the blacklist
        from db.token_blacklist import _token_blacklist
        self.assertIn(token_jti, _token_blacklist)
        self.assertEqual(_token_blacklist[token_jti], expires_at)
    
    def test_is_blacklisted(self):
        """Test checking if tokens are blacklisted."""
        # Add a token to the blacklist
        token_jti = "test_token"
        expires_at = time.time() + 3600  # 1 hour from now
        add_to_blacklist(token_jti, expires_at)
        
        # Test that the token is blacklisted
        result = is_blacklisted(token_jti)
        self.assertTrue(result)
        
        # Test that a non-existent token is not blacklisted
        result = is_blacklisted("non_existent_token")
        self.assertFalse(result)
        
        # Test that an expired token is not blacklisted
        token_jti = "expired_token"
        expires_at = time.time() - 3600  # 1 hour ago
        add_to_blacklist(token_jti, expires_at)
        
        result = is_blacklisted(token_jti)
        self.assertFalse(result)
        
        # Test that the expired token was removed from the blacklist
        from db.token_blacklist import _token_blacklist
        self.assertNotIn(token_jti, _token_blacklist)
    
    def test_cleanup_blacklist(self):
        """Test cleaning up expired tokens."""
        # Add some tokens to the blacklist
        add_to_blacklist("token1", time.time() + 3600)  # 1 hour from now
        add_to_blacklist("token2", time.time() - 3600)  # 1 hour ago
        add_to_blacklist("token3", time.time() - 7200)  # 2 hours ago
        
        # Test that there are 3 tokens in the blacklist
        from db.token_blacklist import _token_blacklist
        self.assertEqual(len(_token_blacklist), 3)
        
        # Clean up the blacklist
        result = cleanup_blacklist()
        
        # Test that 2 tokens were removed
        self.assertEqual(result, 2)
        
        # Test that there is 1 token left in the blacklist
        self.assertEqual(len(_token_blacklist), 1)
        self.assertIn("token1", _token_blacklist)
    
    def test_get_blacklist_size(self):
        """Test getting the blacklist size."""
        # Add some tokens to the blacklist
        add_to_blacklist("token1", time.time() + 3600)  # 1 hour from now
        add_to_blacklist("token2", time.time() + 7200)  # 2 hours from now
        
        # Test that there are 2 tokens in the blacklist
        result = get_blacklist_size()
        self.assertEqual(result, 2)
    
    def test_get_blacklist_stats(self):
        """Test getting blacklist statistics."""
        # Add some tokens to the blacklist
        add_to_blacklist("token1", time.time() + 3600)  # 1 hour from now
        add_to_blacklist("token2", time.time() - 3600)  # 1 hour ago
        
        # Get blacklist statistics
        stats = get_blacklist_stats()
        
        # Test that the statistics are correct
        self.assertEqual(stats["total_tokens"], 2)
        self.assertEqual(stats["expired_tokens"], 1)
        self.assertEqual(stats["valid_tokens"], 1)
        self.assertIn("timestamp", stats)

if __name__ == "__main__":
    unittest.main()
