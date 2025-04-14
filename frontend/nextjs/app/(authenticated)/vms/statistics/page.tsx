import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BarChart, LineChart, PieChart } from "lucide-react"
import LineChartComponent from "@/components/charts/line-chart"
import BarChartComponent from "@/components/charts/bar-chart"
import PieChartComponent from "@/components/charts/pie-chart"
import { ChartWrapper } from "@/components/charts/chart-wrapper"

export default function StatisticsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Statistics</h1>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="hw-profiler">HW Profiler</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="job-tracking">Job Tracking</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
                <LineChart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">42%</div>
                <p className="text-xs text-muted-foreground">Average across all VMs</p>
                <ChartWrapper className="mt-4 aspect-[3/2]" title="CPU usage over time">
                  <LineChartComponent />
                </ChartWrapper>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <BarChart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">2.4GB/4GB</div>
                <p className="text-xs text-muted-foreground">Average across all VMs</p>
                <ChartWrapper className="mt-4 aspect-[3/2]" title="Memory usage by VM">
                  <BarChartComponent />
                </ChartWrapper>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">VM Status Distribution</CardTitle>
                <PieChart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12 VMs</div>
                <p className="text-xs text-muted-foreground">Total managed VMs</p>
                <ChartWrapper className="mt-4 aspect-[3/2]" title="VM status distribution">
                  <PieChartComponent />
                </ChartWrapper>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Performance</CardTitle>
              <CardDescription>Overall system performance metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ChartWrapper className="h-full" title="System performance over time">
                  <LineChartComponent />
                </ChartWrapper>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hw-profiler" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Hardware Profiler</CardTitle>
              <CardDescription>Detailed hardware information for each VM</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-sm text-muted-foreground py-8">
                Hardware profiler interface will be displayed here
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Error Logs</CardTitle>
              <CardDescription>System and application errors</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-sm text-muted-foreground py-8">Error logs will be displayed here</div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="job-tracking" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Job Time Tracking</CardTitle>
              <CardDescription>Performance metrics for automation jobs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center text-sm text-muted-foreground py-8">
                Job time tracking interface will be displayed here
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
