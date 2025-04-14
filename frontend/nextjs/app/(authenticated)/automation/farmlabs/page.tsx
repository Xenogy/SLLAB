import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Upload, RefreshCw, Activity } from "lucide-react"
import Link from "next/link"
import { DataTable } from "@/components/data-table"
import { columns, type Job } from "./columns"

// This would come from your API in a real application
const jobs: Job[] = [
  {
    id: "1",
    name: "Market Scan",
    status: "running",
    progress: "45%",
    startTime: "2023-04-12T08:30:00Z",
    estimatedEnd: "2023-04-12T10:30:00Z",
    assignedVMs: 2,
  },
  {
    id: "2",
    name: "Item Collection",
    status: "completed",
    progress: "100%",
    startTime: "2023-04-11T14:20:00Z",
    estimatedEnd: "2023-04-11T16:20:00Z",
    assignedVMs: 3,
  },
  {
    id: "3",
    name: "Trade Automation",
    status: "queued",
    progress: "0%",
    startTime: null,
    estimatedEnd: null,
    assignedVMs: 2,
  },
  {
    id: "4",
    name: "Account Rotation",
    status: "failed",
    progress: "67%",
    startTime: "2023-04-10T11:45:00Z",
    estimatedEnd: "2023-04-10T13:45:00Z",
    assignedVMs: 4,
  },
  {
    id: "5",
    name: "Inventory Check",
    status: "paused",
    progress: "33%",
    startTime: "2023-04-12T07:30:00Z",
    estimatedEnd: null,
    assignedVMs: 1,
  },
]

export default function FarmlabsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Farm Labs</h1>
        <div className="flex items-center gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Job
          </Button>
          <Button variant="outline" asChild>
            <Link href="/automation/farmlabs/upload">
              <Upload className="mr-2 h-4 w-4" />
              Upload Script
            </Link>
          </Button>
          <Button variant="ghost" size="icon">
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Tabs defaultValue="jobs" className="space-y-4">
        <TabsList>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
          <TabsTrigger value="scripts">Scripts</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>
        <TabsContent value="jobs" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">24</div>
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
                <CardTitle className="text-sm font-medium">Queued</CardTitle>
                <div className="h-2 w-2 rounded-full bg-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">5</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Failed</CardTitle>
                <div className="h-2 w-2 rounded-full bg-red-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Jobs</CardTitle>
              <CardDescription>Manage your automation jobs</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={jobs}
                filterColumn="name"
                filterPlaceholder="Filter by job name..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scripts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Scripts</CardTitle>
              <CardDescription>Manage your automation scripts</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-sm text-muted-foreground py-8">
                Scripts management interface will be displayed here
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Job History</CardTitle>
              <CardDescription>View completed and failed jobs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-sm text-muted-foreground py-8">Job history will be displayed here</div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
