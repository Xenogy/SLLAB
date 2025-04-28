# Phase 5: Testing Improvements

## Overview

This phase focuses on increasing test coverage and implementing comprehensive testing strategies to ensure application reliability.

## Key Objectives

1. Increase backend test coverage
2. Add frontend component tests
3. Implement end-to-end tests
4. Add performance tests

## Improvements

### 1. Backend Testing

#### Unit Tests for API Endpoints

- Add unit tests for all API endpoints
- Test both success and error cases

```python
# tests/api/test_proxmox_nodes.py
import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock

client = TestClient(app)

def test_get_proxmox_nodes():
    """Test getting a list of Proxmox nodes."""
    # Mock the repository
    with patch('routers.proxmox_nodes.ProxmoxNodeRepository') as mock_repo:
        # Set up the mock
        mock_instance = MagicMock()
        mock_repo.return_value = mock_instance
        mock_instance.get_nodes.return_value = {
            "nodes": [
                {
                    "id": 1,
                    "name": "pve1",
                    "hostname": "proxmox.example.com",
                    "port": 8006,
                    "status": "connected",
                    "api_key": "test_key",
                    "last_seen": "2023-04-26T12:34:56",
                    "created_at": "2023-04-25T10:20:30",
                    "updated_at": "2023-04-26T12:34:56",
                    "owner_id": 1
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
        
        # Mock the authentication
        with patch('routers.auth.get_current_user', return_value={"id": 1, "role": "admin"}):
            # Make the request
            response = client.get("/proxmox-nodes/")
            
            # Check the response
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["name"] == "pve1"
            
            # Verify the mock was called correctly
            mock_instance.get_nodes.assert_called_once_with(
                limit=10,
                offset=0,
                search=None,
                status=None
            )
```

#### Integration Tests for Database Access

- Test database access with actual database
- Use test database for integration tests

```python
# tests/db/test_proxmox_node_repository.py
import pytest
import os
from db.repositories.proxmox_nodes import ProxmoxNodeRepository

# Use test database
os.environ["DB_NAME"] = "accountdb_test"

@pytest.fixture
def setup_test_data():
    """Set up test data in the database."""
    # Connect to test database
    from db.connection import get_db_connection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM proxmox_nodes")
        
        # Insert test data
        cursor.execute("""
            INSERT INTO proxmox_nodes (
                name, hostname, port, status, api_key, owner_id
            ) VALUES (
                'test_node', 'test.example.com', 8006, 'connected', 'test_key', 1
            )
        """)
        
        conn.commit()
    
    yield
    
    # Clean up
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM proxmox_nodes")
        conn.commit()

def test_get_nodes(setup_test_data):
    """Test getting nodes from the repository."""
    # Create repository with admin user
    repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
    
    # Get nodes
    result = repo.get_nodes()
    
    # Check result
    assert result["total"] == 1
    assert len(result["nodes"]) == 1
    assert result["nodes"][0]["name"] == "test_node"
    assert result["nodes"][0]["hostname"] == "test.example.com"
```

### 2. Frontend Testing

#### Component Tests

- Add tests for all React components
- Test both rendering and interactions

```javascript
// tests/components/ProxmoxNodeCard.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ProxmoxNodeCard } from '@/components/ProxmoxNodeCard';

describe('ProxmoxNodeCard', () => {
  const mockNode = {
    id: '1',
    name: 'pve1',
    hostname: 'proxmox.example.com',
    port: '8006',
    status: 'connected',
    lastSeen: '2023-04-26 12:34:56',
  };
  
  const mockHandlers = {
    onRefresh: jest.fn(),
    onEdit: jest.fn(),
    onDelete: jest.fn(),
  };
  
  it('renders node information correctly', () => {
    render(<ProxmoxNodeCard node={mockNode} {...mockHandlers} />);
    
    expect(screen.getByText('pve1')).toBeInTheDocument();
    expect(screen.getByText('proxmox.example.com:8006')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
    expect(screen.getByText('2023-04-26 12:34:56')).toBeInTheDocument();
  });
  
  it('calls onRefresh when refresh button is clicked', () => {
    render(<ProxmoxNodeCard node={mockNode} {...mockHandlers} />);
    
    const refreshButton = screen.getByLabelText('Refresh');
    fireEvent.click(refreshButton);
    
    expect(mockHandlers.onRefresh).toHaveBeenCalledWith(mockNode);
  });
  
  it('calls onEdit when edit button is clicked', () => {
    render(<ProxmoxNodeCard node={mockNode} {...mockHandlers} />);
    
    const editButton = screen.getByLabelText('Edit');
    fireEvent.click(editButton);
    
    expect(mockHandlers.onEdit).toHaveBeenCalledWith(mockNode);
  });
  
  it('calls onDelete when delete button is clicked and confirmed', () => {
    // Mock window.confirm
    const originalConfirm = window.confirm;
    window.confirm = jest.fn(() => true);
    
    render(<ProxmoxNodeCard node={mockNode} {...mockHandlers} />);
    
    const deleteButton = screen.getByLabelText('Delete');
    fireEvent.click(deleteButton);
    
    expect(window.confirm).toHaveBeenCalled();
    expect(mockHandlers.onDelete).toHaveBeenCalledWith(mockNode);
    
    // Restore window.confirm
    window.confirm = originalConfirm;
  });
});
```

#### Hook Tests

- Test custom hooks
- Test both success and error cases

```javascript
// tests/hooks/useProxmoxNodes.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import { useProxmoxNodes } from '@/hooks/useProxmoxNodes';
import { proxmoxNodesAPI } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  proxmoxNodesAPI: {
    getNodes: jest.fn(),
  },
}));

describe('useProxmoxNodes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('should fetch nodes on mount', async () => {
    // Mock API response
    proxmoxNodesAPI.getNodes.mockResolvedValue({
      nodes: [
        {
          id: 1,
          name: 'pve1',
          hostname: 'proxmox.example.com',
          port: 8006,
          status: 'connected',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    });
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => useProxmoxNodes());
    
    // Initial state
    expect(result.current.loading).toBe(true);
    expect(result.current.nodes).toEqual([]);
    expect(result.current.error).toBeNull();
    
    // Wait for the API call to resolve
    await waitForNextUpdate();
    
    // Check the final state
    expect(result.current.loading).toBe(false);
    expect(result.current.nodes).toHaveLength(1);
    expect(result.current.nodes[0].name).toBe('pve1');
    expect(result.current.error).toBeNull();
    
    // Verify API was called
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ limit: 10 });
  });
  
  it('should handle API errors', async () => {
    // Mock API error
    proxmoxNodesAPI.getNodes.mockRejectedValue(new Error('API error'));
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => useProxmoxNodes());
    
    // Wait for the API call to reject
    await waitForNextUpdate();
    
    // Check the final state
    expect(result.current.loading).toBe(false);
    expect(result.current.nodes).toEqual([]);
    expect(result.current.error).toBe('Failed to load Proxmox nodes');
    
    // Verify API was called
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ limit: 10 });
  });
  
  it('should refresh nodes when refresh is called', async () => {
    // Mock API response
    proxmoxNodesAPI.getNodes.mockResolvedValue({
      nodes: [
        {
          id: 1,
          name: 'pve1',
          hostname: 'proxmox.example.com',
          port: 8006,
          status: 'connected',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    });
    
    // Render the hook
    const { result, waitForNextUpdate } = renderHook(() => useProxmoxNodes());
    
    // Wait for the initial API call to resolve
    await waitForNextUpdate();
    
    // Clear the mock
    proxmoxNodesAPI.getNodes.mockClear();
    
    // Call refresh
    act(() => {
      result.current.refresh();
    });
    
    // Check loading state
    expect(result.current.loading).toBe(true);
    
    // Wait for the refresh API call to resolve
    await waitForNextUpdate();
    
    // Check the final state
    expect(result.current.loading).toBe(false);
    expect(result.current.nodes).toHaveLength(1);
    
    // Verify API was called again
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ limit: 10 });
  });
});
```

### 3. End-to-End Testing

#### Critical Workflow Tests

- Test critical user workflows
- Use Cypress for end-to-end testing

```javascript
// cypress/integration/proxmox_nodes.spec.js
describe('Proxmox Nodes', () => {
  beforeEach(() => {
    // Log in
    cy.login('admin', 'password');
    
    // Visit the Proxmox nodes page
    cy.visit('/proxmox-nodes');
  });
  
  it('should display a list of Proxmox nodes', () => {
    // Check the page title
    cy.contains('h1', 'Proxmox Nodes').should('be.visible');
    
    // Check the node list
    cy.get('[data-testid="node-card"]').should('have.length.at.least', 1);
  });
  
  it('should add a new Proxmox node', () => {
    // Click the add node button
    cy.contains('button', 'Add Node').click();
    
    // Fill the form
    cy.get('[name="name"]').type('test-node');
    cy.get('[name="hostname"]').type('test.example.com');
    cy.get('[name="port"]').clear().type('8006');
    
    // Submit the form
    cy.contains('button', 'Add Node').click();
    
    // Check the API key dialog
    cy.contains('API Key for test-node').should('be.visible');
    cy.contains('button', 'Close').click();
    
    // Check the new node is in the list
    cy.contains('[data-testid="node-card"]', 'test-node').should('be.visible');
  });
  
  it('should edit a Proxmox node', () => {
    // Find the first node
    cy.get('[data-testid="node-card"]').first().as('firstNode');
    
    // Click the edit button
    cy.get('@firstNode').find('[aria-label="Edit"]').click();
    
    // Update the name
    cy.get('[name="name"]').clear().type('updated-node');
    
    // Submit the form
    cy.contains('button', 'Save Changes').click();
    
    // Check the node was updated
    cy.contains('[data-testid="node-card"]', 'updated-node').should('be.visible');
  });
  
  it('should delete a Proxmox node', () => {
    // Find the first node
    cy.get('[data-testid="node-card"]').first().as('firstNode');
    
    // Get the node name
    cy.get('@firstNode').find('[data-testid="node-name"]').invoke('text').as('nodeName');
    
    // Click the delete button
    cy.get('@firstNode').find('[aria-label="Delete"]').click();
    
    // Confirm deletion
    cy.on('window:confirm', () => true);
    
    // Check the node was deleted
    cy.get('@nodeName').then((nodeName) => {
      cy.contains('[data-testid="node-card"]', nodeName).should('not.exist');
    });
  });
});
```

### 4. Performance Testing

#### API Performance Tests

- Test API endpoint performance
- Set performance benchmarks

```javascript
// tests/performance/api.test.js
const autocannon = require('autocannon');
const { promisify } = require('util');

const autocannonAsync = promisify(autocannon);

describe('API Performance', () => {
  it('should handle high load on GET /proxmox-nodes', async () => {
    const result = await autocannonAsync({
      url: 'http://localhost:8000/proxmox-nodes',
      connections: 100,
      duration: 10,
      headers: {
        'Authorization': 'Bearer ' + process.env.TEST_TOKEN,
      },
    });
    
    console.log(result);
    
    // Check performance metrics
    expect(result.errors).toBe(0);
    expect(result.timeouts).toBe(0);
    expect(result.non2xx).toBe(0);
    expect(result.latency.p99).toBeLessThan(500); // 99th percentile latency < 500ms
    expect(result.requests.average).toBeGreaterThan(100); // > 100 requests per second
  });
});
```

#### Database Performance Tests

- Test database query performance
- Optimize slow queries

```python
# tests/performance/db.py
import time
import pytest
from db.repositories.proxmox_nodes import ProxmoxNodeRepository

def test_get_nodes_performance():
    """Test the performance of getting nodes."""
    # Create repository with admin user
    repo = ProxmoxNodeRepository(user_id=1, user_role="admin")
    
    # Measure execution time
    start_time = time.time()
    result = repo.get_nodes(limit=100)
    end_time = time.time()
    
    # Calculate execution time
    execution_time = end_time - start_time
    
    # Check performance
    assert execution_time < 0.1  # Less than 100ms
    
    # Log performance metrics
    print(f"get_nodes execution time: {execution_time:.4f} seconds")
    print(f"Retrieved {result['total']} nodes")
```

## Implementation Steps

1. Set up testing infrastructure
   - Configure test runners
   - Set up test database
   - Create test utilities

2. Implement backend tests
   - Add unit tests for API endpoints
   - Add integration tests for database access

3. Implement frontend tests
   - Add component tests
   - Add hook tests

4. Implement end-to-end tests
   - Set up Cypress
   - Add tests for critical workflows

5. Implement performance tests
   - Add API performance tests
   - Add database performance tests

## Expected Outcomes

- Increased test coverage
- More reliable application
- Faster detection of regressions
- Better performance monitoring
