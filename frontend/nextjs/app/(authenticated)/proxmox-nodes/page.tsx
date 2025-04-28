"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Download, Upload, RefreshCw, Server, Wifi, WifiOff } from "lucide-react"
import { DataTable } from "@/components/data-table"
import { createColumns, ColumnActions } from "./columns"
import { ColumnDef } from "@tanstack/react-table"
import { useEffect, useState } from "react"
import { proxmoxNodesAPI, ProxmoxNodeResponse, ProxmoxNodeStatus } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import { AddNodeDialog } from "./add-node-dialog"
import { WhitelistDialog } from "./whitelist-dialog"
import { ApiKeyDialog } from "./api-key-dialog"

// Node data type for the table
export type ProxmoxNodeTableData = {
  id: string;
  name: string;
  hostname: string;
  port: string;
  status: ProxmoxNodeStatus;
  lastSeen: string;
  apiKey: string;
}

export default function ProxmoxNodesPage() {
  // State for Node data
  const [nodes, setNodes] = useState<ProxmoxNodeTableData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    total: 0,
    connected: 0,
    disconnected: 0,
    error: 0
  })

  // State for dialogs
  const [addNodeOpen, setAddNodeOpen] = useState(false)
  const [whitelistOpen, setWhitelistOpen] = useState(false)
  const [apiKeyOpen, setApiKeyOpen] = useState(false)
  const [selectedNode, setSelectedNode] = useState<ProxmoxNodeTableData | null>(null)
  const [newNodeData, setNewNodeData] = useState<{id: string, name: string, apiKey: string} | null>(null)
  const [isRegeneratingKey, setIsRegeneratingKey] = useState(false)

  const { toast } = useToast()

  // Function to format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never"
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  // Function to load Node data
  const loadNodes = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await proxmoxNodesAPI.getNodes({ limit: 100 })

      // Transform API response to table data format
      const tableData: ProxmoxNodeTableData[] = response.nodes.map(node => ({
        id: node.id.toString(),
        name: node.name,
        hostname: node.hostname,
        port: node.port.toString(),
        status: node.status,
        lastSeen: formatDate(node.last_seen),
        apiKey: node.api_key
      }))

      setNodes(tableData)

      // Calculate stats
      const connectedCount = response.nodes.filter(node => node.status === "connected").length
      const disconnectedCount = response.nodes.filter(node => node.status === "disconnected").length
      const errorCount = response.nodes.filter(node => node.status === "error").length

      setStats({
        total: response.total,
        connected: connectedCount,
        disconnected: disconnectedCount,
        error: errorCount
      })

    } catch (err) {
      console.error("Error loading Proxmox Nodes:", err)
      setError("Failed to load Proxmox nodes")
      toast({
        title: "Error",
        description: "Failed to load Proxmox nodes",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  // Load Nodes on component mount
  useEffect(() => {
    loadNodes()
  }, [])

  // Handle refresh
  const handleRefresh = () => {
    loadNodes()
  }

  // Handle add node
  const handleAddNode = () => {
    setAddNodeOpen(true)
  }

  // Handle node added
  const handleNodeAdded = (node: ProxmoxNodeResponse) => {
    loadNodes()
    setAddNodeOpen(false)

    // Show API key dialog
    setNewNodeData({
      id: node.id.toString(),
      name: node.name,
      apiKey: node.api_key
    })
    setApiKeyOpen(true)
  }

  // Handle refresh node
  const handleRefreshNode = (node: ProxmoxNodeTableData) => {
    loadNodes()
    toast({
      title: "Refreshed",
      description: `Node ${node.name} refreshed successfully`,
    })
  }

  // Handle edit node
  const handleEditNode = (node: ProxmoxNodeTableData) => {
    // For now, just show a toast
    toast({
      title: "Edit Node",
      description: `Editing node ${node.name} is not implemented yet`,
    })
  }

  // Handle regenerate API key
  const handleRegenerateApiKey = async (node: ProxmoxNodeTableData) => {
    try {
      const response = await proxmoxNodesAPI.regenerateApiKey(parseInt(node.id))

      // Show API key dialog
      setNewNodeData({
        id: node.id,
        name: node.name,
        apiKey: response.api_key
      })
      setIsRegeneratingKey(true)
      setApiKeyOpen(true)

      // Refresh nodes list
      loadNodes()
    } catch (error) {
      console.error("Error regenerating API key:", error)
      toast({
        title: "Error",
        description: "Failed to regenerate API key",
        variant: "destructive"
      })
    }
  }

  // Handle whitelist
  const handleWhitelist = (node: ProxmoxNodeTableData) => {
    setSelectedNode(node)
    setWhitelistOpen(true)
  }

  // Handle whitelist updated
  const handleWhitelistUpdated = () => {
    // Just close the dialog, the toast is already shown in the dialog component
    setWhitelistOpen(false)
  }

  // Handle delete node
  const handleDeleteNode = async (node: ProxmoxNodeTableData) => {
    if (confirm(`Are you sure you want to delete node ${node.name}?`)) {
      try {
        await proxmoxNodesAPI.deleteNode(parseInt(node.id))
        loadNodes()
        toast({
          title: "Success",
          description: `Node ${node.name} deleted successfully`,
        })
      } catch (error) {
        console.error("Error deleting node:", error)
        toast({
          title: "Error",
          description: "Failed to delete node",
          variant: "destructive"
        })
      }
    }
  }

  // Define column actions
  const columnActions: ColumnActions = {
    onRefresh: handleRefreshNode,
    onEdit: handleEditNode,
    onRegenerateApiKey: handleRegenerateApiKey,
    onManageWhitelist: handleWhitelist,
    onDelete: handleDeleteNode
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Proxmox Nodes</h1>
        <div className="flex items-center gap-2">
          <Button onClick={handleAddNode}>
            <Plus className="mr-2 h-4 w-4" />
            Add Node
          </Button>
          <Button variant="outline">
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Nodes</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connected</CardTitle>
            <Wifi className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.connected}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Disconnected</CardTitle>
            <WifiOff className="h-4 w-4 text-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.disconnected}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
            <div className="h-2 w-2 rounded-full bg-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.error}</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Proxmox Nodes</CardTitle>
          <CardDescription>Manage your Proxmox host nodes</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <div className="p-4 text-center text-red-500">
              {error}
              <Button
                variant="outline"
                size="sm"
                className="ml-2"
                onClick={handleRefresh}
                disabled={loading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Retry
              </Button>
            </div>
          ) : loading && nodes.length === 0 ? (
            <div className="p-8 text-center">
              <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading Proxmox nodes...</p>
            </div>
          ) : nodes.length === 0 ? (
            <div className="p-8 text-center">
              <Server className="mx-auto mb-4 h-8 w-8 text-muted-foreground" />
              <p className="mb-2 text-sm text-muted-foreground">No Proxmox nodes found</p>
              <Button size="sm" onClick={handleAddNode}>
                <Plus className="mr-2 h-4 w-4" />
                Add your first node
              </Button>
            </div>
          ) : (
            <DataTable
              columns={createColumns(columnActions) as ColumnDef<ProxmoxNodeTableData>[]}
              data={nodes}
              filterColumn="name"
              filterPlaceholder="Filter by node name..."
            />
          )}
        </CardContent>
      </Card>

      {/* Add Node Dialog */}
      <AddNodeDialog
        open={addNodeOpen}
        onOpenChange={setAddNodeOpen}
        onNodeAdded={handleNodeAdded}
      />

      {/* Whitelist Dialog */}
      {selectedNode && (
        <WhitelistDialog
          open={whitelistOpen}
          onOpenChange={setWhitelistOpen}
          node={selectedNode}
          onWhitelistUpdated={handleWhitelistUpdated}
        />
      )}

      {/* API Key Dialog */}
      {newNodeData && (
        <ApiKeyDialog
          open={apiKeyOpen}
          onOpenChange={(open) => {
            setApiKeyOpen(open)
            if (!open) {
              setIsRegeneratingKey(false)
            }
          }}
          nodeId={newNodeData.id}
          nodeName={newNodeData.name}
          apiKey={newNodeData.apiKey}
          isRegenerating={isRegeneratingKey}
        />
      )}
    </div>
  )
}
