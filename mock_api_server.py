"""
Mock API server for testing the Windows VM Agent.

This simple HTTP server responds to API requests from the agent with mock data.
"""
import http.server
import socketserver
import json
import re
import logging
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mock_api')

# Port to listen on
PORT = 9000

class MockAPIHandler(http.server.BaseHTTPRequestHandler):
    """Handler for the mock API server."""

    def do_GET(self):
        """Handle GET requests."""
        try:
            # Parse the URL
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)

            logger.info(f"Received request: {path} with params: {query_params}")

            # Check authorization
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_error(401, "Unauthorized: Missing or invalid Authorization header")
                return

            # Handle account config endpoint
            if path == '/api/account-config' and 'account_id' in query_params:
                account_id = query_params['account_id'][0]
                vm_id = query_params.get('vm_id', ['unknown'])[0]

                # Generate mock response data
                response_data = {
                    'account_id': account_id,
                    'vm_id': vm_id,
                    'proxy_server': f"http://proxy-{account_id}.example.com:8080",
                    'proxy_bypass': "localhost;127.0.0.1;*.local"
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                logger.info(f"Sent account config for account_id: {account_id}")
                return

            # Default response for unknown endpoints
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def log_message(self, format, *args):
        """Override to use our logger instead of printing to stderr."""
        logger.info(format % args)

def run_server():
    """Run the mock API server."""
    print(f"Starting mock API server on port {PORT}...")
    with socketserver.TCPServer(("", PORT), MockAPIHandler) as httpd:
        print(f"Mock API server running at http://localhost:{PORT}")
        logger.info(f"Mock API server running at http://localhost:{PORT}")
        try:
            print("Server is ready to receive requests")
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped by user")
            logger.info("Server stopped by user")
        finally:
            httpd.server_close()

if __name__ == "__main__":
    run_server()
