"use client"

import { useState, useEffect, useCallback } from 'react'
import { proxmoxNodesAPI, ProxmoxNodeResponse, ProxmoxNodeListParams } from '@/lib/api'

export type ProxmoxNodeTableData = {
  id: string;
  name: string;
  hostname: string;
  port: string;
  status: string;
  lastSeen: string | null;
  apiKey: string;
  ownerId: number;
}

export function useProxmoxNodes(initialParams: ProxmoxNodeListParams = { limit: 10 }) {
  const [nodes, setNodes] = useState<ProxmoxNodeTableData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [params, setParams] = useState<ProxmoxNodeListParams>(initialParams)
  const [stats, setStats] = useState({
    total: 0,
    connected: 0,
    disconnected: 0,
    error: 0
  })

  const mapNodeToTableData = (node: ProxmoxNodeResponse): ProxmoxNodeTableData => ({
    id: node.id.toString(),
    name: node.name,
    hostname: node.hostname,
    port: node.port.toString(),
    status: node.status,
    lastSeen: node.last_seen,
    apiKey: node.api_key,
    ownerId: node.owner_id
  })

  const calculateStats = (nodes: ProxmoxNodeResponse[]) => {
    const connected = nodes.filter(node => node.status === 'connected').length
    const disconnected = nodes.filter(node => node.status === 'disconnected').length
    const error = nodes.filter(node => node.status === 'error').length

    return {
      total: nodes.length,
      connected,
      disconnected,
      error
    }
  }

  const loadNodes = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await proxmoxNodesAPI.getNodes(params)
      
      // Map API response to table data
      const tableData = response.nodes.map(mapNodeToTableData)
      
      // Update state
      setNodes(tableData)
      setStats(calculateStats(response.nodes))
    } catch (err) {
      console.error('Error loading Proxmox nodes:', err)
      setError('Failed to load Proxmox nodes')
    } finally {
      setLoading(false)
    }
  }, [params])

  // Load nodes on mount and when params change
  useEffect(() => {
    loadNodes()
  }, [loadNodes])

  const refresh = () => {
    loadNodes()
  }

  const updateParams = (newParams: Partial<ProxmoxNodeListParams>) => {
    setParams(prev => ({ ...prev, ...newParams }))
  }

  return {
    nodes,
    loading,
    error,
    stats,
    refresh,
    updateParams
  }
}
