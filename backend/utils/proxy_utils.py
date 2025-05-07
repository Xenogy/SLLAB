"""
Utility functions for proxy management.

This module provides utility functions for validating and managing proxies.
"""

import re
import requests
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

def validate_proxy_string(proxy_str: str) -> Optional[str]:
    """
    Validate a proxy string and return a normalized version.
    
    Args:
        proxy_str (str): The proxy string to validate.
        
    Returns:
        Optional[str]: A normalized proxy string or None if invalid.
    """
    if not proxy_str or not isinstance(proxy_str, str):
        return None
    
    # Remove whitespace
    proxy_str = proxy_str.strip()
    
    # Skip empty lines and comments
    if not proxy_str or proxy_str.startswith('#'):
        return None
    
    # Check if it's already a valid proxy URL
    if proxy_str.startswith(('http://', 'https://')):
        # Validate format with regex
        if re.match(r'^(http|https)://([^:@]+:[^:@]+@)?[a-zA-Z0-9.-]+:[0-9]+$', proxy_str):
            return proxy_str
    else:
        # Try to parse as host:port
        if re.match(r'^[a-zA-Z0-9.-]+:[0-9]+$', proxy_str):
            return f"http://{proxy_str}"
        
        # Try to parse as user:pass@host:port
        if re.match(r'^[^:@]+:[^:@]+@[a-zA-Z0-9.-]+:[0-9]+$', proxy_str):
            return f"http://{proxy_str}"
    
    return None

def test_proxy(proxy: str, timeout: int = 5) -> bool:
    """
    Test if a proxy is working.
    
    Args:
        proxy (str): The proxy string to test.
        timeout (int, optional): The timeout in seconds. Defaults to 5.
        
    Returns:
        bool: True if the proxy is working, False otherwise.
    """
    try:
        proxies = {
            "http": proxy,
            "https": proxy
        }
        
        response = requests.get(
            "https://www.google.com",
            proxies=proxies,
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        
        return response.status_code == 200
    except:
        return False

def load_proxies_from_str(proxy_list_str: str) -> List[str]:
    """
    Load proxies from a multiline string.
    
    Args:
        proxy_list_str (str): The multiline string containing proxies.
        
    Returns:
        List[str]: A list of valid proxy strings.
    """
    if not proxy_list_str:
        return []
    
    proxies = []
    for line in proxy_list_str.splitlines():
        proxy = validate_proxy_string(line)
        if proxy:
            proxies.append(proxy)
    
    return proxies

def load_proxies_from_file(file_content: str) -> List[str]:
    """
    Load proxies from file content.
    
    Args:
        file_content (str): The file content containing proxies.
        
    Returns:
        List[str]: A list of valid proxy strings.
    """
    return load_proxies_from_str(file_content)

def load_default_proxies() -> List[str]:
    """
    Load default proxies.
    
    Returns:
        List[str]: A list of default proxy strings.
    """
    # This is just a placeholder. In a real implementation, you might load
    # default proxies from a configuration file or database.
    return []
