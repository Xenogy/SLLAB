"""
API client for the Windows VM Agent.

This module handles communication with the manager API.
"""
import logging
import requests
from typing import Dict, Any, Optional
import json
import string

logger = logging.getLogger(__name__)

# Import LogClient if available, otherwise use a dummy class
try:
    from utils.log_client import LogClient
    HAS_LOG_CLIENT = True
except ImportError:
    HAS_LOG_CLIENT = False

    # Dummy LogClient for backward compatibility
    class LogClient:
        def __init__(self, *args, **kwargs):
            pass

        def log_api_call(self, *args, **kwargs):
            pass

        def log_auth(self, *args, **kwargs):
            pass

        def log_error(self, *args, **kwargs):
            pass

class APIClient:
    """Client for communicating with the manager API."""

    def __init__(self, base_url: str, api_key: str, vm_identifier: str):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the manager API.
            api_key: API key for authentication.
            vm_identifier: Identifier for this VM.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.vm_identifier = vm_identifier
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'WindowsVMAgent/1.0'
        })
        # Note: We don't use the Authorization header for API key authentication
        # The API key is passed as a query parameter instead

        # Initialize log client if available
        self.log_client = None
        if HAS_LOG_CLIENT:
            try:
                self.log_client = LogClient(base_url, api_key, vm_identifier)
                logger.info("Log client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize log client: {e}")
                # Continue without log client

    def get_data(self, endpoint_template: str, context_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get data from the API.

        Args:
            endpoint_template: API endpoint template with placeholders.
            context_data: Data to fill in the placeholders.

        Returns:
            API response data as a dictionary, or None if the request failed.
        """
        try:
            # Create a context with VM identifier and event data
            context = {'VMIdentifier': self.vm_identifier}
            context.update(context_data)

            # Format the endpoint URL with the context data
            endpoint = self._format_template(endpoint_template, context)

            # Ensure the endpoint starts with a slash if it doesn't already
            if not endpoint.startswith('/'):
                endpoint = '/' + endpoint

            # Check if the endpoint already has query parameters
            if '?' in endpoint:
                # Add the API key as an additional query parameter
                url = f"{self.base_url}{endpoint}&api_key={requests.utils.quote(self.api_key)}"
            else:
                # Add the API key as the first query parameter
                url = f"{self.base_url}{endpoint}?api_key={requests.utils.quote(self.api_key)}"

            # Log the constructed URL for debugging
            logger.debug(f"Constructed URL: {url}")

            logger.info(f"Making API request to: {url}")
            logger.debug(f"API Key: {self.api_key}")
            logger.debug(f"Headers: {self.session.headers}")

            # Try both with and without the Authorization header
            headers_without_auth = self.session.headers.copy()
            if 'Authorization' in headers_without_auth:
                del headers_without_auth['Authorization']

            try:
                # First try without Authorization header (using only query param)
                logger.info("Trying request with API key as query parameter only")

                # Log API call attempt
                if self.log_client:
                    self.log_client.log_api_call(endpoint, "GET", None, None, {
                        "auth_method": "query_param",
                        "url": url
                    })

                response = requests.get(url, headers=headers_without_auth, timeout=30)

                if response.status_code == 200:
                    logger.info("Request succeeded with API key as query parameter")

                    # Log successful API call
                    if self.log_client:
                        self.log_client.log_api_call(endpoint, "GET", response.status_code, None, {
                            "auth_method": "query_param",
                            "success": True
                        })

                    return response.json()
                else:
                    logger.warning(f"Request with query parameter failed: {response.status_code}: {response.text}")

                    # Log failed API call
                    if self.log_client:
                        self.log_client.log_api_call(endpoint, "GET", response.status_code,
                                                   f"Query param auth failed: {response.text}", {
                                                       "auth_method": "query_param",
                                                       "success": False
                                                   })

                    # Try with both Authorization header and query parameter
                    logger.info("Trying request with both Authorization header and query parameter")

                    # Log second API call attempt
                    if self.log_client:
                        self.log_client.log_api_call(endpoint, "GET", None, None, {
                            "auth_method": "header_and_query_param",
                            "url": url
                        })

                    response = self.session.get(url, timeout=30)

                    if response.status_code == 200:
                        logger.info("Request succeeded with both Authorization header and query parameter")

                        # Log successful API call
                        if self.log_client:
                            self.log_client.log_api_call(endpoint, "GET", response.status_code, None, {
                                "auth_method": "header_and_query_param",
                                "success": True
                            })

                        return response.json()
                    else:
                        error_msg = f"All request attempts failed. Status: {response.status_code}, Response: {response.text}"
                        logger.error(error_msg)

                        # Log failed API call
                        if self.log_client:
                            self.log_client.log_api_call(endpoint, "GET", response.status_code,
                                                       error_msg, {
                                                           "auth_method": "header_and_query_param",
                                                           "success": False
                                                       })

                        return None
            except Exception as e:
                error_msg = f"Error during request: {str(e)}"
                logger.error(error_msg)

                # Log exception
                if self.log_client:
                    self.log_client.log_error(f"API request failed: {endpoint}", "api", {
                        "endpoint": endpoint,
                        "method": "GET",
                        "error": str(e)
                    }, exception=e)

                return None

        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse API response as JSON: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {str(e)}")
            return None

    def _format_template(self, template: str, context: Dict[str, Any]) -> str:
        """
        Format a template string with context data.

        Args:
            template: Template string with {placeholders}.
            context: Dictionary of values to substitute.

        Returns:
            Formatted string.
        """
        # Use string.Formatter for safer formatting
        formatter = string.Formatter()
        result = []

        for literal_text, field_name, format_spec, conversion in formatter.parse(template):
            result.append(literal_text)

            if field_name is not None:
                if field_name in context:
                    value = context[field_name]
                    # Convert to string and escape for URL
                    if isinstance(value, (int, float, bool)):
                        value = str(value)
                    result.append(requests.utils.quote(str(value)))
                else:
                    # Keep the placeholder if not in context
                    result.append(f"{{{field_name}}}")

        return ''.join(result)

    def test_api_key(self) -> bool:
        """
        Test if the API key is valid by making a simple request.

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        try:
            # Try to access the account-config endpoint with a test account ID
            test_url = f"{self.base_url}/windows-vm-agent/account-config?vm_id={self.vm_identifier}&account_id=test&api_key={requests.utils.quote(self.api_key)}"
            logger.info(f"Testing API key with request to: {test_url}")

            # Log API key test attempt
            if self.log_client:
                self.log_client.log_auth("Testing API key authentication", False, {
                    "url": test_url,
                    "status": "attempt"
                })

            # Try without Authorization header first
            headers_without_auth = self.session.headers.copy()
            if 'Authorization' in headers_without_auth:
                del headers_without_auth['Authorization']

            response = requests.get(test_url, headers=headers_without_auth, timeout=30)

            # Check if we got a 401 (invalid API key) or any other error
            if response.status_code == 401:
                error_msg = f"API key test failed: {response.status_code}: {response.text}"
                logger.error(error_msg)

                # Log authentication failure
                if self.log_client:
                    self.log_client.log_auth("API key authentication failed", False, {
                        "status_code": response.status_code,
                        "response": response.text
                    })

                return False
            elif response.status_code == 404:
                # 404 means the account wasn't found, but the API key was valid
                logger.info("API key is valid (got 404 for test account)")

                # Log authentication success
                if self.log_client:
                    self.log_client.log_auth("API key authentication successful", True, {
                        "status_code": response.status_code,
                        "status": "valid_key_404_resource"
                    })

                return True
            elif response.status_code == 200:
                logger.info("API key is valid (got 200 OK)")

                # Log authentication success
                if self.log_client:
                    self.log_client.log_auth("API key authentication successful", True, {
                        "status_code": response.status_code,
                        "status": "valid_key_200_ok"
                    })

                return True
            else:
                warning_msg = f"Unexpected status code during API key test: {response.status_code}"
                logger.warning(warning_msg)

                # Log authentication warning
                if self.log_client:
                    self.log_client.log_auth("API key authentication returned unexpected status", False, {
                        "status_code": response.status_code,
                        "response": response.text,
                        "status": "unexpected_status"
                    })

                return False

        except Exception as e:
            error_msg = f"Error testing API key: {str(e)}"
            logger.error(error_msg)

            # Log authentication error
            if self.log_client:
                self.log_client.log_error("API key authentication test failed with exception", "security", {
                    "error": str(e)
                }, exception=e)

            return False
