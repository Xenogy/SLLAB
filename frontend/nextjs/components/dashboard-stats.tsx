"use client"

// This component is client-side only

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Activity, Bot, Server, AlertTriangle, Loader2 } from "lucide-react"
import LineChartComponent from "@/components/charts/line-chart"
import { ChartWrapper } from "@/components/charts/chart-wrapper"
import { useLatestMetricValue, useSystemOverview } from "@/hooks/use-timeseries"
import { Button } from "@/components/ui/button"

export function DashboardStats() {
  // Fetch system overview data
  const {
    cpuUsage,
    memoryUsage,
    loading: systemOverviewLoading,
    error: systemOverviewError,
    refresh: refreshSystemOverview
  } = useSystemOverview("hourly", "day")

  // Fetch latest metric values
  const { value: latestAccountCount, loading: accountCountLoading } = useLatestMetricValue("account_count", "system", "system")
  const { value: latestVmCount, loading: vmCountLoading } = useLatestMetricValue("vm_count", "system", "system")
  const { value: latestErrorCount, loading: errorCountLoading } = useLatestMetricValue("error_count", "system", "system")
  const { value: latestJobCount, loading: jobCountLoading } = useLatestMetricValue("job_count", "system", "system")
  return (
    <Tabs defaultValue="overview" className="space-y-4">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="accounts">Accounts</TabsTrigger>
        <TabsTrigger value="jobs">Jobs</TabsTrigger>
        <TabsTrigger value="vms">VMs</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="space-y-4">
        <div className="flex justify-end mb-2">
          <Button onClick={refreshSystemOverview} variant="outline" size="sm">
            {systemOverviewLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              "Refresh"
            )}
          </Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Accounts</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {accountCountLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  latestAccountCount !== null ? latestAccountCount : 'N/A'
                )}
              </div>
              <p className="text-xs text-muted-foreground">Managed accounts</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Jobs</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {jobCountLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  latestJobCount !== null ? latestJobCount : 'N/A'
                )}
              </div>
              <p className="text-xs text-muted-foreground">Running jobs</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Running VMs</CardTitle>
              <Server className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {vmCountLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  latestVmCount !== null ? latestVmCount : 'N/A'
                )}
              </div>
              <p className="text-xs text-muted-foreground">Active virtual machines</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Errors</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {errorCountLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  latestErrorCount !== null ? latestErrorCount : 'N/A'
                )}
              </div>
              <p className="text-xs text-muted-foreground">Unresolved errors</p>
            </CardContent>
          </Card>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>Performance Overview</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
              <ChartWrapper className="aspect-[2/1]" title="Performance metrics over time">
                {systemOverviewError ? (
                  <div className="flex h-full items-center justify-center">
                    <p className="text-sm text-muted-foreground">
                      Error loading performance data. Please try again.
                    </p>
                  </div>
                ) : cpuUsage && cpuUsage.length > 0 ? (
                  <LineChartComponent
                    data={cpuUsage}
                    loading={systemOverviewLoading}
                    color="#f97316"
                    showDots={false}
                  />
                ) : (
                  <div className="flex h-full items-center justify-center">
                    <p className="text-sm text-muted-foreground">
                      No performance data available. Please generate sample data or wait for metrics to be collected.
                    </p>
                  </div>
                )}
              </ChartWrapper>
            </CardContent>
          </Card>
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest system events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center">
                  <div className="mr-2 h-2 w-2 rounded-full bg-green-500" />
                  <div className="flex-1 flex justify-between">
                    <div className="text-sm">VM #8 started successfully</div>
                    <div className="text-xs text-muted-foreground">2m ago</div>
                  </div>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-2 w-2 rounded-full bg-yellow-500" />
                  <div className="flex-1 flex justify-between">
                    <div className="text-sm">Account #42 login warning</div>
                    <div className="text-xs text-muted-foreground">15m ago</div>
                  </div>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-2 w-2 rounded-full bg-blue-500" />
                  <div className="flex-1 flex justify-between">
                    <div className="text-sm">Job #87 completed</div>
                    <div className="text-xs text-muted-foreground">1h ago</div>
                  </div>
                </div>
                <div className="flex items-center">
                  <div className="mr-2 h-2 w-2 rounded-full bg-red-500" />
                  <div className="flex-1 flex justify-between">
                    <div className="text-sm">VM #3 error detected</div>
                    <div className="text-xs text-muted-foreground">3h ago</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
      <TabsContent value="accounts" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Account Statistics</CardTitle>
            <CardDescription>Overview of all managed Steam accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center text-sm text-muted-foreground">
              Account statistics content will be displayed here
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="jobs" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Job Statistics</CardTitle>
            <CardDescription>Overview of all running and completed jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center text-sm text-muted-foreground">
              Job statistics content will be displayed here
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="vms" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>VM Statistics</CardTitle>
            <CardDescription>Overview of all virtual machines</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center text-sm text-muted-foreground">
              VM statistics content will be displayed here
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  )
}
