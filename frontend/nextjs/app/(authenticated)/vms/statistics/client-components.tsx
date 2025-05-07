"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { BarChart, LineChart, PieChart, Loader2 } from "lucide-react"
import LineChartComponent from "@/components/charts/line-chart"
import BarChartComponent from "@/components/charts/bar-chart"
import PieChartComponent from "@/components/charts/pie-chart"
import { ChartWrapper } from "@/components/charts/chart-wrapper"
import { useTimeseriesData, useLatestMetricValue, useSystemOverview } from "@/hooks/use-timeseries"
import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function StatisticsPageClient() {
  // State for period selection
  const [period, setPeriod] = useState<string>("hourly")
  const [duration, setDuration] = useState<string>("day")
  const [generatingSampleData, setGeneratingSampleData] = useState<boolean>(false)
  const [current_user, setCurrentUser] = useState<any>(null)

  // Fetch current user
  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        // Use the authAPI from lib/api.ts
        const { authAPI } = await import('@/lib/api')
        const userData = await authAPI.getCurrentUser()
        setCurrentUser(userData)
      } catch (error) {
        console.error('Error fetching current user:', error)
      }
    }

    fetchCurrentUser()
  }, [])

  // Fetch system overview data
  const {
    cpuUsage,
    memoryUsage,
    diskUsage,
    vmCount,
    loading: systemOverviewLoading,
    error: systemOverviewError,
    refresh: refreshSystemOverview
  } = useSystemOverview(period, duration)

  // Fetch latest metric values
  const {
    value: latestCpuUsage,
    loading: cpuLoading
  } = useLatestMetricValue("cpu_usage", "system", "system")

  const {
    value: latestMemoryUsage,
    loading: memoryLoading
  } = useLatestMetricValue("memory_usage", "system", "system")

  const {
    value: latestVmCount,
    loading: vmCountLoading
  } = useLatestMetricValue("vm_count", "system", "system")

  // Fetch VM status distribution data
  const {
    data: vmStatusData,
    loading: vmStatusLoading,
    error: vmStatusError,
    refresh: refreshVmStatus
  } = useTimeseriesData("vm_status_distribution", {
    period: "hourly",
    limit: 1000
  })

  // Transform VM status data for pie chart
  const vmStatusPieData = !vmStatusLoading && vmStatusData && vmStatusData.length > 0
    ? [
        { name: "Running", value: vmStatusData[vmStatusData.length - 1]?.running || 0 },
        { name: "Stopped", value: vmStatusData[vmStatusData.length - 1]?.stopped || 0 },
        { name: "Error", value: vmStatusData[vmStatusData.length - 1]?.error || 0 }
      ]
    : [
        { name: "Running", value: 0 },
        { name: "Stopped", value: 0 },
        { name: "Error", value: 0 }
      ];

  // Handle refresh
  const handleRefresh = () => {
    refreshSystemOverview();
    refreshVmStatus();
  }

  // Handle period change
  const handlePeriodChange = (value: string) => {
    setPeriod(value);
  }

  // Handle duration change
  const handleDurationChange = (value: string) => {
    setDuration(value);
  }

  // Handle generate sample data
  const handleGenerateSampleData = async () => {
    try {
      setGeneratingSampleData(true)

      // Use the fetchAPI function from lib/api.ts
      const { fetchAPI } = await import('@/lib/api')
      const data = await fetchAPI('/timeseries/generate-sample-data', {
        method: 'POST',
        body: { days: 7 }
      })

      console.log('Sample data generated:', data)
      // Refresh data
      refreshSystemOverview()
      refreshVmStatus()
    } catch (error) {
      console.error('Error generating sample data:', error)

      // Create mock data for testing if API fails
      const mockData = createMockData()
      console.log('Using mock data instead:', mockData)
    } finally {
      setGeneratingSampleData(false)
    }
  }

  // Create mock data for testing
  const createMockData = () => {
    const now = new Date()
    const mockData = []

    // Create 24 hours of data
    for (let i = 0; i < 24; i++) {
      const timestamp = new Date(now.getTime() - (23 - i) * 60 * 60 * 1000).toISOString()
      mockData.push({
        timestamp,
        value: Math.random() * 100
      })
    }

    return mockData
  }

  // State for mock data
  const [useMockData, setUseMockData] = useState(false)
  const [mockCpuData, setMockCpuData] = useState<TimeseriesDataPoint[]>([])
  const [mockMemoryData, setMockMemoryData] = useState<TimeseriesDataPoint[]>([])
  const [mockVmStatusData, setMockVmStatusData] = useState<any[]>([])
  const [collectingMetrics, setCollectingMetrics] = useState<boolean>(false)

  // Handle using mock data
  const handleUseMockData = () => {
    setUseMockData(true)
    setMockCpuData(createMockData())
    setMockMemoryData(createMockData())

    // Create a mock VM status distribution
    setMockVmStatusData([
      {
        timestamp: new Date().toISOString(),
        running: Math.floor(Math.random() * 10),
        stopped: Math.floor(Math.random() * 5),
        error: Math.floor(Math.random() * 2)
      }
    ])
  }

  // Handle collect metrics
  const handleCollectMetrics = async () => {
    try {
      setCollectingMetrics(true)

      // Use the fetchAPI function from lib/api.ts
      const { fetchAPI } = await import('@/lib/api')

      // First, try to collect metrics
      console.log('Triggering metrics collection...')
      const data = await fetchAPI('/timeseries/collect-metrics', {
        method: 'POST'
      })

      console.log('Metrics collection triggered:', data)

      // Wait a moment to allow metrics to be processed
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Then refresh the data
      console.log('Refreshing data...')
      await refreshSystemOverview()
      await refreshVmStatus()

      // Show success message
      alert('Metrics collected successfully! The charts should now display real data.')

      // Set useMockData to false to ensure we're showing real data
      setUseMockData(false)
    } catch (error) {
      console.error('Error collecting metrics:', error)
      alert('Error collecting metrics. Please try again or check the console for details.')
    } finally {
      setCollectingMetrics(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Statistics</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Period:</span>
            <Select value={period} onValueChange={handlePeriodChange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="raw">Raw</SelectItem>
                <SelectItem value="hourly">Hourly</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
                <SelectItem value="weekly">Weekly</SelectItem>
                <SelectItem value="monthly">Monthly</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">Duration:</span>
            <Select value={duration} onValueChange={handleDurationChange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Duration" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hour">Last Hour</SelectItem>
                <SelectItem value="day">Last Day</SelectItem>
                <SelectItem value="week">Last Week</SelectItem>
                <SelectItem value="month">Last Month</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleRefresh} variant="outline" size="sm">
              {systemOverviewLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                "Refresh"
              )}
            </Button>
            {current_user?.role === 'admin' && (
              <Button
                onClick={handleGenerateSampleData}
                variant="outline"
                size="sm"
                disabled={generatingSampleData}
              >
                {generatingSampleData ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  "Generate Sample Data"
                )}
              </Button>
            )}
            <Button
              onClick={handleUseMockData}
              variant="outline"
              size="sm"
            >
              Use Mock Data
            </Button>
            {current_user?.role === 'admin' && (
              <Button
                onClick={handleCollectMetrics}
                variant="default"
                size="sm"
                disabled={collectingMetrics}
                className="bg-green-600 hover:bg-green-700"
              >
                {collectingMetrics ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Collecting...
                  </>
                ) : (
                  "Collect Real Metrics"
                )}
              </Button>
            )}
          </div>
        </div>
      </div>

      {current_user?.role === 'admin' && (
        <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-md mb-4 border border-blue-200 dark:border-blue-800">
          <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300">Admin Tip</h3>
          <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">
            To see real-time metrics, click the <span className="font-medium">"Collect Real Metrics"</span> button above.
            This will trigger data collection from the system and display actual performance metrics.
          </p>
        </div>
      )}

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
                <div className="text-2xl font-bold">
                  {cpuLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    `${latestCpuUsage !== null ? latestCpuUsage.toFixed(1) : 'N/A'}%`
                  )}
                </div>
                <p className="text-xs text-muted-foreground">System CPU usage</p>
                <ChartWrapper className="mt-4 aspect-[3/2]" title="CPU usage over time">
                  {useMockData && mockCpuData.length > 0 ? (
                    <LineChartComponent
                      data={mockCpuData}
                      loading={false}
                      color="#f97316"
                    />
                  ) : cpuUsage && cpuUsage.length > 0 ? (
                    <LineChartComponent
                      data={cpuUsage}
                      loading={systemOverviewLoading}
                      color="#f97316"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <p className="text-xs text-muted-foreground">
                        No CPU data available. Try clicking "Use Mock Data" for a demo.
                      </p>
                    </div>
                  )}
                </ChartWrapper>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
                <BarChart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {memoryLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    `${latestMemoryUsage !== null ? latestMemoryUsage.toFixed(1) : 'N/A'}%`
                  )}
                </div>
                <p className="text-xs text-muted-foreground">System memory usage</p>
                <ChartWrapper className="mt-4 aspect-[3/2]" title="Memory usage over time">
                  {useMockData && mockMemoryData.length > 0 ? (
                    <LineChartComponent
                      data={mockMemoryData}
                      loading={false}
                      color="#8884d8"
                    />
                  ) : memoryUsage && memoryUsage.length > 0 ? (
                    <LineChartComponent
                      data={memoryUsage}
                      loading={systemOverviewLoading}
                      color="#8884d8"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <p className="text-xs text-muted-foreground">
                        No memory data available. Try clicking "Use Mock Data" for a demo.
                      </p>
                    </div>
                  )}
                </ChartWrapper>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">VM Status Distribution</CardTitle>
                <PieChart className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {vmCountLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    `${latestVmCount !== null ? latestVmCount : 'N/A'} VMs`
                  )}
                </div>
                <p className="text-xs text-muted-foreground">Total managed VMs</p>
                <ChartWrapper className="mt-4 aspect-[3/2]" title="VM status distribution">
                  {useMockData && mockVmStatusData.length > 0 ? (
                    <PieChartComponent
                      data={[
                        { name: "Running", value: mockVmStatusData[0].running },
                        { name: "Stopped", value: mockVmStatusData[0].stopped },
                        { name: "Error", value: mockVmStatusData[0].error }
                      ]}
                      loading={false}
                      colors={["#4ade80", "#94a3b8", "#f87171"]}
                    />
                  ) : vmStatusData && vmStatusData.length > 0 ? (
                    <PieChartComponent
                      data={vmStatusPieData}
                      loading={vmStatusLoading}
                      colors={["#4ade80", "#94a3b8", "#f87171"]}
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <p className="text-xs text-muted-foreground">
                        No VM status data available. Try clicking "Use Mock Data" for a demo.
                      </p>
                    </div>
                  )}
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
                  {systemOverviewError && !useMockData ? (
                    <div className="flex h-full items-center justify-center">
                      <p className="text-sm text-muted-foreground">
                        Error loading system performance data: {systemOverviewError}
                      </p>
                    </div>
                  ) : useMockData && mockCpuData.length > 0 ? (
                    <LineChartComponent
                      data={mockCpuData}
                      loading={false}
                      color="#f97316"
                    />
                  ) : cpuUsage && cpuUsage.length > 0 ? (
                    <LineChartComponent
                      data={cpuUsage}
                      loading={systemOverviewLoading}
                      color="#f97316"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <p className="text-sm text-muted-foreground">
                        No performance data available. Please click "Use Mock Data" for a demo or generate sample data.
                      </p>
                    </div>
                  )}
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
