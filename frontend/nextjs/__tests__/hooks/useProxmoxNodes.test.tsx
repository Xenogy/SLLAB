import { renderHook, act } from '@testing-library/react'
import { useProxmoxNodes } from '@/hooks/use-proxmox-nodes'
import { proxmoxNodesAPI } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  proxmoxNodesAPI: {
    getNodes: jest.fn(),
  },
}))

describe('useProxmoxNodes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('should fetch nodes on mount', async () => {
    // Mock API response
    (proxmoxNodesAPI.getNodes as jest.Mock).mockResolvedValue({
      nodes: [
        {
          id: 1,
          name: 'pve1',
          hostname: 'proxmox.example.com',
          port: 8006,
          status: 'connected',
          api_key: 'test_key',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    })
    
    // Render the hook
    const { result, rerender } = renderHook(() => useProxmoxNodes())
    
    // Initial state
    expect(result.current.loading).toBe(true)
    expect(result.current.nodes).toEqual([])
    expect(result.current.error).toBeNull()
    
    // Wait for the API call to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Check the final state
    expect(result.current.loading).toBe(false)
    expect(result.current.nodes).toHaveLength(1)
    expect(result.current.nodes[0].name).toBe('pve1')
    expect(result.current.error).toBeNull()
    
    // Verify API was called
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ limit: 10 })
  })
  
  it('should handle API errors', async () => {
    // Mock API error
    (proxmoxNodesAPI.getNodes as jest.Mock).mockRejectedValue(new Error('API error'))
    
    // Render the hook
    const { result } = renderHook(() => useProxmoxNodes())
    
    // Wait for the API call to reject
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Check the final state
    expect(result.current.loading).toBe(false)
    expect(result.current.nodes).toEqual([])
    expect(result.current.error).toBe('Failed to load Proxmox nodes')
    
    // Verify API was called
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ limit: 10 })
  })
  
  it('should refresh nodes when refresh is called', async () => {
    // Mock API response
    (proxmoxNodesAPI.getNodes as jest.Mock).mockResolvedValue({
      nodes: [
        {
          id: 1,
          name: 'pve1',
          hostname: 'proxmox.example.com',
          port: 8006,
          status: 'connected',
          api_key: 'test_key',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
      ],
      total: 1,
      limit: 10,
      offset: 0,
    })
    
    // Render the hook
    const { result } = renderHook(() => useProxmoxNodes())
    
    // Wait for the initial API call to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Clear the mock
    (proxmoxNodesAPI.getNodes as jest.Mock).mockClear()
    
    // Call refresh
    act(() => {
      result.current.refresh()
    })
    
    // Check loading state
    expect(result.current.loading).toBe(true)
    
    // Wait for the refresh API call to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Check the final state
    expect(result.current.loading).toBe(false)
    expect(result.current.nodes).toHaveLength(1)
    
    // Verify API was called again
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ limit: 10 })
  })
  
  it('should update params when updateParams is called', async () => {
    // Mock API response
    (proxmoxNodesAPI.getNodes as jest.Mock).mockResolvedValue({
      nodes: [],
      total: 0,
      limit: 10,
      offset: 0,
    })
    
    // Render the hook
    const { result } = renderHook(() => useProxmoxNodes())
    
    // Wait for the initial API call to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Clear the mock
    (proxmoxNodesAPI.getNodes as jest.Mock).mockClear()
    
    // Update params
    act(() => {
      result.current.updateParams({ limit: 20, search: 'test' })
    })
    
    // Wait for the API call with new params to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Verify API was called with new params
    expect(proxmoxNodesAPI.getNodes).toHaveBeenCalledWith({ 
      limit: 20, 
      search: 'test' 
    })
  })
  
  it('should calculate stats correctly', async () => {
    // Mock API response with different statuses
    (proxmoxNodesAPI.getNodes as jest.Mock).mockResolvedValue({
      nodes: [
        {
          id: 1,
          name: 'pve1',
          hostname: 'proxmox1.example.com',
          port: 8006,
          status: 'connected',
          api_key: 'test_key1',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
        {
          id: 2,
          name: 'pve2',
          hostname: 'proxmox2.example.com',
          port: 8006,
          status: 'disconnected',
          api_key: 'test_key2',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
        {
          id: 3,
          name: 'pve3',
          hostname: 'proxmox3.example.com',
          port: 8006,
          status: 'error',
          api_key: 'test_key3',
          last_seen: '2023-04-26T12:34:56',
          created_at: '2023-04-25T10:20:30',
          updated_at: '2023-04-26T12:34:56',
          owner_id: 1,
        },
      ],
      total: 3,
      limit: 10,
      offset: 0,
    })
    
    // Render the hook
    const { result } = renderHook(() => useProxmoxNodes())
    
    // Wait for the API call to resolve
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
    
    // Check the stats
    expect(result.current.stats).toEqual({
      total: 3,
      connected: 1,
      disconnected: 1,
      error: 1
    })
  })
})
