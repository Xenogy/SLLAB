import requests
from bs4 import BeautifulSoup
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
from typing import List, Dict, Any, Optional
from app.utils import interpret_status, validate_proxy_string
from app.proxy_manager import ProxyManager

# In-memory store for task statuses and results (for demonstration)
# In production, use Redis, a database, or another persistent store.
tasks_db: Dict[str, Dict[str, Any]] = {}

# Global dictionary to store proxy managers for each task
# This ensures each task has its own proxy manager
proxy_managers: Dict[str, ProxyManager] = {}

def check_single_url_for_ban_info(url: str, proxy_to_use: Optional[str] = None,
                                  max_retries: int = 0, retry_delay: float = 5,
                                  batch_id_for_log: Any = "N/A", url_idx_for_log: int = 0,
                                  total_in_batch_for_log: int = 0) -> str:
    # Add a delay for testing progress tracking
    if "test_progress" in url or url.startswith("765611980000"):
        print(f"Adding test delay for URL: {url}")
        time.sleep(1.0)  # 1 second delay for testing

    # Set up headers for the request
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.9'}

    # Validate and set up proxy
    proxies_dict = None
    if proxy_to_use:
        # Validate the proxy string
        valid_proxy = validate_proxy_string(proxy_to_use)
        if valid_proxy:
            proxies_dict = {"http": valid_proxy, "https": valid_proxy}
        else:
            print(f"Warning: Invalid proxy format: '{proxy_to_use}'. Proceeding without proxy.")
            proxy_to_use = None

    log_prefix = f"[API Task - Batch {batch_id_for_log} | URL {url_idx_for_log}/{total_in_batch_for_log}] {url}"
    last_error_status = "ERROR_UNKNOWN_NO_ATTEMPTS_MADE"

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"{log_prefix} - Retrying (Retry {attempt} of {max_retries}, Delay: {retry_delay}s)...")

            with requests.Session() as session:
                session.headers.update(headers)
                if proxies_dict: session.proxies.update(proxies_dict)
                response = session.get(url, timeout=25)
            response.raise_for_status()

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
        except requests.exceptions.ProxyError as pe:
            last_error_status = f"PROXY_ERROR_CONNECT: {pe}"
            print(f"{log_prefix} - Proxy Error: {pe} (Attempt {attempt+1} of {max_retries+1})")
        except requests.exceptions.HTTPError as http_err:
            sc = getattr(getattr(http_err, 'response', None), 'status_code', "UNKNOWN_HTTP_STATUS")
            last_error_status = f"ERROR_HTTP_{sc} ({http_err})"
            print(f"{log_prefix} - HTTP Error {sc}: {http_err} (Attempt {attempt+1} of {max_retries+1})")
            if sc == 404: return last_error_status
        except requests.exceptions.RequestException as re:
            last_error_status = f"ERROR_CONNECTION" if isinstance(re, requests.exceptions.ConnectionError) else f"ERROR_REQUEST_GENERAL: {re}"
            print(f"{log_prefix} - Request Exception: {re} (Attempt {attempt+1} of {max_retries+1})")
        except Exception as e:
            last_error_status = f"ERROR_UNEXPECTED: {e}"
            print(f"{log_prefix} - Unexpected Error: {e} (Attempt {attempt+1} of {max_retries+1})")
            return last_error_status
        if attempt < max_retries:
            is_retryable = ("TIMEOUT" in last_error_status or "PROXY_ERROR" in last_error_status or "ERROR_CONNECTION" in last_error_status or
                            any(code in last_error_status for code in ["ERROR_HTTP_500", "ERROR_HTTP_502", "ERROR_HTTP_503", "ERROR_HTTP_504", "ERROR_HTTP_429"]))
            if is_retryable:
                time.sleep(retry_delay)
                continue
            else: return last_error_status
        else:
            print(f"{log_prefix} - Max retries reached. Final error: {last_error_status}")
            return f"RETRY_FAILED_FINAL: {last_error_status}"
    return f"RETRY_FAILED_FINAL: {last_error_status}" # Fallback

def process_one_batch(batch_id: Any, urls_in_batch: List[str], proxy_for_this_batch: Optional[str],
                      workers_in_batch: int, inter_req_submit_delay_in_batch: float,
                      max_retries_url: int, retry_delay_url: float,
                      task_id: Optional[str] = None,
                      total_urls: Optional[int] = None,
                      processed_urls_ref: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """
    Process a batch of URLs.

    Args:
        processed_urls_ref: A mutable list with a single integer element that tracks the total processed URLs.
                           This allows us to update the counter from within this function.
    """
    print(f"[API Task - Batch {batch_id}] Starting. URLs: {len(urls_in_batch)}. Proxy: {proxy_for_this_batch or 'None'}. Workers: {workers_in_batch}.")
    batch_results = []
    effective_workers_in_batch = max(1, min(workers_in_batch, len(urls_in_batch)))

    # Track URLs processed within this batch
    urls_processed_in_batch = 0
    total_urls_in_batch = len(urls_in_batch)

    # Function to update progress after each URL is processed
    def update_progress():
        nonlocal urls_processed_in_batch
        urls_processed_in_batch += 1

        # Update the global counter if provided
        if processed_urls_ref is not None:
            processed_urls_ref[0] += 1

            # Update progress in tasks_db if task_id is provided
            if task_id and task_id in tasks_db and total_urls:
                # Only update every few URLs to avoid excessive updates
                if processed_urls_ref[0] % 5 == 0 or processed_urls_ref[0] == total_urls:
                    progress = min(99, (processed_urls_ref[0] / total_urls) * 100)
                    tasks_db[task_id].update({"progress": round(progress, 2)})
                    print(f"[API Task {task_id}] Progress: {processed_urls_ref[0]}/{total_urls} URLs ({progress:.2f}%)")

    if effective_workers_in_batch == 1:
        for url_idx, url in enumerate(urls_in_batch):
            if inter_req_submit_delay_in_batch > 0 and url_idx > 0:
                time.sleep(inter_req_submit_delay_in_batch)
            raw_status = check_single_url_for_ban_info(url, proxy_for_this_batch,
                                                       max_retries_url, retry_delay_url,
                                                       batch_id, url_idx + 1, len(urls_in_batch))
            batch_results.append({'url': url, 'raw_status': raw_status,
                                  'proxy_used': proxy_for_this_batch or "None", 'batch_id': batch_id})

            # Update progress
            update_progress()
    else:
        with ThreadPoolExecutor(max_workers=effective_workers_in_batch, thread_name_prefix=f'APIBatch{batch_id}Worker') as batch_executor:
            future_to_url_map_batch = {}
            for url_idx, url_in_b in enumerate(urls_in_batch):
                future = batch_executor.submit(check_single_url_for_ban_info,
                                               url_in_b, proxy_for_this_batch,
                                               max_retries_url, retry_delay_url,
                                               batch_id, url_idx + 1, len(urls_in_batch))
                future_to_url_map_batch[future] = url_in_b
                if inter_req_submit_delay_in_batch > 0 and url_idx < len(urls_in_batch) -1 :
                    time.sleep(inter_req_submit_delay_in_batch)
            for future_b in as_completed(future_to_url_map_batch):
                url_res = future_to_url_map_batch[future_b]
                try: raw_status_res = future_b.result()
                except Exception as exc_b:
                    raw_status_res = f"ERROR_INNER_THREAD_EXCEPTION: {exc_b}"
                    print(f"[API Task - Batch {batch_id}] URL {url_res} - Inner thread exception: {exc_b}")
                batch_results.append({'url': url_res, 'raw_status': raw_status_res,
                                      'proxy_used': proxy_for_this_batch or "None", 'batch_id': batch_id})

                # Update progress
                update_progress()
    print(f"[API Task - Batch {batch_id}] Finished. Results: {len(batch_results)}.")
    return batch_results


def run_checks_background_task(
    task_id: str,
    generated_urls: List[str],
    proxies_list: List[str],
    params: Dict[str, Any] # Contains all concurrency/retry params
):
    # Initialize task with 0% progress
    tasks_db[task_id] = {"status": "PROCESSING", "results": [], "progress": 0, "message": "Starting URL checks..."}

    # Get total number of URLs to process
    total_urls = len(generated_urls)
    if total_urls == 0:
        tasks_db[task_id].update({"status": "FAILED", "message": "No valid URLs to process.", "progress": 100})
        return

    # Initialize proxy manager for this task
    proxy_manager = ProxyManager(proxies_list)
    proxy_managers[task_id] = proxy_manager

    # Log proxy information
    proxy_count = len(proxies_list) if proxies_list else 0
    if proxy_count > 0:
        print(f"[API Task {task_id}] Using {proxy_count} proxies")
    else:
        print(f"[API Task {task_id}] No proxies provided, running without proxies")

    # Simple counter for processed URLs - this is our single source of truth for progress
    processed_urls_count = 0

    # Check if max_concurrent_batches exceeds proxy count
    if proxies_list and params['max_concurrent_batches'] > len(proxies_list):
        print(f"[API Task {task_id}] Warning: max_concurrent_batches ({params['max_concurrent_batches']}) exceeds proxy count ({len(proxies_list)})")
        print(f"[API Task {task_id}] Reducing max_concurrent_batches to match proxy count")
        params['max_concurrent_batches'] = len(proxies_list)

    # Divide URLs into batches
    all_results_list = []
    logical_url_batches = [generated_urls[i:i + params['logical_batch_size']] for i in range(0, total_urls, params['logical_batch_size'])]
    total_logical_batches_to_run = len(logical_url_batches)

    # Create a mutable reference to track processed URLs across all batches
    # Using a list with a single integer element allows it to be modified by reference
    processed_urls_ref = [0]

    try:
        with ThreadPoolExecutor(max_workers=params['max_concurrent_batches'], thread_name_prefix='APIOuterBatchRunner') as outer_executor:
            future_to_batch_info_map = {}

            # Submit initial batches up to max_concurrent_batches
            for batch_idx, current_url_list_for_batch in enumerate(logical_url_batches[:params['max_concurrent_batches']]):
                batch_unique_id = batch_idx + 1

                # Get a proxy from the manager
                proxy_for_this_outer_batch = proxy_manager.get_proxy()

                # Submit the batch for processing with the shared counter
                future = outer_executor.submit(
                    process_one_batch,
                    batch_unique_id,
                    current_url_list_for_batch,
                    proxy_for_this_outer_batch,
                    params['max_workers_per_batch'],
                    params['inter_request_submit_delay'],
                    params['max_retries_per_url'],
                    params['retry_delay_seconds'],
                    task_id,
                    total_urls,
                    processed_urls_ref
                )

                # Store batch info for tracking
                future_to_batch_info_map[future] = {
                    'batch_id': batch_unique_id,
                    'proxy': proxy_for_this_outer_batch
                }

            # Process remaining batches as earlier ones complete
            next_batch_idx = params['max_concurrent_batches']

            # Process completed batches and submit new ones
            while future_to_batch_info_map:
                # Check if any futures are done
                done_futures = []
                for future in list(future_to_batch_info_map.keys()):
                    if future.done():
                        done_futures.append(future)

                # If no futures are done, wait a bit and check again
                if not done_futures:
                    print(f"[API Task {task_id}] Waiting for batches to complete... Current progress: {processed_urls_ref[0]}/{total_urls} URLs")
                    time.sleep(1)  # Short sleep to avoid CPU spinning
                    continue

                # Process completed batches
                for future_outer in done_futures:
                    batch_info = future_to_batch_info_map.pop(future_outer)
                    batch_id_completed = batch_info['batch_id']
                    proxy_used = batch_info['proxy']

                    try:
                        # Get results from the completed batch
                        results_from_one_batch = future_outer.result()
                        all_results_list.extend(results_from_one_batch)
                    except Exception as exc_outer:
                        print(f"[API Task {task_id} - OuterExecutor] Batch {batch_id_completed} task generated an exception: {exc_outer}")
                    finally:
                        # Release the proxy back to the pool
                        if proxy_used:
                            proxy_manager.release_proxy(proxy_used)

                        # Submit a new batch if there are any left
                        if next_batch_idx < len(logical_url_batches):
                            batch_unique_id = next_batch_idx + 1
                            current_url_list = logical_url_batches[next_batch_idx]

                            # Get a proxy for the new batch
                            proxy_for_new_batch = proxy_manager.get_proxy()

                            # Submit the new batch with the shared counter
                            future = outer_executor.submit(
                                process_one_batch,
                                batch_unique_id,
                                current_url_list,
                                proxy_for_new_batch,
                                params['max_workers_per_batch'],
                                params['inter_request_submit_delay'],
                                params['max_retries_per_url'],
                                params['retry_delay_seconds'],
                                task_id,
                                total_urls,
                                processed_urls_ref
                            )

                            # Store batch info for tracking
                            future_to_batch_info_map[future] = {
                                'batch_id': batch_unique_id,
                                'proxy': proxy_for_new_batch
                            }

                            next_batch_idx += 1

        # Ensure progress is at 100% for all completed URLs
        print(f"[API Task {task_id}] All batches completed. Total URLs processed: {processed_urls_ref[0]}/{total_urls}")

        # Prepare final results
        output_data_for_api = []
        for res_item in all_results_list:
            steam_id = res_item['url'].split('/')[-1]
            raw_s, proxy_u = res_item['raw_status'], res_item['proxy_used']
            batch_id_info = res_item.get('batch_id', 'N/A')
            s_sum, details = interpret_status(raw_s)
            if ("Error" in s_sum or "Proxy Error" in s_sum) and proxy_u != "None" and proxy_u not in details:
                details = f"{details} (Proxy: {proxy_u})" if details else f"(Proxy: {proxy_u})"
            output_data_for_api.append({'steam_id': steam_id, 'status_summary': s_sum, 'details': details,
                                         'proxy_used': proxy_u, 'batch_id': batch_id_info})

        # Add proxy usage statistics to the task results
        proxy_stats = proxy_manager.get_status()

        # Set final progress to 100%
        tasks_db[task_id].update({
            "status": "COMPLETED",
            "results": output_data_for_api,
            "progress": 100,
            "message": "Processing complete.",
            "proxy_stats": proxy_stats
        })

        print(f"[API Task {task_id}] Task completed. Final progress: 100%")

        # Clean up the proxy manager
        if task_id in proxy_managers:
            del proxy_managers[task_id]

    except Exception as e:
        print(f"[API Task {task_id}] Critical error during background processing: {e}")

        # Update task status to failed but keep the current progress
        current_progress = round((processed_urls_ref[0] / total_urls) * 100, 2) if total_urls > 0 else 0
        tasks_db[task_id].update({
            "status": "FAILED",
            "message": f"Critical error: {e}",
            "progress": current_progress
        })

        print(f"[API Task {task_id}] Task failed. Final progress: {current_progress}%")

        # Clean up the proxy manager even on error
        if task_id in proxy_managers:
            del proxy_managers[task_id]