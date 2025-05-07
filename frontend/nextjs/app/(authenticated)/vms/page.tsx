"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Download, Upload, RefreshCw, Server, Clock, Star, MoreHorizontal, Edit, Trash, Play, Pause, Terminal, RotateCw, ChevronDown } from "lucide-react"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { createColumns } from "./columns"
import { ColumnDef } from "@tanstack/react-table"
import { useEffect, useState, useMemo } from "react"
import { vmsAPI, VMResponse, VMStatus, proxmoxNodesAPI, ProxmoxNodeResponse, windowsVMAgentAPI, WindowsVMAgentResponse, WindowsVMAgentStatus } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Textarea } from "@/components/ui/textarea"

// Helper function to format uptime from seconds to days, hours, minutes
const formatUptime = (seconds: number): string => {
  if (!seconds) return "0d 0h 0m"

  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  return `${days}d ${hours}h ${minutes}m`
}

// For debugging
console.log("createColumns imported:", createColumns);

// VM data type for the table
export type VMTableData = {
  id: string;
  name: string;
  status: VMStatus;
  ip: string;
  cpu: string;
  cpu_cores: string;
  memory: string;
  uptime: string;
  proxmox_node_id?: number;
  proxmox_node?: string;
  source?: 'database' | 'proxmox';
  whitelist?: boolean;
  agent_status?: WindowsVMAgentStatus;
  agent_last_seen?: string | null;
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
  const [refreshTimeout, setRefreshTimeout] = useState(30) // Default 30 seconds
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
    cpu: vm.status === "running"
      ? (vm.cpu_usage_percent !== null
        ? `${vm.cpu_usage_percent}%`
        : (vm.cpu_cores ? "0%" : "N/A"))
      : "0%",
    cpu_cores: vm.cpu_cores ? `${vm.cpu_cores}` : "N/A",
    memory: vm.memory_mb ? `${(vm.memory_mb / 1024).toFixed(1)}GB/${(vm.memory_mb / 1024).toFixed(1)}GB` : "N/A",
    // Format uptime from seconds to days, hours, minutes
    uptime: vm.status === "running" && vm.uptime_seconds
      ? formatUptime(vm.uptime_seconds)
      : "0d 0h 0m",
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

      // Fetch Windows VM agent status for each VM
      for (const vm of allVMs) {
        try {
          // Only check agent status for database VMs (not Proxmox live VMs)
          if (vm.source === 'database') {
            const agentStatus = await windowsVMAgentAPI.getAgentStatus(vm.id)
            if (agentStatus) {
              vm.agent_status = agentStatus.status
              vm.agent_last_seen = agentStatus.last_seen
            }
          }
        } catch (err) {
          // If agent not found or error, leave agent_status undefined
          console.log(`No agent found for VM ${vm.id}`)
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
      }, refreshTimeout * 1000) // Convert seconds to milliseconds

      setRefreshInterval(interval)

      // Clean up interval on unmount or when autoRefresh or refreshTimeout changes
      return () => {
        clearInterval(interval)
        setRefreshInterval(null)
      }
    } else if (refreshInterval) {
      // Clear existing interval if auto-refresh is disabled
      clearInterval(refreshInterval)
      setRefreshInterval(null)
    }
  }, [autoRefresh, refreshTimeout]) // Re-run when autoRefresh or refreshTimeout changes

  // Handle refresh
  const handleRefresh = () => {
    loadVMs()
  }

  // Handle sync - temporarily disabled
  const handleSync = async (nodeId: number) => {
    // Show a toast message explaining that the feature is temporarily disabled
    toast({
      title: "Feature temporarily disabled",
      description: "The sync feature is temporarily disabled to prevent creation of non-existent VMs. Please use the refresh button instead.",
      variant: "default"
    })
  }

  // State for the PowerShell command dialog
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [dialogContent, setDialogContent] = useState({
    apiKey: '',
    powershellCommand: '',
    powershellScript: '',
    vmId: '',
    vmName: ''
  })

  // Handle agent registration
  const handleRegisterAgent = async (vmId: string, vmName: string) => {
    try {
      // Show loading toast
      toast({
        title: "Registering agent...",
        description: "Please wait while we register the Windows VM agent.",
        variant: "default"
      })

      // Call the API to register the agent
      const response = await windowsVMAgentAPI.registerAgent(vmId, vmName)

      // Set dialog content
      setDialogContent({
        apiKey: response.api_key,
        powershellCommand: response.powershell_command,
        powershellScript: response.powershell_script,
        vmId: vmId,
        vmName: vmName || `VM ${vmId}`
      })

      // Open the dialog
      setIsDialogOpen(true)

      // Show success toast
      toast({
        title: "Agent registered successfully",
        description: "Please use the PowerShell command to install the agent on your Windows VM.",
        variant: "default"
      })

      // Refresh VM list to show updated agent status
      loadVMs()
    } catch (err) {
      console.error("Error registering agent:", err)
      toast({
        title: "Error",
        description: "Failed to register Windows VM agent. Please try again.",
        variant: "destructive"
      })
    }
  }

  // Handle copy to clipboard
  const handleCopy = (text: string, successMessage: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copied!",
      description: successMessage,
      variant: "default"
    })
  }

  // Whitelist functionality removed - now managed on the Proxmox Nodes page
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

            {autoRefresh && (
              <div className="ml-2">
                <Select
                  value={refreshTimeout.toString()}
                  onValueChange={(value) => setRefreshTimeout(parseInt(value))}
                >
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Refresh every" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="5">5 seconds</SelectItem>
                    <SelectItem value="15">15 seconds</SelectItem>
                    <SelectItem value="30">30 seconds</SelectItem>
                    <SelectItem value="60">1 minute</SelectItem>
                    <SelectItem value="300">5 minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
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
            {/* Sync button temporarily disabled to prevent creation of non-existent VMs */}
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
                    accessorKey: "cpu_cores",
                    header: "CPU Cores",
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
                    id: "agent_status",
                    header: "VM Agent",
                    cell: ({ row }) => {
                      const vm = row.original;
                      const agentStatus = vm.agent_status;
                      const lastSeen = vm.agent_last_seen;

                      // Only show for database VMs, not Proxmox live VMs
                      if (vm.source === 'proxmox') {
                        return <span className="text-muted-foreground">N/A</span>;
                      }

                      if (!agentStatus) {
                        return (
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs"
                            onClick={() => handleRegisterAgent(vm.id, vm.name)}
                          >
                            Register Agent
                          </Button>
                        );
                      }

                      // Determine badge color based on status
                      let badgeVariant: "default" | "secondary" | "destructive" | "outline" = "outline";
                      if (agentStatus === "running") {
                        badgeVariant = "default";
                      } else if (agentStatus === "stopped") {
                        badgeVariant = "secondary";
                      } else if (agentStatus === "error") {
                        badgeVariant = "destructive";
                      }

                      // Format last seen time if available
                      let lastSeenText = "Never";
                      if (lastSeen) {
                        const lastSeenDate = new Date(lastSeen);
                        const now = new Date();
                        const diffMs = now.getTime() - lastSeenDate.getTime();
                        const diffMins = Math.floor(diffMs / 60000);

                        if (diffMins < 1) {
                          lastSeenText = "Just now";
                        } else if (diffMins < 60) {
                          lastSeenText = `${diffMins}m ago`;
                        } else if (diffMins < 1440) {
                          const hours = Math.floor(diffMins / 60);
                          lastSeenText = `${hours}h ago`;
                        } else {
                          const days = Math.floor(diffMins / 1440);
                          lastSeenText = `${days}d ago`;
                        }
                      }

                      return (
                        <div className="flex flex-col">
                          <Badge variant={badgeVariant}>
                            {agentStatus}
                          </Badge>
                          {lastSeen && (
                            <span className="text-xs text-muted-foreground mt-1">
                              Last seen: {lastSeenText}
                            </span>
                          )}
                        </div>
                      );
                    },
                  },
                  // Whitelist column removed - now managed on the Proxmox Nodes page
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

      {/* PowerShell Command Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Windows VM Agent Installation</DialogTitle>
            <DialogDescription>
              Run the following PowerShell command on your Windows VM to install the agent.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-medium mb-2">VM Information</h3>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="font-semibold">VM ID:</span> {dialogContent.vmId}
                </div>
                <div>
                  <span className="font-semibold">VM Name:</span> {dialogContent.vmName}
                </div>
                <div>
                  <span className="font-semibold">API Key:</span>
                  <code className="ml-1 bg-gray-100 dark:bg-gray-800 p-1 rounded text-xs">{dialogContent.apiKey}</code>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="ml-2 h-6 px-2"
                    onClick={() => handleCopy(dialogContent.apiKey, "API key copied to clipboard")}
                  >
                    Copy
                  </Button>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">PowerShell Command</h3>
              <div className="relative">
                <Textarea
                  readOnly
                  value={dialogContent.powershellCommand}
                  className="font-mono text-xs h-20"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  className="absolute top-2 right-2"
                  onClick={() => handleCopy(dialogContent.powershellCommand, "PowerShell command copied to clipboard")}
                >
                  Copy Command
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Run this command in PowerShell as Administrator on your Windows VM.
              </p>
            </div>

            <div>
              <h3 className="text-sm font-medium mb-2">PowerShell Script (Alternative)</h3>
              <div className="relative">
                <Textarea
                  readOnly
                  value={dialogContent.powershellScript}
                  className="font-mono text-xs h-40"
                />
                <Button
                  variant="secondary"
                  size="sm"
                  className="absolute top-2 right-2"
                  onClick={() => handleCopy(dialogContent.powershellScript, "PowerShell script copied to clipboard")}
                >
                  Copy Script
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Alternatively, you can save this as a .ps1 file and run it as Administrator on your Windows VM.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
