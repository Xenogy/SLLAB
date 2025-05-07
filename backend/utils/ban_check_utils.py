"""
Utility functions for the ban check functionality.

This module provides utility functions for checking Steam profiles for bans.
It includes functions for generating URLs, checking profiles, and managing proxies.
"""

import csv
import io
import re
import time
import threading
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from typing import List, Dict, Any, Optional, Set, Tuple

from db.repositories.ban_check import BanCheckRepository

# Configure default parameters
class ScriptConfig:
    """Configuration for the BanCheck API with optimized parameters."""
    # Base configuration
    MIN_URLS_PER_LOGICAL_BATCH = 10
    MAX_URLS_PER_LOGICAL_BATCH = 100
    MIN_WORKERS = 1
    MAX_WORKERS_CAP_TOTAL = 50
    
    # Default parameters
    DEFAULT_MAX_CONCURRENT_BATCHES = 6
    DEFAULT_MAX_WORKERS_PER_BATCH = 3
    DEFAULT_INTER_REQUEST_SUBMIT_DELAY_S = 0.2
    DEFAULT_MAX_RETRIES_PER_URL = 3
    DEFAULT_RETRY_DELAY_SECONDS = 5
    
    # Adaptive parameters based on account list size
    @staticmethod
    def get_optimal_params(num_accounts: int) -> Dict[str, Any]:
        """Get optimal parameters based on the number of accounts."""
        if num_accounts < 50:
            return {
                "logical_batch_size": 10,
                "max_concurrent_batches": 6,
                "max_workers_per_batch": 3,
                "inter_request_submit_delay": 0.2,
                "max_retries_per_url": 3,
                "retry_delay_seconds": 5
            }
        elif num_accounts < 200:
            return {
                "logical_batch_size": 20,
                "max_concurrent_batches": 8,
                "max_workers_per_batch": 3,
                "inter_request_submit_delay": 0.3,
                "max_retries_per_url": 3,
                "retry_delay_seconds": 5
            }
        else:
            return {
                "logical_batch_size": 50,
                "max_concurrent_batches": 10,
                "max_workers_per_batch": 2,
                "inter_request_submit_delay": 0.5,
                "max_retries_per_url": 3,
                "retry_delay_seconds": 10
            }

# Proxy Manager
class ProxyManager:
    """Thread-safe proxy manager that tracks proxy usage and prevents reuse."""
    
    def __init__(self, proxies: List[str]):
        """Initialize the proxy manager with a list of proxies."""
        self.all_proxies = list(proxies) if proxies else []
        self.available_proxies = list(self.all_proxies)
        self.in_use_proxies: Set[str] = set()
        self.lock = threading.Lock()
        self.proxy_usage_count: Dict[str, int] = {proxy: 0 for proxy in self.all_proxies}
    
    def get_proxy(self) -> Optional[str]:
        """Get an available proxy. Returns None if no proxies are available."""
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
        """Release a proxy back to the available pool."""
        with self.lock:
            if proxy in self.in_use_proxies:
                self.in_use_proxies.remove(proxy)
                self.available_proxies.append(proxy)
    
    def wait_for_proxy(self, timeout: float = 30.0, check_interval: float = 0.5) -> Optional[str]:
        """Wait for a proxy to become available, up to the specified timeout."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            proxy = self.get_proxy()
            if proxy:
                return proxy
            time.sleep(check_interval)
        return None
    
    def get_status(self) -> Dict:
        """Get the current status of the proxy manager."""
        with self.lock:
            return {
                "total_proxies": len(self.all_proxies),
                "available_proxies": len(self.available_proxies),
                "in_use_proxies": len(self.in_use_proxies),
                "usage_counts": dict(self.proxy_usage_count)
            }

# URL Generation Functions
def generate_urls_from_steamids(steam_ids: List[str]) -> List[str]:
    """Generate Steam profile URLs from a list of Steam IDs."""
    urls = []
    for steam_id in steam_ids:
        # Clean the Steam ID
        steam_id = steam_id.strip()
        if steam_id:
            # Check if it's a valid Steam ID format
            if re.match(r'^[0-9]{17}$', steam_id):
                urls.append(f"https://steamcommunity.com/profiles/{steam_id}")
            elif re.match(r'^STEAM_[0-5]:[01]:[0-9]+$', steam_id):
                # Convert Steam ID to Steam64 ID
                # This is a simplified conversion and may not work for all cases
                parts = steam_id.split(":")
                if len(parts) == 3:
                    try:
                        y = int(parts[1])
                        z = int(parts[2])
                        steam64_id = 76561197960265728 + z * 2 + y
                        urls.append(f"https://steamcommunity.com/profiles/{steam64_id}")
                    except ValueError:
                        pass
            else:
                # Assume it's a custom URL
                urls.append(f"https://steamcommunity.com/id/{steam_id}")
    return urls

def generate_urls_from_csv_content(csv_content: str, steam_id_column: str = "steam64_id") -> List[str]:
    """Generate Steam profile URLs from CSV content."""
    urls = []
    try:
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            if steam_id_column in row and row[steam_id_column]:
                steam_id = row[steam_id_column].strip()
                if steam_id:
                    # Check if it's a valid Steam ID format
                    if re.match(r'^[0-9]{17}$', steam_id):
                        urls.append(f"https://steamcommunity.com/profiles/{steam_id}")
                    elif re.match(r'^STEAM_[0-5]:[01]:[0-9]+$', steam_id):
                        # Convert Steam ID to Steam64 ID
                        # This is a simplified conversion and may not work for all cases
                        parts = steam_id.split(":")
                        if len(parts) == 3:
                            try:
                                y = int(parts[1])
                                z = int(parts[2])
                                steam64_id = 76561197960265728 + z * 2 + y
                                urls.append(f"https://steamcommunity.com/profiles/{steam64_id}")
                            except ValueError:
                                pass
                    else:
                        # Assume it's a custom URL
                        urls.append(f"https://steamcommunity.com/id/{steam_id}")
    except Exception as e:
        print(f"Error processing CSV: {e}")
    
    return urls

# Ban Check Functions
def check_single_url_for_ban_info(url: str, proxy_to_use: Optional[str] = None,
                                 max_retries: int = 0, retry_delay: float = 5,
                                 batch_id_for_log: Any = "N/A", url_idx_for_log: int = 0,
                                 total_in_batch_for_log: int = 0) -> str:
    """Check a single URL for ban information."""
    log_prefix = f"Batch {batch_id_for_log} - URL {url_idx_for_log}/{total_in_batch_for_log}"
    print(f"{log_prefix} - Checking {url}")
    
    last_error_status = "ERROR_UNKNOWN"
    
    # Extract Steam ID from URL
    steam_id = None
    if "/profiles/" in url:
        steam_id = url.split("/profiles/")[1].split("/")[0]
    elif "/id/" in url:
        steam_id = url.split("/id/")[1].split("/")[0]
    
    # Setup proxy
    proxies = None
    if proxy_to_use:
        proxies = {
            "http": proxy_to_use,
            "https": proxy_to_use
        }
    
    # Try to get the page with retries
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                proxies=proxies,
                timeout=10,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
            )
            
            if response.status_code != 200:
                last_error_status = f"ERROR_HTTP_{response.status_code}"
                print(f"{log_prefix} - HTTP error {response.status_code} (Attempt {attempt+1} of {max_retries+1})")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue
            
            # Parse the page
            soup = BeautifulSoup(response.content, 'html.parser')
            ban_info_span = soup.find('span', class_='profile_ban_info')
            if ban_info_span:
                print(f"{log_prefix} - Found ban info.")
                return f"BANNED: {ban_info_span.get_text(strip=True)}"
            if soup.find('div', class_='profile_private_info'):
                print(f"{log_prefix} - Profile is private.")
                return "PRIVATE_PROFILE"
            if soup.find('div', class_='profile_header_centered_persona'):
                print(f"{log_prefix} - Profile public, no ban span.")
                return "NOT_BANNED_PUBLIC"
            print(f"{log_prefix} - Unexpected page structure.")
            return "PROFILE_UNEXPECTED_STRUCTURE"
        
        except requests.exceptions.Timeout:
            last_error_status = "ERROR_TIMEOUT"
            print(f"{log_prefix} - Timed out (Attempt {attempt+1} of {max_retries+1})")
        except requests.exceptions.ProxyError:
            last_error_status = "ERROR_PROXY"
            print(f"{log_prefix} - Proxy error (Attempt {attempt+1} of {max_retries+1})")
        except requests.exceptions.ConnectionError:
            last_error_status = "ERROR_CONNECTION"
            print(f"{log_prefix} - Connection error (Attempt {attempt+1} of {max_retries+1})")
        except Exception as e:
            last_error_status = f"ERROR: {str(e)}"
            print(f"{log_prefix} - Error: {e} (Attempt {attempt+1} of {max_retries+1})")
        
        if attempt < max_retries:
            time.sleep(retry_delay)
    
    return last_error_status

def interpret_status(raw_status: str) -> Dict[str, str]:
    """Interpret the raw status string and return a structured result."""
    if raw_status.startswith("BANNED:"):
        ban_text = raw_status.replace("BANNED:", "").strip()
        return {
            "status_summary": "BANNED",
            "details": ban_text
        }
    elif raw_status == "PRIVATE_PROFILE":
        return {
            "status_summary": "PRIVATE",
            "details": "Profile is private"
        }
    elif raw_status == "NOT_BANNED_PUBLIC":
        return {
            "status_summary": "NOT_BANNED",
            "details": "No bans detected"
        }
    elif raw_status == "PROFILE_UNEXPECTED_STRUCTURE":
        return {
            "status_summary": "UNKNOWN",
            "details": "Could not determine ban status due to unexpected page structure"
        }
    elif raw_status.startswith("ERROR"):
        return {
            "status_summary": "ERROR",
            "details": raw_status
        }
    else:
        return {
            "status_summary": "UNKNOWN",
            "details": raw_status
        }

# Background Task Function
def run_checks_background_task(
    task_id: str,
    generated_urls: List[str],
    proxies_list: List[str],
    params: Dict[str, Any],
    user_id: Optional[int] = None,
    user_role: Optional[str] = None
):
    """Run the ban checks in a background task."""
    # Create repository
    ban_check_repo = BanCheckRepository(user_id=user_id, user_role=user_role)
    
    # Update task status
    ban_check_repo.update_task(
        task_id=task_id,
        data={
            "status": "PROCESSING",
            "message": "Starting URL checks...",
            "progress": 0
        }
    )
    
    # Get total number of URLs to process
    total_urls = len(generated_urls)
    if total_urls == 0:
        ban_check_repo.update_task(
            task_id=task_id,
            data={
                "status": "FAILED",
                "message": "No valid URLs to process.",
                "progress": 100
            }
        )
        return
    
    # Initialize proxy manager
    proxy_manager = ProxyManager(proxies_list)
    
    # Initialize results
    results = []
    
    # Initialize progress tracking
    processed_urls = 0
    progress_lock = threading.Lock()
    
    def update_progress():
        nonlocal processed_urls
        with progress_lock:
            processed_urls += 1
            progress = (processed_urls / total_urls) * 100
            # Update task progress every 5% or when complete
            if progress % 5 < 1 or processed_urls == total_urls:
                ban_check_repo.update_task(
                    task_id=task_id,
                    data={
                        "progress": progress,
                        "message": f"Processed {processed_urls}/{total_urls} URLs ({progress:.1f}%)"
                    }
                )
    
    # Process URLs in batches
    try:
        # Get parameters
        logical_batch_size = params.get("logical_batch_size", ScriptConfig.DEFAULT_MAX_CONCURRENT_BATCHES)
        max_concurrent_batches = params.get("max_concurrent_batches", ScriptConfig.DEFAULT_MAX_WORKERS_PER_BATCH)
        max_workers_per_batch = params.get("max_workers_per_batch", ScriptConfig.DEFAULT_MAX_WORKERS_PER_BATCH)
        inter_request_submit_delay = params.get("inter_request_submit_delay", ScriptConfig.DEFAULT_INTER_REQUEST_SUBMIT_DELAY_S)
        max_retries_per_url = params.get("max_retries_per_url", ScriptConfig.DEFAULT_MAX_RETRIES_PER_URL)
        retry_delay_seconds = params.get("retry_delay_seconds", ScriptConfig.DEFAULT_RETRY_DELAY_SECONDS)
        
        # Adjust batch size if needed
        logical_batch_size = max(ScriptConfig.MIN_URLS_PER_LOGICAL_BATCH, min(logical_batch_size, ScriptConfig.MAX_URLS_PER_LOGICAL_BATCH))
        
        # Calculate number of batches
        num_batches = (total_urls + logical_batch_size - 1) // logical_batch_size
        
        # Process batches
        with ThreadPoolExecutor(max_workers=max_concurrent_batches) as executor:
            batch_futures = []
            
            for batch_idx in range(num_batches):
                # Get URLs for this batch
                start_idx = batch_idx * logical_batch_size
                end_idx = min(start_idx + logical_batch_size, total_urls)
                batch_urls = generated_urls[start_idx:end_idx]
                
                # Submit batch
                future = executor.submit(
                    process_batch,
                    batch_urls,
                    batch_idx,
                    proxy_manager,
                    max_workers_per_batch,
                    inter_request_submit_delay,
                    max_retries_per_url,
                    retry_delay_seconds,
                    update_progress
                )
                batch_futures.append(future)
            
            # Collect results
            for future in as_completed(batch_futures):
                batch_results = future.result()
                results.extend(batch_results)
        
        # Update task with results
        proxy_stats = proxy_manager.get_status()
        ban_check_repo.update_task(
            task_id=task_id,
            data={
                "status": "COMPLETED",
                "message": f"Completed checking {total_urls} URLs",
                "progress": 100,
                "results": results,
                "proxy_stats": proxy_stats
            }
        )
    
    except Exception as e:
        # Update task with error
        ban_check_repo.update_task(
            task_id=task_id,
            data={
                "status": "FAILED",
                "message": f"Error processing URLs: {str(e)}",
                "progress": (processed_urls / total_urls) * 100 if total_urls > 0 else 0,
                "results": results
            }
        )

def process_batch(
    urls_in_batch: List[str],
    batch_id: int,
    proxy_manager: ProxyManager,
    max_workers_in_batch: int,
    inter_req_submit_delay_in_batch: float,
    max_retries_url: int,
    retry_delay_url: float,
    update_progress_callback: callable
) -> List[Dict[str, Any]]:
    """Process a batch of URLs."""
    batch_results = []
    
    # Get a proxy for this batch
    proxy_for_this_batch = proxy_manager.get_proxy()
    
    try:
        # Adjust workers based on available URLs
        effective_workers_in_batch = min(max_workers_in_batch, len(urls_in_batch))
        
        # Process URLs
        if effective_workers_in_batch == 1:
            for url_idx, url in enumerate(urls_in_batch):
                if inter_req_submit_delay_in_batch > 0 and url_idx > 0:
                    time.sleep(inter_req_submit_delay_in_batch)
                
                raw_status = check_single_url_for_ban_info(
                    url,
                    proxy_for_this_batch,
                    max_retries_url,
                    retry_delay_url,
                    batch_id,
                    url_idx + 1,
                    len(urls_in_batch)
                )
                
                # Extract Steam ID from URL
                steam_id = None
                if "/profiles/" in url:
                    steam_id = url.split("/profiles/")[1].split("/")[0]
                elif "/id/" in url:
                    steam_id = url.split("/id/")[1].split("/")[0]
                
                # Interpret status
                status_info = interpret_status(raw_status)
                
                # Add result
                result = {
                    "steam_id": steam_id,
                    "url": url,
                    "status_summary": status_info["status_summary"],
                    "details": status_info["details"],
                    "proxy_used": proxy_for_this_batch or "None",
                    "batch_id": batch_id
                }
                batch_results.append(result)
                
                # Update progress
                update_progress_callback()
        else:
            with ThreadPoolExecutor(max_workers=effective_workers_in_batch) as batch_executor:
                future_to_url_map_batch = {}
                
                for url_idx, url_in_b in enumerate(urls_in_batch):
                    future = batch_executor.submit(
                        check_single_url_for_ban_info,
                        url_in_b,
                        proxy_for_this_batch,
                        max_retries_url,
                        retry_delay_url,
                        batch_id,
                        url_idx + 1,
                        len(urls_in_batch)
                    )
                    future_to_url_map_batch[future] = url_in_b
                    
                    if inter_req_submit_delay_in_batch > 0 and url_idx < len(urls_in_batch) - 1:
                        time.sleep(inter_req_submit_delay_in_batch)
                
                for future_b in as_completed(future_to_url_map_batch):
                    url = future_to_url_map_batch[future_b]
                    
                    try:
                        raw_status = future_b.result()
                        
                        # Extract Steam ID from URL
                        steam_id = None
                        if "/profiles/" in url:
                            steam_id = url.split("/profiles/")[1].split("/")[0]
                        elif "/id/" in url:
                            steam_id = url.split("/id/")[1].split("/")[0]
                        
                        # Interpret status
                        status_info = interpret_status(raw_status)
                        
                        # Add result
                        result = {
                            "steam_id": steam_id,
                            "url": url,
                            "status_summary": status_info["status_summary"],
                            "details": status_info["details"],
                            "proxy_used": proxy_for_this_batch or "None",
                            "batch_id": batch_id
                        }
                        batch_results.append(result)
                    
                    except Exception as exc_b:
                        print(f"Batch {batch_id} - Error processing URL {url}: {exc_b}")
                        
                        # Extract Steam ID from URL
                        steam_id = None
                        if "/profiles/" in url:
                            steam_id = url.split("/profiles/")[1].split("/")[0]
                        elif "/id/" in url:
                            steam_id = url.split("/id/")[1].split("/")[0]
                        
                        # Add error result
                        result = {
                            "steam_id": steam_id,
                            "url": url,
                            "status_summary": "ERROR",
                            "details": f"Error: {str(exc_b)}",
                            "proxy_used": proxy_for_this_batch or "None",
                            "batch_id": batch_id
                        }
                        batch_results.append(result)
                    
                    # Update progress
                    update_progress_callback()
    
    finally:
        # Release proxy
        if proxy_for_this_batch:
            proxy_manager.release_proxy(proxy_for_this_batch)
    
    return batch_results
