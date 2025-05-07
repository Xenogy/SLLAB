"""
Test proxy list for the BanCheck API.

This module provides a default list of test proxies that can be used when no other proxy list is supplied.
These are placeholder proxies and should be replaced with real proxies in production.
"""

# List of test proxies (these are example/placeholder proxies)
# Format: http://user:pass@host:port or http://host:port
TEST_PROXIES = [
    "http://test-proxy-1.example.com:8080",
    "http://test-proxy-2.example.com:8080",
    "http://test-proxy-3.example.com:8080",
    "http://test-proxy-4.example.com:8080",
    "http://test-proxy-5.example.com:8080",
]

def get_test_proxies():
    """
    Get the list of test proxies.
    
    Returns:
        List[str]: A list of test proxy URLs.
    """
    return TEST_PROXIES.copy()
