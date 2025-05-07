"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RefreshCw } from "lucide-react"
import { logsAPI, LogStatistic } from "@/lib/logs-api"
import { useToast } from "@/components/ui/use-toast"

// Import Chart.js components
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
  ChartOptions,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
)

export function LogStatistics() {
  const { toast } = useToast()
  const [timeRange, setTimeRange] = useState('7')
  const [groupBy, setGroupBy] = useState('day')
  const [statistics, setStatistics] = useState<LogStatistic[]>([])
  const [loading, setLoading] = useState(false)

  // Define colors for log levels
  const levelColors = {
    DEBUG: 'rgba(108, 117, 125, 0.7)',
    INFO: 'rgba(13, 110, 253, 0.7)',
    WARNING: 'rgba(255, 193, 7, 0.7)',
    ERROR: 'rgba(220, 53, 69, 0.7)',
    CRITICAL: 'rgba(127, 0, 0, 0.7)',
  }

  // Fetch statistics
  const fetchStatistics = async () => {
    setLoading(true)
    try {
      const data = await logsAPI.getStatistics(parseInt(timeRange), groupBy)
      setStatistics(data)
    } catch (error) {
      console.error("Error fetching log statistics:", error)
      toast({
        title: "Error",
        description: "Failed to fetch log statistics. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchStatistics()
  }, [timeRange, groupBy])

  // Process data for chart
  const prepareChartData = (): ChartData<'bar'> => {
    if (!statistics.length) {
      return {
        labels: [],
        datasets: [],
      }
    }

    // Get unique time periods and levels
    const timePeriods = Array.from(new Set(statistics.map(stat => {
      const date = new Date(stat.time_period)
      return groupBy === 'hour' 
        ? date.toLocaleString(undefined, { hour: 'numeric', hour12: true })
        : date.toLocaleDateString()
    })))
    
    const levels = Array.from(new Set(statistics.map(stat => stat.level)))
    
    // Sort levels by severity
    const levelOrder = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    levels.sort((a, b) => levelOrder.indexOf(a) - levelOrder.indexOf(b))
    
    // Create datasets for each level
    const datasets = levels.map(level => {
      const levelData = timePeriods.map(period => {
        const stat = statistics.find(s => {
          const date = new Date(s.time_period)
          const formattedDate = groupBy === 'hour' 
            ? date.toLocaleString(undefined, { hour: 'numeric', hour12: true })
            : date.toLocaleDateString()
          return formattedDate === period && s.level === level
        })
        return stat ? stat.count : 0
      })
      
      return {
        label: level,
        data: levelData,
        backgroundColor: levelColors[level as keyof typeof levelColors] || 'rgba(0, 0, 0, 0.7)',
      }
    })
    
    return {
      labels: timePeriods,
      datasets,
    }
  }

  // Chart options
  const chartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Log Volume by Level',
      },
    },
    scales: {
      x: {
        stacked: true,
      },
      y: {
        stacked: true,
        beginAtZero: true,
      },
    },
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Log Statistics</CardTitle>
            <CardDescription>
              Log volume by level over time
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Time Range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Last 24 hours</SelectItem>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
            <Select value={groupBy} onValueChange={setGroupBy}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Group By" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="hour">Hour</SelectItem>
                <SelectItem value="day">Day</SelectItem>
                <SelectItem value="week">Week</SelectItem>
                <SelectItem value="month">Month</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : statistics.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <p className="mb-2 text-sm text-muted-foreground">No log statistics available</p>
            <p className="text-xs text-muted-foreground">Try adjusting your time range or check back later</p>
          </div>
        ) : (
          <div className="h-64">
            <Bar data={prepareChartData()} options={chartOptions} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
