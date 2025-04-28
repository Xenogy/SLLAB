"""
Performance tests for API endpoints.

This module contains tests to measure the performance of API endpoints.
"""

import pytest
import time
import statistics
from fastapi.testclient import TestClient
from main import app
from routers.auth import get_current_user

client = TestClient(app)

# Mock the authentication
@pytest.fixture
def mock_auth():
    """Mock the authentication."""
    app.dependency_overrides[get_current_user] = lambda: {"id": 1, "role": "admin"}
    yield
    app.dependency_overrides = {}

@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_get_proxmox_nodes_performance(self, mock_auth):
        """Test the performance of the GET /proxmox-nodes endpoint."""
        # Number of requests to make
        num_requests = 100
        
        # Store response times
        response_times = []
        
        # Make requests and measure response time
        for _ in range(num_requests):
            start_time = time.time()
            response = client.get("/proxmox-nodes/")
            end_time = time.time()
            
            # Calculate response time in milliseconds
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            # Check that the response is successful
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[int(num_requests * 0.95)]
        p99_response_time = sorted(response_times)[int(num_requests * 0.99)]
        
        # Log performance metrics
        print(f"\nGET /proxmox-nodes/ performance metrics:")
        print(f"  Average response time: {avg_response_time:.2f} ms")
        print(f"  Median response time: {median_response_time:.2f} ms")
        print(f"  95th percentile response time: {p95_response_time:.2f} ms")
        print(f"  99th percentile response time: {p99_response_time:.2f} ms")
        
        # Assert performance requirements
        assert avg_response_time < 100, f"Average response time ({avg_response_time:.2f} ms) exceeds 100 ms"
        assert p95_response_time < 200, f"95th percentile response time ({p95_response_time:.2f} ms) exceeds 200 ms"
    
    def test_get_vms_performance(self, mock_auth):
        """Test the performance of the GET /vms endpoint."""
        # Number of requests to make
        num_requests = 100
        
        # Store response times
        response_times = []
        
        # Make requests and measure response time
        for _ in range(num_requests):
            start_time = time.time()
            response = client.get("/vms/")
            end_time = time.time()
            
            # Calculate response time in milliseconds
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            # Check that the response is successful
            assert response.status_code == 200
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[int(num_requests * 0.95)]
        p99_response_time = sorted(response_times)[int(num_requests * 0.99)]
        
        # Log performance metrics
        print(f"\nGET /vms/ performance metrics:")
        print(f"  Average response time: {avg_response_time:.2f} ms")
        print(f"  Median response time: {median_response_time:.2f} ms")
        print(f"  95th percentile response time: {p95_response_time:.2f} ms")
        print(f"  99th percentile response time: {p99_response_time:.2f} ms")
        
        # Assert performance requirements
        assert avg_response_time < 100, f"Average response time ({avg_response_time:.2f} ms) exceeds 100 ms"
        assert p95_response_time < 200, f"95th percentile response time ({p95_response_time:.2f} ms) exceeds 200 ms"
