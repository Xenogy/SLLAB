"""
Proxy Manager for BanCheck API

This module provides a thread-safe proxy management system that ensures
proxies are not reused while they're still in use by another task.
"""

import threading
import time
from typing import List, Optional, Set, Dict

from app.utils import validate_proxy_string

class ProxyManager:
    """
    Thread-safe proxy manager that tracks proxy usage and prevents reuse
    of proxies that are still in use by other tasks.
    """

    def __init__(self, proxies: List[str]):
        """
        Initialize the proxy manager with a list of proxies.

        Args:
            proxies: List of proxy strings in the format http(s)://[user:pass@]host:port
        """
        # Validate all proxies before adding them to the manager
        valid_proxies = []
        if proxies:
            for proxy in proxies:
                valid_proxy = validate_proxy_string(proxy)
                if valid_proxy:
                    valid_proxies.append(valid_proxy)
                else:
                    print(f"Warning: Skipping invalid proxy: '{proxy}'")

        self.all_proxies = valid_proxies
        self.available_proxies = list(valid_proxies)
        self.in_use_proxies: Set[str] = set()
        self.lock = threading.Lock()
        self.proxy_usage_count: Dict[str, int] = {proxy: 0 for proxy in self.all_proxies}

    def get_proxy(self) -> Optional[str]:
        """
        Get an available proxy. Returns None if no proxies are available.

        Returns:
            A proxy string or None if no proxies are available
        """
        with self.lock:
            if not self.available_proxies:
                return None

            # Get the least used proxy from available proxies
            if self.all_proxies:
                proxy = min(self.available_proxies, key=lambda p: self.proxy_usage_count.get(p, 0))
            else:
                proxy = self.available_proxies[0]

            self.available_proxies.remove(proxy)
            self.in_use_proxies.add(proxy)
            self.proxy_usage_count[proxy] = self.proxy_usage_count.get(proxy, 0) + 1

            return proxy

    def release_proxy(self, proxy: str) -> None:
        """
        Release a proxy back to the available pool.

        Args:
            proxy: The proxy string to release
        """
        with self.lock:
            if proxy in self.in_use_proxies:
                self.in_use_proxies.remove(proxy)
                self.available_proxies.append(proxy)

    def wait_for_proxy(self, timeout: float = 30.0, check_interval: float = 0.5) -> Optional[str]:
        """
        Wait for a proxy to become available, up to the specified timeout.

        Args:
            timeout: Maximum time to wait in seconds
            check_interval: How often to check for available proxies

        Returns:
            A proxy string or None if timeout is reached
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            proxy = self.get_proxy()
            if proxy:
                return proxy
            time.sleep(check_interval)
        return None

    def get_status(self) -> Dict:
        """
        Get the current status of the proxy manager.

        Returns:
            A dictionary with proxy status information
        """
        with self.lock:
            return {
                "total_proxies": len(self.all_proxies),
                "available_proxies": len(self.available_proxies),
                "in_use_proxies": len(self.in_use_proxies),
                "usage_counts": dict(self.proxy_usage_count)
            }
