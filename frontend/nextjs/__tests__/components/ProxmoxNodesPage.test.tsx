import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import ProxmoxNodesPage from '@/app/(authenticated)/proxmox-nodes/page';

// Mock the API response
const server = setupServer(
  rest.get('*/proxmox-nodes', (req, res, ctx) => {
    return res(
      ctx.json({
        nodes: [
          {
            id: 1,
            name: 'test-node',
            hostname: 'test.example.com',
            port: 8006,
            status: 'connected',
            api_key: 'test-key',
            last_seen: '2023-04-26T12:34:56',
            created_at: '2023-04-25T10:20:30',
            updated_at: '2023-04-26T12:34:56',
            owner_id: 1
          }
        ],
        total: 1,
        limit: 10,
        offset: 0
      })
    );
  })
);

// Mock the components that are not relevant to this test
jest.mock('@/components/data-table', () => ({
  DataTable: ({ columns, data }) => (
    <div data-testid="data-table">
      <div>Columns: {columns.length}</div>
      <div>Rows: {data.length}</div>
      {data.map((row) => (
        <div key={row.id} data-testid="node-row">
          {row.name} - {row.hostname}:{row.port} - {row.status}
        </div>
      ))}
    </div>
  ),
}));

jest.mock('./add-node-dialog', () => ({
  AddNodeDialog: ({ open, onOpenChange, onNodeAdded }) => (
    <div data-testid="add-node-dialog">
      {open ? 'Open' : 'Closed'}
      <button onClick={() => onNodeAdded({ id: 2, name: 'new-node', api_key: 'new-key' })}>
        Add Node
      </button>
    </div>
  ),
}));

jest.mock('@/components/ui/toast', () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Start the server before all tests
beforeAll(() => server.listen());
// Reset any request handlers that we may add during the tests
afterEach(() => server.resetHandlers());
// Clean up after the tests are finished
afterAll(() => server.close());

describe('ProxmoxNodesPage', () => {
  it('renders the page title', () => {
    render(<ProxmoxNodesPage />);
    expect(screen.getByText('Proxmox Nodes')).toBeInTheDocument();
  });

  it('loads and displays nodes', async () => {
    render(<ProxmoxNodesPage />);
    
    // Initially shows loading state
    expect(screen.getByText('Loading Proxmox nodes...')).toBeInTheDocument();
    
    // Wait for the nodes to load
    await waitFor(() => {
      expect(screen.getByTestId('data-table')).toBeInTheDocument();
    });
    
    // Check that the node data is displayed
    expect(screen.getByTestId('node-row')).toHaveTextContent('test-node - test.example.com:8006 - connected');
  });

  it('handles API errors', async () => {
    // Mock an API error
    server.use(
      rest.get('*/proxmox-nodes', (req, res, ctx) => {
        return res(ctx.status(500), ctx.json({ detail: 'Server error' }));
      })
    );
    
    render(<ProxmoxNodesPage />);
    
    // Wait for the error message
    await waitFor(() => {
      expect(screen.getByText(/Failed to load Proxmox nodes/)).toBeInTheDocument();
    });
    
    // Check that the retry button is displayed
    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();
    
    // Reset the mock to return successful response
    server.use(
      rest.get('*/proxmox-nodes', (req, res, ctx) => {
        return res(
          ctx.json({
            nodes: [
              {
                id: 1,
                name: 'test-node',
                hostname: 'test.example.com',
                port: 8006,
                status: 'connected',
                api_key: 'test-key',
                last_seen: '2023-04-26T12:34:56',
                created_at: '2023-04-25T10:20:30',
                updated_at: '2023-04-26T12:34:56',
                owner_id: 1
              }
            ],
            total: 1,
            limit: 10,
            offset: 0
          })
        );
      })
    );
    
    // Click the retry button
    fireEvent.click(retryButton);
    
    // Wait for the nodes to load
    await waitFor(() => {
      expect(screen.getByTestId('data-table')).toBeInTheDocument();
    });
  });

  it('opens the add node dialog when the add button is clicked', () => {
    render(<ProxmoxNodesPage />);
    
    // Click the add node button
    fireEvent.click(screen.getByText('Add Node'));
    
    // Check that the dialog is open
    expect(screen.getByTestId('add-node-dialog')).toHaveTextContent('Open');
  });
});
