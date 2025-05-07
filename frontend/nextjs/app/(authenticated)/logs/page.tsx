"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Calendar } from "@/components/ui/calendar"
import { format } from "date-fns"
import { CalendarIcon, RefreshCw, FileText, Filter, X } from "lucide-react"
import { DataTable } from "@/components/data-table"
import { createColumns } from "./columns"
import { useToast } from "@/components/ui/use-toast"
import { LogDetailDialog } from "./log-detail-dialog"
import { LogStatistics } from "./log-statistics"
import { logsAPI, LogEntry, LogLevel, LogCategory, LogSource } from "@/lib/logs-api"
import { logInfo } from "@/lib/log-utils"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

export default function LogsPage() {
  const { toast } = useToast()
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [totalLogs, setTotalLogs] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterOpen, setFilterOpen] = useState(false)

  // Filter states
  const [startDate, setStartDate] = useState<Date | undefined>(undefined)
  const [endDate, setEndDate] = useState<Date | undefined>(undefined)
  const [selectedLevels, setSelectedLevels] = useState<LogLevel[]>([])
  const [categories, setCategories] = useState<LogCategory[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [sources, setSources] = useState<LogSource[]>([])
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [entityType, setEntityType] = useState<string>("")
  const [entityId, setEntityId] = useState<string>("")

  // Predefined time ranges
  const timeRanges = [
    { label: "Last hour", value: "1h" },
    { label: "Last 24 hours", value: "24h" },
    { label: "Last 7 days", value: "7d" },
    { label: "Last 30 days", value: "30d" },
    { label: "Custom", value: "custom" },
  ]
  const [selectedTimeRange, setSelectedTimeRange] = useState("24h")

  // Log levels with colors
  const logLevels: { value: LogLevel, label: string, color: string }[] = [
    { value: "DEBUG", label: "Debug", color: "bg-gray-500" },
    { value: "INFO", label: "Info", color: "bg-blue-500" },
    { value: "WARNING", label: "Warning", color: "bg-yellow-500" },
    { value: "ERROR", label: "Error", color: "bg-red-500" },
    { value: "CRITICAL", label: "Critical", color: "bg-red-800" },
  ]

  // Fetch logs
  const fetchLogs = async () => {
    setLoading(true)
    try {
      // Check if we have a token before making the request
      // Import AUTH_CONFIG to use the correct token key
      const { AUTH_CONFIG } = await import('@/lib/config')
      const token = localStorage.getItem(AUTH_CONFIG.tokenKey)
      if (!token) {
        console.warn('No authentication token found in localStorage')

        // Check if we have a token in cookies
        const cookies = document.cookie.split(';').map(cookie => cookie.trim())
        const tokenCookie = cookies.find(cookie => cookie.startsWith(`${AUTH_CONFIG.tokenKey}=`))
        if (!tokenCookie) {
          console.warn('No authentication token found in cookies either')
          toast({
            title: "Authentication Error",
            description: "Your session may have expired. Please try refreshing the page or logging in again.",
            variant: "destructive",
          })
          setLogs([])
          setTotalLogs(0)
          setTotalPages(0)
          setLoading(false)
          return
        }
      }

      // Prepare filter parameters
      const params: any = {
        page,
        page_size: pageSize,
      }

      // Add search query if provided
      if (searchQuery) {
        params.search = searchQuery
      }

      // Add date filters
      if (startDate) {
        params.start_time = startDate.toISOString()
      } else if (selectedTimeRange !== "custom") {
        // Calculate start time based on selected time range
        const now = new Date()
        let startTime: Date

        switch (selectedTimeRange) {
          case "1h":
            startTime = new Date(now.getTime() - 60 * 60 * 1000)
            break
          case "24h":
            startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000)
            break
          case "7d":
            startTime = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
            break
          case "30d":
            startTime = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
            break
          default:
            startTime = new Date(now.getTime() - 24 * 60 * 60 * 1000)
        }

        params.start_time = startTime.toISOString()
      }

      if (endDate) {
        params.end_time = endDate.toISOString()
      }

      // Add level filters
      if (selectedLevels.length > 0) {
        params.levels = selectedLevels
      }

      // Add category filters
      if (selectedCategories.length > 0) {
        params.categories = selectedCategories
      }

      // Add source filters
      if (selectedSources.length > 0) {
        params.sources = selectedSources
      }

      // Add entity filters
      if (entityType) {
        params.entity_type = entityType
      }

      if (entityId) {
        params.entity_id = entityId
      }

      console.log('Fetching logs with params:', params)
      const response = await logsAPI.getLogs(params)
      console.log('Logs response:', response)
      setLogs(response.logs)
      setTotalLogs(response.total)
      setTotalPages(response.total_pages)
    } catch (error: any) {
      console.error("Error fetching logs:", error)

      // Provide more specific error messages based on the error
      let errorMessage = "Failed to fetch logs. Please try again."

      if (error.message === 'Not authenticated. Please log in again.') {
        errorMessage = "Your session has expired. Please refresh the page or log in again."
      } else if (error.message && error.message.includes('401')) {
        errorMessage = "Authentication error. Please refresh the page or log in again."
      } else if (error.message && error.message.includes('403')) {
        errorMessage = "You don't have permission to view these logs."
      } else if (error.message && error.message.includes('500')) {
        errorMessage = "Server error. Please try again later."
      }

      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive",
      })

      setLogs([])
      setTotalLogs(0)
      setTotalPages(0)
    } finally {
      setLoading(false)
    }
  }

  // Fetch categories and sources
  const fetchMetadata = async () => {
    try {
      // Check if we have a token before making the request
      // Import AUTH_CONFIG to use the correct token key
      const { AUTH_CONFIG } = await import('@/lib/config')
      const token = localStorage.getItem(AUTH_CONFIG.tokenKey)
      if (!token) {
        console.warn('No authentication token found in localStorage for metadata fetch')
        return
      }

      console.log('Fetching log metadata (categories and sources)')
      const [categoriesResponse, sourcesResponse] = await Promise.all([
        logsAPI.getCategories(),
        logsAPI.getSources(),
      ])
      console.log('Metadata fetched successfully:', { categories: categoriesResponse.length, sources: sourcesResponse.length })
      setCategories(categoriesResponse)
      setSources(sourcesResponse)
    } catch (error: any) {
      console.error("Error fetching metadata:", error)

      // Only show toast for non-auth errors to avoid duplicate messages
      if (!error.message?.includes('401')) {
        toast({
          title: "Warning",
          description: "Could not load log categories and sources. Some filter options may be unavailable.",
          variant: "warning",
        })
      }
    }
  }

  // Initial data fetch
  useEffect(() => {
    fetchLogs()
    fetchMetadata()

    // Create a test log entry when the page loads
    logInfo(
      "Logs page loaded",
      "UI",
      "LogsPage",
      { page, pageSize, filters: { levels: selectedLevels, categories: selectedCategories, sources: selectedSources } },
      "page",
      "logs"
    )
  }, [page, pageSize])

  // Handle log details view
  const handleViewDetails = (log: LogEntry) => {
    setSelectedLog(log)
    setDetailsOpen(true)
  }

  // Handle search
  const handleSearch = () => {
    setPage(1) // Reset to first page when searching
    fetchLogs()
  }

  // Handle filter changes
  const handleFilterChange = () => {
    setPage(1) // Reset to first page when filtering
    fetchLogs()
  }

  // Handle time range selection
  const handleTimeRangeChange = (value: string) => {
    setSelectedTimeRange(value)

    // Clear custom date range if not "custom"
    if (value !== "custom") {
      setStartDate(undefined)
      setEndDate(undefined)
    }
  }

  // Handle level selection
  const handleLevelChange = (level: LogLevel) => {
    setSelectedLevels(prev => {
      if (prev.includes(level)) {
        return prev.filter(l => l !== level)
      } else {
        return [...prev, level]
      }
    })
  }

  // Handle category selection
  const handleCategoryChange = (category: string) => {
    setSelectedCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category)
      } else {
        return [...prev, category]
      }
    })
  }

  // Handle source selection
  const handleSourceChange = (source: string) => {
    setSelectedSources(prev => {
      if (prev.includes(source)) {
        return prev.filter(s => s !== source)
      } else {
        return [...prev, source]
      }
    })
  }

  // Clear all filters
  const clearFilters = () => {
    setSelectedTimeRange("24h")
    setStartDate(undefined)
    setEndDate(undefined)
    setSelectedLevels([])
    setSelectedCategories([])
    setSelectedSources([])
    setEntityType("")
    setEntityId("")
    setSearchQuery("")
  }

  // Create columns with actions
  const columns = createColumns({
    onViewDetails: handleViewDetails,
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Logs</h1>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => fetchLogs()} disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Popover open={filterOpen} onOpenChange={setFilterOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Filters
                {(selectedLevels.length > 0 || selectedCategories.length > 0 || selectedSources.length > 0 || entityType || entityId || startDate || endDate) && (
                  <Badge className="ml-2 bg-primary" variant="secondary">
                    {selectedLevels.length + selectedCategories.length + selectedSources.length + (entityType ? 1 : 0) + (entityId ? 1 : 0) + (startDate || endDate ? 1 : 0)}
                  </Badge>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-96 p-4" align="end">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-medium">Filters</h3>
                  <Button variant="ghost" size="sm" onClick={clearFilters}>
                    <X className="h-4 w-4 mr-2" />
                    Clear All
                  </Button>
                </div>

                {/* Time Range */}
                <div className="space-y-2">
                  <Label>Time Range</Label>
                  <Select value={selectedTimeRange} onValueChange={handleTimeRangeChange}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select time range" />
                    </SelectTrigger>
                    <SelectContent>
                      {timeRanges.map((range) => (
                        <SelectItem key={range.value} value={range.value}>
                          {range.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  {selectedTimeRange === "custom" && (
                    <div className="grid grid-cols-2 gap-2 mt-2">
                      <div>
                        <Label className="text-xs">Start Date</Label>
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button
                              variant="outline"
                              className="w-full justify-start text-left font-normal mt-1"
                              size="sm"
                            >
                              <CalendarIcon className="mr-2 h-4 w-4" />
                              {startDate ? format(startDate, "PPP") : "Pick a date"}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0">
                            <Calendar
                              mode="single"
                              selected={startDate}
                              onSelect={setStartDate}
                              initialFocus
                            />
                          </PopoverContent>
                        </Popover>
                      </div>
                      <div>
                        <Label className="text-xs">End Date</Label>
                        <Popover>
                          <PopoverTrigger asChild>
                            <Button
                              variant="outline"
                              className="w-full justify-start text-left font-normal mt-1"
                              size="sm"
                            >
                              <CalendarIcon className="mr-2 h-4 w-4" />
                              {endDate ? format(endDate, "PPP") : "Pick a date"}
                            </Button>
                          </PopoverTrigger>
                          <PopoverContent className="w-auto p-0">
                            <Calendar
                              mode="single"
                              selected={endDate}
                              onSelect={setEndDate}
                              initialFocus
                            />
                          </PopoverContent>
                        </Popover>
                      </div>
                    </div>
                  )}
                </div>

                {/* Log Levels */}
                <div className="space-y-2">
                  <Label>Log Levels</Label>
                  <div className="flex flex-wrap gap-2">
                    {logLevels.map((level) => (
                      <div key={level.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`level-${level.value}`}
                          checked={selectedLevels.includes(level.value)}
                          onCheckedChange={() => handleLevelChange(level.value)}
                        />
                        <Label htmlFor={`level-${level.value}`} className="flex items-center">
                          <Badge className={`${level.color} text-white`}>{level.label}</Badge>
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Categories */}
                {categories.length > 0 && (
                  <div className="space-y-2">
                    <Label>Categories</Label>
                    <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                      {categories.map((category) => (
                        <div key={category.id} className="flex items-center space-x-2">
                          <Checkbox
                            id={`category-${category.id}`}
                            checked={selectedCategories.includes(category.name)}
                            onCheckedChange={() => handleCategoryChange(category.name)}
                          />
                          <Label htmlFor={`category-${category.id}`}>{category.name}</Label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sources */}
                {sources.length > 0 && (
                  <div className="space-y-2">
                    <Label>Sources</Label>
                    <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                      {sources.map((source) => (
                        <div key={source.id} className="flex items-center space-x-2">
                          <Checkbox
                            id={`source-${source.id}`}
                            checked={selectedSources.includes(source.name)}
                            onCheckedChange={() => handleSourceChange(source.name)}
                          />
                          <Label htmlFor={`source-${source.id}`}>{source.name}</Label>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Entity Filters */}
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Entity Type</Label>
                    <Input
                      placeholder="Entity Type"
                      value={entityType}
                      onChange={(e) => setEntityType(e.target.value)}
                      size="sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Entity ID</Label>
                    <Input
                      placeholder="Entity ID"
                      value={entityId}
                      onChange={(e) => setEntityId(e.target.value)}
                      size="sm"
                    />
                  </div>
                </div>

                <Button className="w-full" onClick={() => { handleFilterChange(); setFilterOpen(false); }}>
                  Apply Filters
                </Button>
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Log Entries</CardTitle>
          <CardDescription>
            View and filter log entries from various sources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center py-4">
            <Input
              placeholder="Search log messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="max-w-sm"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch()
                }
              }}
            />
            <Button className="ml-2" onClick={handleSearch}>
              Search
            </Button>
          </div>

          {/* Active Filters Display */}
          {(selectedLevels.length > 0 || selectedCategories.length > 0 || selectedSources.length > 0 || entityType || entityId || startDate || endDate) && (
            <div className="flex flex-wrap gap-2 mb-4">
              {selectedTimeRange !== "24h" && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Time: {selectedTimeRange === "custom" ? "Custom Range" : timeRanges.find(r => r.value === selectedTimeRange)?.label}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => { setSelectedTimeRange("24h"); setStartDate(undefined); setEndDate(undefined); }} />
                </Badge>
              )}

              {selectedLevels.map(level => (
                <Badge key={level} variant="secondary" className="flex items-center gap-1">
                  Level: {level}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => handleLevelChange(level)} />
                </Badge>
              ))}

              {selectedCategories.map(category => (
                <Badge key={category} variant="secondary" className="flex items-center gap-1">
                  Category: {category}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => handleCategoryChange(category)} />
                </Badge>
              ))}

              {selectedSources.map(source => (
                <Badge key={source} variant="secondary" className="flex items-center gap-1">
                  Source: {source}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => handleSourceChange(source)} />
                </Badge>
              ))}

              {entityType && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Entity Type: {entityType}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setEntityType("")} />
                </Badge>
              )}

              {entityId && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Entity ID: {entityId}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setEntityId("")} />
                </Badge>
              )}

              {searchQuery && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  Search: {searchQuery}
                  <X className="h-3 w-3 cursor-pointer" onClick={() => setSearchQuery("")} />
                </Badge>
              )}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center items-center h-64">
              <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <FileText className="mx-auto mb-4 h-8 w-8 text-muted-foreground" />
              <p className="mb-2 text-sm text-muted-foreground">No logs found</p>
              <p className="text-xs text-muted-foreground">Try adjusting your filters or search query</p>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={logs}
              showFilter={false}
            />
          )}

          {/* Pagination */}
          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-muted-foreground">
              Showing {logs.length} of {totalLogs} logs
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page => Math.max(1, page - 1))}
                disabled={page === 1 || loading}
              >
                Previous
              </Button>
              <span className="text-sm">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(page => Math.min(totalPages, page + 1))}
                disabled={page === totalPages || loading}
              >
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Log Statistics */}
      <LogStatistics />

      {/* Log Detail Dialog */}
      <LogDetailDialog
        log={selectedLog}
        open={detailsOpen}
        onOpenChange={setDetailsOpen}
      />
    </div>
  )
}
