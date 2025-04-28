"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Download, Upload, RefreshCw, Server, Clock, Star, MoreHorizontal, Edit, Trash, Play, Pause, Terminal, RotateCw } from "lucide-react"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { DataTable } from "@/components/data-table"
import { Badge } from "@/components/ui/badge"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { createColumns } from "./columns"
import { ColumnDef } from "@tanstack/react-table"
import { useEffect, useState, useMemo } from "react"
import { vmsAPI, VMResponse, VMStatus, proxmoxNodesAPI, ProxmoxNodeResponse } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

// For debugging
console.log("createColumns imported:", createColumns);

// VM data type for the table
export type VMTableData = {
  id: string;
  name: string;
  status: VMStatus;
  ip: string;
  cpu: string;
  memory: string;
  uptime: string;
  proxmox_node_id?: number;
  proxmox_node?: string;
  source?: 'database' | 'proxmox';
  whitelist?: boolean;
}

export default function VMsPage() {
  // State for VM data
  const [vms, setVms] = useState<VMTableData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({
    total: 0,
    running: 0,
    stopped: 0,
    error: 0
  })
  const [nodes, setNodes] = useState<ProxmoxNodeResponse[]>([])
  const [showProxmoxVMs, setShowProxmoxVMs] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null)
  const [syncingNodes, setSyncingNodes] = useState<number[]>([])

  const { toast } = useToast()

  // Function to load Proxmox nodes
  const loadNodes = async () => {
    try {
      const response = await proxmoxNodesAPI.getNodes({ status: 'connected' })
      setNodes(response.nodes)
      return response.nodes
    } catch (err) {
      console.error("Error loading Proxmox nodes:", err)
      return []
    }
  }

  // Function to transform VM data to table format
  const transformVMToTableData = (vm: VMResponse, source: 'database' | 'proxmox' = 'database'): VMTableData => ({
    id: vm.id.toString(),
    name: vm.name,
    status: vm.status,
    ip: vm.ip_address || "N/A",
    cpu: vm.cpu_cores ? `${Math.floor(Math.random() * 100)}%` : "N/A",
    memory: vm.memory_mb ? `${(vm.memory_mb / 1024).toFixed(1)}GB/${(vm.memory_mb / 1024).toFixed(1)}GB` : "N/A",
    uptime: vm.status === "running" ? `${Math.floor(Math.random() * 5)}d ${Math.floor(Math.random() * 24)}h ${Math.floor(Math.random() * 60)}m` : "0d 0h 0m",
    proxmox_node_id: vm.proxmox_node_id,
    proxmox_node: vm.proxmox_node,
    source: source,
    whitelist: source === 'database' // Assume database VMs are whitelisted
  })

  // Function to load VM data
  const loadVMs = async () => {
    console.log("Loading VMs...")
    setLoading(true)
    setError(null)

    try {
      // Load VMs from database
      const dbResponse = await vmsAPI.getVMs({ limit: 100 })
      console.log("DB VMs response:", dbResponse)
      let allVMs: VMTableData[] = dbResponse.vms.map(vm => {
        console.log("Transforming VM:", vm)
        return transformVMToTableData(vm, 'database')
      })

      // Load Proxmox nodes if needed
      let proxmoxNodes = nodes
      if (proxmoxNodes.length === 0) {
        proxmoxNodes = await loadNodes()
      }

      // Load VMs from Proxmox nodes if enabled
      if (showProxmoxVMs && proxmoxNodes.length > 0) {
        try {
          const proxmoxVMsResponse = await vmsAPI.getProxmoxVMs()

          // Filter out VMs that are already in the database (by VMID and node)
          const existingVMKeys = new Set(
            dbResponse.vms.map(vm => `${vm.vmid}-${vm.proxmox_node}`)
          )

          const newProxmoxVMs = proxmoxVMsResponse.filter(
            vm => !existingVMKeys.has(`${vm.vmid}-${vm.proxmox_node}`)
          )

          // Add new VMs from Proxmox to the list
          allVMs = [...allVMs, ...newProxmoxVMs.map(vm => transformVMToTableData(vm, 'proxmox'))]
        } catch (proxmoxErr) {
          console.error("Error loading Proxmox VMs:", proxmoxErr)
          // Don't fail completely if Proxmox VMs can't be loaded
          toast({
            title: "Warning",
            description: "Could not load VMs from Proxmox nodes",
            variant: "default"
          })
        }
      }

      setVms(allVMs)

      // Calculate stats
      const runningCount = allVMs.filter(vm => vm.status === "running").length
      const stoppedCount = allVMs.filter(vm => vm.status === "stopped").length
      const errorCount = allVMs.filter(vm => vm.status === "error").length

      setStats({
        total: allVMs.length,
        running: runningCount,
        stopped: stoppedCount,
        error: errorCount
      })

    } catch (err) {
      console.error("Error loading VMs:", err)
      setError("Failed to load virtual machines")
      toast({
        title: "Error",
        description: "Failed to load virtual machines",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  // Load nodes on component mount
  useEffect(() => {
    console.log("Loading nodes...")
    loadNodes().then(loadedNodes => {
      console.log("Nodes loaded:", loadedNodes)
    })
  }, [])

  // Load VMs when showProxmoxVMs changes or on component mount
  useEffect(() => {
    loadVMs()
  }, [showProxmoxVMs])

  // Handle auto-refresh
  useEffect(() => {
    // Set up auto-refresh if enabled
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadVMs()
      }, 30000) // Refresh every 30 seconds

      setRefreshInterval(interval)

      // Clean up interval on unmount or when autoRefresh changes
      return () => {
        clearInterval(interval)
        setRefreshInterval(null)
      }
    } else if (refreshInterval) {
      // Clear existing interval if auto-refresh is disabled
      clearInterval(refreshInterval)
      setRefreshInterval(null)
    }
  }, [autoRefresh]) // Re-run when autoRefresh changes

  // Handle refresh
  const handleRefresh = () => {
    loadVMs()
  }

  // Handle sync
  const handleSync = async (nodeId: number) => {
    if (syncingNodes.includes(nodeId)) {
      return // Already syncing
    }

    try {
      setSyncingNodes(prev => [...prev, nodeId])

      const response = await proxmoxNodesAPI.syncNodeVMs(nodeId)

      toast({
        title: "Sync started",
        description: response.message,
        variant: "default"
      })

      // Wait a bit and then refresh the VMs
      setTimeout(() => {
        loadVMs()
        setSyncingNodes(prev => prev.filter(id => id !== nodeId))
      }, 5000)
    } catch (err) {
      console.error("Error syncing VMs:", err)
      toast({
        title: "Error",
        description: "Failed to sync virtual machines",
        variant: "destructive"
      })
      setSyncingNodes(prev => prev.filter(id => id !== nodeId))
    }
  }

  // Handle whitelist toggle
  const updateVMWhitelist = async (vmId: string, checked: boolean) => {
    try {
      // Find the VM in the list
      const vm = vms.find(vm => vm.id === vmId)
      if (!vm) {
        toast({
          title: "Error",
          description: "Cannot find VM with ID " + vmId,
          variant: "destructive"
        })
        return
      }

      // Check if we have either proxmox_node or proxmox_node_id
      if (!vm.proxmox_node && !vm.proxmox_node_id) {
        toast({
          title: "Error",
          description: "Cannot update whitelist for this VM - no Proxmox node information",
          variant: "destructive"
        })
        return
      }

      // Find the node for this VM
      let node: ProxmoxNodeResponse | undefined;

      if (vm.proxmox_node_id) {
        // If we have the node ID, use it directly
        node = nodes.find(node => node.id === vm.proxmox_node_id);
      } else if (vm.proxmox_node) {
        // Fallback to using the node name
        node = nodes.find(node => node.name === vm.proxmox_node);
      }

      if (!node) {
        toast({
          title: "Error",
          description: "Cannot find Proxmox node for this VM",
          variant: "destructive"
        })
        return
      }

      // Get current whitelist
      const whitelistResponse = await proxmoxNodesAPI.getNodeWhitelist(node.id)
      const currentWhitelist = whitelistResponse.vmids

      // Update whitelist based on checked state
      let newWhitelist: number[]
      const vmidNumber = parseInt(vm.id)

      if (checked) {
        // Add to whitelist if not already there
        newWhitelist = [...currentWhitelist, vmidNumber]
      } else {
        // Remove from whitelist
        newWhitelist = currentWhitelist.filter(id => id !== vmidNumber)
      }

      // Remove duplicates
      newWhitelist = [...new Set(newWhitelist)]

      // Update whitelist on server
      await proxmoxNodesAPI.setVMIDWhitelist({
        node_id: node.id,
        vmids: newWhitelist
      })

      // Update local state
      setVms(vms.map(v =>
        v.id === vmId
          ? { ...v, whitelist: checked }
          : v
      ))

      toast({
        title: "Whitelist updated",
        description: `VM ${vm.name} ${checked ? 'added to' : 'removed from'} whitelist`,
        variant: "default"
      })

    } catch (err) {
      console.error("Error updating whitelist:", err)
      toast({
        title: "Error",
        description: "Failed to update whitelist",
        variant: "destructive"
      })
    }
  }
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Virtual Machines</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="show-proxmox"
              checked={showProxmoxVMs}
              onCheckedChange={setShowProxmoxVMs}
            />
            <Label htmlFor="show-proxmox">Show Proxmox VMs</Label>
          </div>

          <div className="flex items-center space-x-2">
            <Switch
              id="auto-refresh"
              checked={autoRefresh}
              onCheckedChange={setAutoRefresh}
            />
            <Label htmlFor="auto-refresh" className="flex items-center">
              <Clock className="mr-1 h-4 w-4" />
              Auto-refresh
            </Label>
          </div>

          <div className="flex items-center gap-2">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New VM
            </Button>
            <Button variant="outline">
              <Upload className="mr-2 h-4 w-4" />
              Import
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            {nodes.length > 0 && (
              <div className="flex items-center gap-1">
                {nodes.map(node => (
                  <Button
                    key={node.id}
                    variant="outline"
                    size="sm"
                    onClick={() => handleSync(node.id)}
                    disabled={syncingNodes.includes(node.id)}
                  >
                    <RotateCw className={`mr-1 h-3 w-3 ${syncingNodes.includes(node.id) ? 'animate-spin' : ''}`} />
                    Sync {node.name}
                  </Button>
                ))}
              </div>
            )}
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
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total VMs</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <div className="h-2 w-2 rounded-full bg-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.running}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stopped</CardTitle>
            <div className="h-2 w-2 rounded-full bg-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.stopped}</div>
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
          <CardTitle>Virtual Machines</CardTitle>
          <CardDescription>Manage your virtual machines</CardDescription>
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
          ) : loading && vms.length === 0 ? (
            <div className="p-8 text-center">
              <RefreshCw className="mx-auto mb-4 h-8 w-8 animate-spin text-muted-foreground" />
              <p className="text-sm text-muted-foreground">Loading virtual machines...</p>
            </div>
          ) : vms.length === 0 ? (
            <div className="p-8 text-center">
              <Server className="mx-auto mb-4 h-8 w-8 text-muted-foreground" />
              <p className="mb-2 text-sm text-muted-foreground">No virtual machines found</p>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Create your first VM
              </Button>
            </div>
          ) : (
            <>
              {/* Debug info */}
              {console.log("About to render DataTable")}
              {console.log("createColumns:", createColumns)}
              {console.log("updateVMWhitelist:", updateVMWhitelist)}
              {console.log("vms:", vms)}

              {/* Create columns directly without useMemo */}
              {(() => {
                console.log("Creating columns directly");
                // Define columns inline
                const columns: ColumnDef<VMTableData>[] = [
                  {
                    accessorKey: "name",
                    header: "Name",
                  },
                  {
                    accessorKey: "status",
                    header: "Status",
                    cell: ({ row }) => {
                      const status = row.getValue("status") as string;
                      return (
                        <Badge variant={status === "running" ? "default" : status === "stopped" ? "secondary" : "destructive"}>
                          {status}
                        </Badge>
                      );
                    },
                  },
                  {
                    accessorKey: "ip",
                    header: "IP Address",
                  },
                  {
                    accessorKey: "cpu",
                    header: "CPU Usage",
                  },
                  {
                    accessorKey: "memory",
                    header: "Memory",
                  },
                  {
                    accessorKey: "uptime",
                    header: "Uptime",
                  },
                  {
                    accessorKey: "proxmox_node",
                    header: "Proxmox Node",
                    cell: ({ row }) => {
                      const node = row.getValue("proxmox_node") as string | undefined;
                      const source = row.original.source;
                      if (!node) return <span className="text-muted-foreground">N/A</span>;
                      return (
                        <div className="flex items-center">
                          <Server className="mr-2 h-4 w-4 text-muted-foreground" />
                          <span>{node}</span>
                          {source === 'proxmox' && (
                            <Badge variant="outline" className="ml-2 text-xs">
                              Live
                            </Badge>
                          )}
                        </div>
                      );
                    },
                  },
                  {
                    accessorKey: "whitelist",
                    header: "Whitelist",
                    cell: ({ row }) => {
                      const whitelist = row.getValue("whitelist") as boolean || false;
                      const vm = row.original;
                      return (
                        <div className="flex items-center">
                          {whitelist ? (
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                          ) : (
                            <Star className="h-4 w-4 text-muted-foreground" />
                          )}
                          <Switch
                            checked={whitelist}
                            className="ml-2"
                            onCheckedChange={(checked) => updateVMWhitelist(vm.id, checked)}
                          />
                        </div>
                      );
                    },
                  },
                  {
                    id: "actions",
                    cell: ({ row }) => {
                      const vm = row.original;
                      const isRunning = vm.status === "running";
                      return (
                        <div className="flex items-center justify-end gap-2">
                          <Button variant="ghost" size="icon" className={isRunning ? "text-amber-500" : "text-emerald-500"}>
                            {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                          </Button>
                          <Button variant="ghost" size="icon">
                            <RefreshCw className="h-4 w-4" />
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuItem>
                                <Terminal className="mr-2 h-4 w-4" />
                                Console
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive">
                                <Trash className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      );
                    },
                  },
                ];

                return (
                  <DataTable
                    columns={columns}
                    data={vms}
                    filterColumn="name"
                    filterPlaceholder="Filter by VM name..."
                  />
                );
              })()}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
