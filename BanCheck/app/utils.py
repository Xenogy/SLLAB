import csv
import io
from typing import List, Tuple, Dict, Optional, Any

class ScriptConfig:
    """
    Configuration for the BanCheck API with optimized parameters.

    This class provides optimized parameters for different account list sizes.
    The parameters are automatically adjusted based on the number of accounts.
    """
    # Base configuration
    MIN_URLS_PER_LOGICAL_BATCH = 10
    MAX_URLS_PER_LOGICAL_BATCH = 100
    MIN_WORKERS = 1
    MAX_WORKERS_CAP_TOTAL = 50

    # Default parameters (optimized for small lists < 50 accounts)
    # Keep these for backward compatibility
    DEFAULT_MAX_CONCURRENT_BATCHES = 6  # Increased from 3 to 6 for better parallelism
    DEFAULT_MAX_WORKERS_PER_BATCH = 3   # Kept at 3 as it provides good balance
    DEFAULT_INTER_REQUEST_SUBMIT_DELAY_S = 0.2  # Increased from 0.1 to 0.2 to reduce rate limiting
    DEFAULT_MAX_RETRIES_PER_URL = 3     # Increased from 2 to 3 for better reliability
    DEFAULT_RETRY_DELAY_SECONDS = 5     # Kept at 5 seconds as it works well

    @staticmethod
    def get_optimized_params(account_count: int) -> Dict[str, Any]:
        """
        Get optimized parameters based on account list size.

        Args:
            account_count: Number of accounts to check

        Returns:
            Dictionary with optimized parameters
        """
        # Default parameters (optimized for small lists < 50 accounts)
        params = {
            "logical_batch_size": 10,
            "max_concurrent_batches": 6,
            "max_workers_per_batch": 3,
            "inter_request_submit_delay": 0.2,
            "max_retries_per_url": 3,
            "retry_delay_seconds": 5
        }

        # Medium list (50-200 accounts)
        if 50 <= account_count < 200:
            params["logical_batch_size"] = 20

        # Large list (200-500 accounts)
        elif 200 <= account_count < 500:
            params["logical_batch_size"] = 30
            params["max_concurrent_batches"] = 8
            params["max_workers_per_batch"] = 4
            params["inter_request_submit_delay"] = 0.3

        # Very large list (500+ accounts)
        elif account_count >= 500:
            params["logical_batch_size"] = 50
            params["max_concurrent_batches"] = 10
            params["max_workers_per_batch"] = 5
            params["inter_request_submit_delay"] = 0.5

        return params

def interpret_status(status_string: str) -> Tuple[str, str]:
    if "RETRY_FAILED_FINAL" in status_string:
        final_error = status_string.split("RETRY_FAILED_FINAL: ")[-1]
        summary, details = interpret_status(final_error)
        return f"Error (Retries Exhausted - {summary})", details
    if status_string.startswith("BANNED:"): return "Banned", status_string.replace("BANNED: ", "").strip()
    if status_string == "NOT_BANNED_PUBLIC": return "Not Banned (Public Profile)", ""
    if status_string == "PRIVATE_PROFILE": return "Private Profile", ""
    if status_string == "PROFILE_UNEXPECTED_STRUCTURE": return "Profile Structure Issue", "Could not find typical profile elements or ban info."
    if status_string.startswith("ERROR_HTTP_404_NOT_FOUND"): return "Error (Profile Not Found)", status_string
    if status_string.startswith("PROXY_ERROR_"): return f"Proxy Error ({status_string.replace('PROXY_ERROR_', '').replace('_', ' ').title()})", status_string
    if status_string.startswith("ERROR_"): return f"Error ({status_string.replace('ERROR_', '').replace('_', ' ').title()})", status_string
    return "Unknown Status", status_string

def generate_urls_from_steamids(steam_ids: List[str]) -> Tuple[List[str], List[Dict]]:
    urls, problem_ids_info = [], []
    base_url = "https://steamcommunity.com/profiles/{}"
    for idx, steam_id_original in enumerate(steam_ids):
        if steam_id_original:
            steam_id = steam_id_original.strip()
            if steam_id.startswith("765") and len(steam_id) == 17 and steam_id.isdigit():
                urls.append(base_url.format(steam_id))
            else:
                problem_ids_info.append({"row_number": idx + 1, "id_value": steam_id_original, "reason": "Invalid SteamID64 format"})
        else:
            problem_ids_info.append({"row_number": idx + 1, "id_value": None, "reason": "Empty SteamID provided"})
    return urls, problem_ids_info


def generate_urls_from_csv_content(csv_content: str, id_column_name: str = "steamid") -> Tuple[List[str], List[Dict]]:
    urls, problem_ids_info = [], []
    base_url = "https://steamcommunity.com/profiles/{}"
    try:
        # Use io.StringIO to treat the string content like a file
        csvfile = io.StringIO(csv_content)
        reader = csv.DictReader(csvfile)
        if id_column_name not in reader.fieldnames:
            problem_ids_info.append({"row_number": "N/A", "id_value": "N/A", "reason": f"Column '{id_column_name}' not found in CSV headers: {reader.fieldnames}"})
            return [], problem_ids_info

        for row_num, row in enumerate(reader, 1):
            steam_id_original = row.get(id_column_name)
            if steam_id_original:
                steam_id = steam_id_original.strip()
                if steam_id.startswith("765") and len(steam_id) == 17 and steam_id.isdigit():
                    urls.append(base_url.format(steam_id))
                else:
                    problem_ids_info.append({"row_number": row_num, "id_value": steam_id_original, "reason": "Invalid SteamID64 format"})
            else:
                problem_ids_info.append({"row_number": row_num, "id_value": None, "reason": f"Missing or empty SteamID in column '{id_column_name}'"})
    except Exception as e:
        problem_ids_info.append({"row_number": "N/A", "id_value": "N/A", "reason": f"Error reading CSV content: {e}"})
        return [], problem_ids_info
    return urls, problem_ids_info

def validate_proxy_string(proxy_string: str) -> Optional[str]:
    """
    Validate and format a proxy string.

    Args:
        proxy_string: The proxy string to validate

    Returns:
        A properly formatted proxy string or None if invalid
    """
    if not proxy_string or not isinstance(proxy_string, str):
        return None

    # Remove any whitespace
    proxy_string = proxy_string.strip()
    if not proxy_string:
        return None

    # Skip comments
    if proxy_string.startswith("#"):
        return None

    # Add http:// prefix if not present
    if not (proxy_string.startswith("http://") or proxy_string.startswith("https://")):
        proxy_string = f"http://{proxy_string}"

    # Basic validation - should contain at least a host and port
    # This is a simple check, could be more sophisticated
    if ":" not in proxy_string[8:]:  # Check after http:// or https://
        print(f"Warning: Proxy string '{proxy_string}' doesn't appear to have a port")
        return None

    return proxy_string

def load_proxies_from_str(proxy_list_str: Optional[str]) -> List[str]:
    """
    Load proxies from a multiline string.

    Args:
        proxy_list_str: A string containing one proxy per line

    Returns:
        A list of validated proxy strings
    """
    proxies = []
    if not proxy_list_str:
        return proxies

    try:
        for line_num, line_content in enumerate(io.StringIO(proxy_list_str), 1):
            proxy_string = validate_proxy_string(line_content)
            if proxy_string:
                proxies.append(proxy_string)

        if proxies:
            print(f"API: Loaded {len(proxies)} proxies from string. First few: {proxies[:min(3, len(proxies))]}")
        else:
            print(f"API: No valid proxies found in provided string.")
    except Exception as e:
        print(f"API: Error loading proxies from string: {e}")

    return proxies

async def load_proxies_from_file(proxy_file_content: bytes) -> List[str]:
    """
    Load proxies from an uploaded file's content.

    Args:
        proxy_file_content: The binary content of the uploaded proxy file

    Returns:
        List of proxy strings in the format http(s)://[user:pass@]host:port
    """
    proxies = []
    if not proxy_file_content:
        return proxies

    try:
        # Decode the file content to string
        proxy_list_str = proxy_file_content.decode('utf-8-sig')  # Handle BOM

        # Use our load_proxies_from_str function to process the content
        proxies = load_proxies_from_str(proxy_list_str)

        if proxies:
            print(f"API: Loaded {len(proxies)} proxies from file. First few: {proxies[:min(3, len(proxies))]}")
        else:
            print(f"API: No valid proxies found in uploaded file.")
    except Exception as e:
        print(f"API: Error loading proxies from file: {e}")

    return proxies

def load_default_proxies() -> List[str]:
    """
    Load proxies from the default proxy file in test_data/proxies.txt.

    This function is used when no proxy list is provided to the API endpoints.

    Returns:
        List of proxy strings in the format http(s)://[user:pass@]host:port
    """
    import os

    # Define the default proxy file path relative to the project root
    default_proxy_path = os.path.join("BanCheck", "test_data", "proxies.txt")

    # Check if the file exists
    if not os.path.exists(default_proxy_path):
        print(f"API: Default proxy file not found at {default_proxy_path}")
        return []

    proxies = []
    try:
        # Read the file content
        with open(default_proxy_path, 'r') as f:
            proxy_list_str = f.read()

        # Use our load_proxies_from_str function to process the content
        proxies = load_proxies_from_str(proxy_list_str)

        if proxies:
            print(f"API: Loaded {len(proxies)} proxies from default file. First few: {proxies[:min(3, len(proxies))]}")
        else:
            print(f"API: No valid proxies found in default proxy file.")
    except Exception as e:
        print(f"API: Error loading default proxies: {e}")

    return proxies