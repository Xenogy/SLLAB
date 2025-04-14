import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Plus, Download, Upload, RefreshCw, Server } from "lucide-react"
import { DataTable } from "@/components/data-table"
import { columns } from "./columns"
import { ColumnDef } from "@tanstack/react-table"

// This would come from your API in a real application
const vms = [
  {
    id: "1",
    name: "VM-01",
    status: "running",
    ip: "192.168.1.101",
    cpu: "45%",
    memory: "2.4GB/4GB",
    uptime: "3d 5h 12m",
  },
  {
    id: "2",
    name: "VM-02",
    status: "stopped",
    ip: "192.168.1.102",
    cpu: "0%",
    memory: "0GB/4GB",
    uptime: "0d 0h 0m",
  },
  {
    id: "3",
    name: "VM-03",
    status: "running",
    ip: "192.168.1.103",
    cpu: "78%",
    memory: "3.1GB/4GB",
    uptime: "1d 14h 23m",
  },
  {
    id: "4",
    name: "VM-04",
    status: "error",
    ip: "192.168.1.104",
    cpu: "100%",
    memory: "3.9GB/4GB",
    uptime: "0d 2h 45m",
  },
  {
    id: "5",
    name: "VM-05",
    status: "running",
    ip: "192.168.1.105",
    cpu: "22%",
    memory: "1.8GB/4GB",
    uptime: "5d 8h 17m",
  },
]

export default function VMsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Virtual Machines</h1>
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
          <Button variant="ghost" size="icon">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total VMs</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">12</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running</CardTitle>
            <div className="h-2 w-2 rounded-full bg-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">8</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stopped</CardTitle>
            <div className="h-2 w-2 rounded-full bg-gray-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">3</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
            <div className="h-2 w-2 rounded-full bg-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1</div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Virtual Machines</CardTitle>
          <CardDescription>Manage your virtual machines</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            columns={columns as ColumnDef<typeof vms[0]>[]}
            data={vms}
            filterColumn="name"
            filterPlaceholder="Filter by VM name..."
          />
        </CardContent>
      </Card>
    </div>
  )
}
