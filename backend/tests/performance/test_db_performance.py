"""
Performance tests for database operations.

This module contains tests to measure the performance of database operations.
"""

import pytest
import time
import statistics
from db.repositories.proxmox_nodes import ProxmoxNodeRepository
from db.repositories.vms import VMRepository

@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations."""
    
    def test_get_nodes_performance(self):
        """Test the performance of getting nodes from the repository."""
        # Create repository with admin user
        repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
        
        # Number of queries to make
        num_queries = 100
        
        # Store execution times
        execution_times = []
        
        # Make queries and measure execution time
        for _ in range(num_queries):
            start_time = time.time()
            result = repo.get_nodes(limit=100)
            end_time = time.time()
            
            # Calculate execution time in milliseconds
            execution_time = (end_time - start_time) * 1000
            execution_times.append(execution_time)
        
        # Calculate statistics
        avg_execution_time = statistics.mean(execution_times)
        median_execution_time = statistics.median(execution_times)
        p95_execution_time = sorted(execution_times)[int(num_queries * 0.95)]
        p99_execution_time = sorted(execution_times)[int(num_queries * 0.99)]
        
        # Log performance metrics
        print(f"\nProxmoxNodeRepository.get_nodes() performance metrics:")
        print(f"  Average execution time: {avg_execution_time:.2f} ms")
        print(f"  Median execution time: {median_execution_time:.2f} ms")
        print(f"  95th percentile execution time: {p95_execution_time:.2f} ms")
        print(f"  99th percentile execution time: {p99_execution_time:.2f} ms")
        print(f"  Retrieved {result['total']} nodes")
        
        # Assert performance requirements
        assert avg_execution_time < 50, f"Average execution time ({avg_execution_time:.2f} ms) exceeds 50 ms"
        assert p95_execution_time < 100, f"95th percentile execution time ({p95_execution_time:.2f} ms) exceeds 100 ms"
    
    def test_get_vms_performance(self):
        """Test the performance of getting VMs from the repository."""
        # Create repository with admin user
        repo = VMRepository(user_id=1, user_role="admin")
        
        # Number of queries to make
        num_queries = 100
        
        # Store execution times
        execution_times = []
        
        # Make queries and measure execution time
        for _ in range(num_queries):
            start_time = time.time()
            result = repo.get_vms(limit=100)
            end_time = time.time()
            
            # Calculate execution time in milliseconds
            execution_time = (end_time - start_time) * 1000
            execution_times.append(execution_time)
        
        # Calculate statistics
        avg_execution_time = statistics.mean(execution_times)
        median_execution_time = statistics.median(execution_times)
        p95_execution_time = sorted(execution_times)[int(num_queries * 0.95)]
        p99_execution_time = sorted(execution_times)[int(num_queries * 0.99)]
        
        # Log performance metrics
        print(f"\nVMRepository.get_vms() performance metrics:")
        print(f"  Average execution time: {avg_execution_time:.2f} ms")
        print(f"  Median execution time: {median_execution_time:.2f} ms")
        print(f"  95th percentile execution time: {p95_execution_time:.2f} ms")
        print(f"  99th percentile execution time: {p99_execution_time:.2f} ms")
        print(f"  Retrieved {result['total']} VMs")
        
        # Assert performance requirements
        assert avg_execution_time < 50, f"Average execution time ({avg_execution_time:.2f} ms) exceeds 50 ms"
        assert p95_execution_time < 100, f"95th percentile execution time ({p95_execution_time:.2f} ms) exceeds 100 ms"
