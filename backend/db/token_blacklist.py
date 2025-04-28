"""
Token blacklist module.

This module provides functions for managing a token blacklist to support token revocation.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)

# In-memory token blacklist
# In a production environment, this should be stored in a database or Redis
_token_blacklist: Dict[str, float] = {}
_blacklist_lock = threading.RLock()

# Constants
DEFAULT_CLEANUP_INTERVAL = 3600  # 1 hour in seconds

def add_to_blacklist(token_jti: str, expires_at: float) -> bool:
    """
    Add a token to the blacklist.
    
    Args:
        token_jti (str): The token JTI (JWT ID)
        expires_at (float): The token expiration timestamp
        
    Returns:
        bool: True if the token was added to the blacklist, False otherwise
    """
    with _blacklist_lock:
        try:
            _token_blacklist[token_jti] = expires_at
            logger.info(f"Token {token_jti[:8]}... added to blacklist, expires at {datetime.fromtimestamp(expires_at)}")
            return True
        except Exception as e:
            logger.error(f"Error adding token to blacklist: {e}")
            return False

def is_blacklisted(token_jti: str) -> bool:
    """
    Check if a token is blacklisted.
    
    Args:
        token_jti (str): The token JTI (JWT ID)
        
    Returns:
        bool: True if the token is blacklisted, False otherwise
    """
    with _blacklist_lock:
        # Check if the token is in the blacklist
        if token_jti in _token_blacklist:
            # Check if the token has expired
            expires_at = _token_blacklist[token_jti]
            if time.time() > expires_at:
                # Token has expired, remove it from the blacklist
                del _token_blacklist[token_jti]
                logger.debug(f"Token {token_jti[:8]}... removed from blacklist (expired)")
                return False
            
            logger.info(f"Token {token_jti[:8]}... is blacklisted")
            return True
        
        return False

def cleanup_blacklist() -> int:
    """
    Clean up expired tokens from the blacklist.
    
    Returns:
        int: The number of tokens removed from the blacklist
    """
    with _blacklist_lock:
        current_time = time.time()
        expired_tokens = [jti for jti, expires_at in _token_blacklist.items() if current_time > expires_at]
        
        for jti in expired_tokens:
            del _token_blacklist[jti]
        
        if expired_tokens:
            logger.info(f"Removed {len(expired_tokens)} expired tokens from blacklist")
        
        return len(expired_tokens)

def get_blacklist_size() -> int:
    """
    Get the size of the blacklist.
    
    Returns:
        int: The number of tokens in the blacklist
    """
    with _blacklist_lock:
        return len(_token_blacklist)

def get_blacklist_stats() -> Dict[str, Any]:
    """
    Get statistics about the blacklist.
    
    Returns:
        Dict[str, Any]: Statistics about the blacklist
    """
    with _blacklist_lock:
        current_time = time.time()
        total_tokens = len(_token_blacklist)
        expired_tokens = sum(1 for expires_at in _token_blacklist.values() if current_time > expires_at)
        valid_tokens = total_tokens - expired_tokens
        
        return {
            "total_tokens": total_tokens,
            "expired_tokens": expired_tokens,
            "valid_tokens": valid_tokens,
            "timestamp": current_time
        }

# Start a background thread to periodically clean up the blacklist
def start_cleanup_thread(interval: int = DEFAULT_CLEANUP_INTERVAL) -> threading.Thread:
    """
    Start a background thread to periodically clean up the blacklist.
    
    Args:
        interval (int, optional): The cleanup interval in seconds. Defaults to DEFAULT_CLEANUP_INTERVAL.
        
    Returns:
        threading.Thread: The cleanup thread
    """
    def cleanup_thread():
        logger.info(f"Token blacklist cleanup thread started (interval: {interval}s)")
        while True:
            try:
                # Sleep first to avoid cleaning up immediately after startup
                time.sleep(interval)
                
                # Clean up the blacklist
                cleanup_blacklist()
            except Exception as e:
                logger.error(f"Error in token blacklist cleanup thread: {e}")
    
    thread = threading.Thread(target=cleanup_thread, daemon=True)
    thread.start()
    return thread

# Start the cleanup thread when the module is imported
cleanup_thread = start_cleanup_thread()
