"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/use-toast"
import { banCheckAPI, BanCheckTask } from "@/lib/api"
import { AdvancedOptionsDialog } from "../(authenticated)/bans/advanced-options-dialog"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, Upload, RefreshCw, Settings, FileText, Download } from "lucide-react"
import { DataTable } from "@/components/data-table"
import Link from "next/link"

// Configuration constants
const POLLING_INTERVAL_BASE_MS = 1000; // Base polling interval in milliseconds
const POLLING_INTERVAL_RANDOM_MS = 2000; // Random additional time to avoid rate limiting
const POLLING_RETRY_DELAY_MS = 5000; // Delay for retrying after errors
const POLLING_RATE_LIMIT_DELAY_MS = 10000; // Delay for retrying after rate limiting

export function PublicBansPageClient() {
  // State for the active tab
  const [activeTab, setActiveTab] = useState("steam-ids")

  // State for Steam IDs input
  const [steamIDs, setSteamIDs] = useState("")

  // State for CSV file
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [steamIdColumn, setSteamIdColumn] = useState("steam64_id")

  // State for advanced options
  const [advancedOptionsOpen, setAdvancedOptionsOpen] = useState(false)
  const [advancedOptions, setAdvancedOptions] = useState({
    use_auto_balancing: true,
    proxy_list_str: "",
    logical_batch_size: 20,
    max_concurrent_batches: 3,
    max_workers_per_batch: 3,
    inter_request_submit_delay: 0.1,
    max_retries_per_url: 2,
    retry_delay_seconds: 5.0
  })

  // State for loading and errors
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // State for current task and results
  const [currentTask, setCurrentTask] = useState<BanCheckTask | null>(null)
  const [statusFilter, setStatusFilter] = useState("all")

  // State for stored results
  const [storedResults, setStoredResults] = useState<BanCheckTask[]>([])
  const [selectedStoredResult, setSelectedStoredResult] = useState<BanCheckTask | null>(null)

  // Refs for file input and polling
  const fileInputRef = useRef<HTMLInputElement>(null)
  const activePollingRef = useRef<Record<string, boolean>>({})
  const pollingTimeoutsRef = useRef<Record<string, NodeJS.Timeout>>({})

  // Toast hook
  const { toast } = useToast()

  // Function to handle Steam IDs submission
  const handleSubmitSteamIDs = async () => {
    if (!steamIDs.trim()) {
      toast({
        title: "Error",
        description: "Please enter at least one Steam ID.",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Split the Steam IDs by newline and filter out empty lines
      const ids = steamIDs.split("\n").map(id => id.trim()).filter(id => id)

      // Submit the Steam IDs for checking
      const response = await banCheckAPI.checkSteamIDsPublic(ids, advancedOptions)

      // Show success message
      toast({
        title: "Success",
        description: `Task submitted successfully. ${ids.length} Steam IDs will be checked.`,
      })

      // Set the current task
      setCurrentTask(response)

      // Start polling for task status
      pollTaskStatus(response.task_id)
    } catch (err) {
      console.error("Error submitting Steam IDs:", err)
      setError("Failed to submit Steam IDs. Please try again.")
      toast({
        title: "Error",
        description: "Failed to submit Steam IDs. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Function to handle file change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setCsvFile(e.target.files[0])
    } else {
      setCsvFile(null)
    }
  }

  // Function to handle CSV submission
  const handleSubmitCSV = async () => {
    if (!csvFile) {
      toast({
        title: "Error",
        description: "Please select a CSV file.",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Submit the CSV file for checking
      const response = await banCheckAPI.checkCSVPublic(csvFile, steamIdColumn, advancedOptions)

      // Show success message
      toast({
        title: "Success",
        description: "CSV file submitted successfully.",
      })

      // Set the current task
      setCurrentTask(response)

      // Start polling for task status
      pollTaskStatus(response.task_id)
    } catch (err) {
      console.error("Error submitting CSV file:", err)
      setError("Failed to submit CSV file. Please try again.")
      toast({
        title: "Error",
        description: "Failed to submit CSV file. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Function to poll task status
  const pollTaskStatus = (taskId: string) => {
    // Mark this task as actively polling
    activePollingRef.current[taskId] = true;

    const pollTask = async () => {
      if (!activePollingRef.current[taskId]) {
        console.log(`Polling stopped for task ${taskId}`);
        return;
      }

      try {
        // Get task status
        const task = await banCheckAPI.getTaskPublic(taskId);

        // Update the current task
        setCurrentTask(task);

        // If the task is still in progress, continue polling
        if (task.status === "PENDING" || task.status === "PROCESSING") {
          // Calculate next polling interval with jitter to avoid rate limiting
          const jitter = Math.random() * POLLING_INTERVAL_RANDOM_MS;
          const nextPollMs = POLLING_INTERVAL_BASE_MS + jitter;

          // Schedule next poll
          const timeoutId = setTimeout(pollTask, nextPollMs);
          pollingTimeoutsRef.current[taskId] = timeoutId;
        } else {
          // Task is complete, stop polling
          stopPollingTaskStatus(taskId);

          // Store the completed task results in localStorage
          storeTaskResults(task);
        }
      } catch (err) {
        console.error(`Error polling task ${taskId}:`, err);

        // If there's an error, retry after a delay
        const timeoutId = setTimeout(pollTask, POLLING_RETRY_DELAY_MS);
        pollingTimeoutsRef.current[taskId] = timeoutId;
      }
    };

    // Start polling
    pollTask();
  };

  // Function to stop polling task status
  const stopPollingTaskStatus = (taskId: string) => {
    activePollingRef.current[taskId] = false;
  };

  // Function to clear polling timeout
  const clearPollingTimeout = (taskId: string) => {
    if (pollingTimeoutsRef.current[taskId]) {
      clearTimeout(pollingTimeoutsRef.current[taskId]);
      delete pollingTimeoutsRef.current[taskId];
    }
  };

  // Load stored results from localStorage on component mount
  useEffect(() => {
    try {
      const storedResultsJson = localStorage.getItem('banCheckResults');
      if (storedResultsJson) {
        const parsedResults = JSON.parse(storedResultsJson);
        setStoredResults(parsedResults);
      }
    } catch (error) {
      console.error('Error loading stored results from localStorage:', error);
    }
  }, []);

  // Store task results in localStorage when a task completes
  const storeTaskResults = (task: BanCheckTask) => {
    if (task.status === 'COMPLETED' && task.results && task.results.length > 0) {
      try {
        // Get existing stored results
        const storedResultsJson = localStorage.getItem('banCheckResults');
        let existingResults: BanCheckTask[] = [];

        if (storedResultsJson) {
          existingResults = JSON.parse(storedResultsJson);
        }

        // Check if this task is already stored
        const taskExists = existingResults.some(t => t.task_id === task.task_id);

        if (!taskExists) {
          // Add the new task to the stored results
          const updatedResults = [task, ...existingResults].slice(0, 10); // Keep only the 10 most recent results
          localStorage.setItem('banCheckResults', JSON.stringify(updatedResults));
          setStoredResults(updatedResults);
        }
      } catch (error) {
        console.error('Error storing task results in localStorage:', error);
      }
    }
  };

  // Clear all stored results
  const clearStoredResults = () => {
    try {
      localStorage.removeItem('banCheckResults');
      setStoredResults([]);
      setSelectedStoredResult(null);
      toast({
        title: "Success",
        description: "All saved results have been cleared.",
      });
    } catch (error) {
      console.error('Error clearing stored results:', error);
      toast({
        title: "Error",
        description: "Failed to clear saved results.",
        variant: "destructive",
      });
    }
  };

  // Export results to CSV
  const exportResultsToCSV = (results: any[]) => {
    try {
      if (!results || results.length === 0) {
        toast({
          title: "Error",
          description: "No results to export.",
          variant: "destructive",
        });
        return;
      }

      // Create CSV header
      const headers = ["steam_id", "status_summary", "details"];

      // Create CSV content
      let csvContent = headers.join(",") + "\n";

      // Add data rows
      results.forEach(result => {
        const row = [
          result.steam_id,
          result.status_summary,
          // Escape quotes in details to avoid breaking CSV format
          `"${(result.details || "").replace(/"/g, '""')}"`
        ];
        csvContent += row.join(",") + "\n";
      });

      // Create a blob and download link
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `ban-check-results-${new Date().toISOString().slice(0, 10)}.csv`);
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      toast({
        title: "Success",
        description: "Results exported to CSV.",
      });
    } catch (error) {
      console.error('Error exporting results to CSV:', error);
      toast({
        title: "Error",
        description: "Failed to export results.",
        variant: "destructive",
      });
    }
  };

  // Clean up polling when component unmounts
  useEffect(() => {
    return () => {
      console.log("Component unmounting, cleaning up all polling");
      // Stop all active polling and clear all timeouts
      Object.keys(activePollingRef.current).forEach(taskId => {
        console.log(`Cleaning up polling for task ${taskId}`);
        clearPollingTimeout(taskId);
        stopPollingTaskStatus(taskId);
      });
    };
  }, []);

  // Filter results based on status filter
  const filteredResults = currentTask?.results ? currentTask.results.filter(result => {
    if (statusFilter === "all") return true;
    if (statusFilter === "banned") {
      return result.status_summary.includes("BANNED") && !result.details.includes("No bans detected");
    }
    if (statusFilter === "clean") {
      return result.status_summary.includes("CLEAN") || result.details.includes("No bans detected");
    }
    return true;
  }) : [];

  return (
    <div className="space-y-6 mt-2">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Public Steam Ban Checker</h1>
        <div className="flex items-center space-x-2">
          <Link href="/auth/login">
            <Button variant="outline">
              Sign In
            </Button>
          </Link>
          <Link href="/auth/register">
            <Button>
              Register
            </Button>
          </Link>
        </div>
      </div>

      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              You are using the public version of the ban checker. Sign in to save your tasks and access them later.
            </p>
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="steam-ids">Check Steam IDs</TabsTrigger>
          <TabsTrigger value="csv">Check CSV File</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        {/* Steam IDs Tab */}
        <TabsContent value="steam-ids" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Check Steam IDs</CardTitle>
              <CardDescription>
                Enter Steam IDs to check for bans, one per line.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="steam-ids">Steam IDs</Label>
                <Textarea
                  id="steam-ids"
                  placeholder="Enter Steam IDs, one per line"
                  value={steamIDs}
                  onChange={(e) => setSteamIDs(e.target.value)}
                  disabled={loading}
                  className="min-h-[200px]"
                />
                <p className="text-xs text-muted-foreground">
                  Enter Steam IDs in any format (Steam64, Steam32, etc.)
                </p>
              </div>

              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => setAdvancedOptionsOpen(true)}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Advanced Options
                </Button>

                <Button
                  onClick={handleSubmitSteamIDs}
                  disabled={loading || !steamIDs.trim()}
                >
                  {loading ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="mr-2 h-4 w-4" />
                  )}
                  Check Bans
                </Button>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Current Task Status */}
          {currentTask && (
            <Card>
              <CardHeader>
                <CardTitle>Current Task Status</CardTitle>
                <CardDescription>
                  {currentTask.task_id}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Status: {currentTask.status}</p>
                    <p className="text-sm text-muted-foreground">{currentTask.message}</p>
                  </div>
                  {(currentTask.status === "PENDING" || currentTask.status === "PROCESSING") && (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  )}
                </div>

                {typeof currentTask.progress === 'number' && (
                  <Progress value={currentTask.progress * 100} />
                )}

                {currentTask.results && currentTask.results.length > 0 && (
                  <div className="space-y-5">
                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => exportResultsToCSV(currentTask.results)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Export to CSV
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Total Checked</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold">{currentTask.results.length}</p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Banned</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold text-red-500">
                            {currentTask.results.filter(r =>
                              r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                            ).length}
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Clean</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold text-green-500">
                            {currentTask.results.filter(r =>
                              r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                            ).length}
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Error</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold text-yellow-500">
                            {currentTask.results.filter(r =>
                              r.status_summary.includes("ERROR")
                            ).length}
                          </p>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Custom filter component */}
                    <div className="flex items-center space-x-2">
                      <label htmlFor="status-filter" className="text-sm font-medium">
                        Status:
                      </label>
                      <select
                        id="status-filter"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="p-2 border rounded-md text-sm"
                      >
                        <option value="all">All ({currentTask.results.length})</option>
                        <option value="banned">Banned ({currentTask.results.filter(r =>
                          r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                        ).length})</option>
                        <option value="clean">Clean ({currentTask.results.filter(r =>
                          r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                        ).length})</option>
                      </select>
                    </div>

                    {/* Results table */}
                    <DataTable
                      columns={[
                        {
                          accessorKey: "steam_id",
                          header: "Steam ID",
                        },
                        {
                          accessorKey: "status_summary",
                          header: "Status",
                          cell: ({ row }) => {
                            const status = row.getValue("status_summary") as string;
                            let color = "text-gray-500";
                            if (status.includes("BANNED")) color = "text-red-500";
                            if (status.includes("CLEAN")) color = "text-green-500";
                            if (status.includes("ERROR")) color = "text-yellow-500";
                            return <span className={color}>{status}</span>;
                          },
                        },
                        {
                          accessorKey: "details",
                          header: "Details",
                        },
                        {
                          id: "actions",
                          cell: ({ row }) => {
                            const steamId = row.getValue("steam_id") as string;
                            return (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(`https://steamcommunity.com/profiles/${steamId}`, "_blank")}
                              >
                                View Profile
                              </Button>
                            );
                          },
                        },
                      ]}
                      data={filteredResults}
                      filterColumn="steam_id"
                      filterPlaceholder="Filter by Steam ID..."
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* CSV Tab */}
        <TabsContent value="csv" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Check CSV File</CardTitle>
              <CardDescription>
                Upload a CSV file containing Steam IDs to check for bans.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="csv-file">CSV File</Label>
                <Input
                  id="csv-file"
                  type="file"
                  accept=".csv"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  disabled={loading}
                />
                <p className="text-xs text-muted-foreground">
                  CSV file should have a column containing Steam IDs.
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="steam-id-column">Steam ID Column Name</Label>
                <Input
                  id="steam-id-column"
                  placeholder="Column name containing Steam IDs"
                  value={steamIdColumn}
                  onChange={(e) => setSteamIdColumn(e.target.value)}
                  disabled={loading}
                />
                <p className="text-xs text-muted-foreground">
                  Default: steam64_id
                </p>
              </div>

              <div className="flex justify-between">
                <Button
                  variant="outline"
                  onClick={() => setAdvancedOptionsOpen(true)}
                >
                  <Settings className="mr-2 h-4 w-4" />
                  Advanced Options
                </Button>

                <Button
                  onClick={handleSubmitCSV}
                  disabled={loading || !csvFile}
                >
                  {loading ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Upload className="mr-2 h-4 w-4" />
                  )}
                  Upload and Check
                </Button>
              </div>

              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Current Task Status */}
          {currentTask && (
            <Card>
              <CardHeader>
                <CardTitle>Current Task Status</CardTitle>
                <CardDescription>
                  {currentTask.task_id}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Same content as in the Steam IDs tab */}
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Status: {currentTask.status}</p>
                    <p className="text-sm text-muted-foreground">{currentTask.message}</p>
                  </div>
                  {(currentTask.status === "PENDING" || currentTask.status === "PROCESSING") && (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  )}
                </div>

                {typeof currentTask.progress === 'number' && (
                  <Progress value={currentTask.progress * 100} />
                )}

                {/* Results section */}
                {currentTask.results && currentTask.results.length > 0 && (
                  <div className="space-y-5">
                    <div className="flex justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => exportResultsToCSV(currentTask.results)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Export to CSV
                      </Button>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Total Checked</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold">{currentTask.results.length}</p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Banned</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold text-red-500">
                            {currentTask.results.filter(r =>
                              r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                            ).length}
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Clean</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold text-green-500">
                            {currentTask.results.filter(r =>
                              r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                            ).length}
                          </p>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="p-4">
                          <CardTitle className="text-sm">Error</CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <p className="text-2xl font-bold text-yellow-500">
                            {currentTask.results.filter(r =>
                              r.status_summary.includes("ERROR")
                            ).length}
                          </p>
                        </CardContent>
                      </Card>
                    </div>

                    {/* Custom filter component */}
                    <div className="flex items-center space-x-2">
                      <label htmlFor="status-filter-csv" className="text-sm font-medium">
                        Status:
                      </label>
                      <select
                        id="status-filter-csv"
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="p-2 border rounded-md text-sm"
                      >
                        <option value="all">All ({currentTask.results.length})</option>
                        <option value="banned">Banned ({currentTask.results.filter(r =>
                          r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                        ).length})</option>
                        <option value="clean">Clean ({currentTask.results.filter(r =>
                          r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                        ).length})</option>
                      </select>
                    </div>

                    {/* Results table */}
                    <DataTable
                      columns={[
                        {
                          accessorKey: "steam_id",
                          header: "Steam ID",
                        },
                        {
                          accessorKey: "status_summary",
                          header: "Status",
                          cell: ({ row }) => {
                            const status = row.getValue("status_summary") as string;
                            let color = "text-gray-500";
                            if (status.includes("BANNED")) color = "text-red-500";
                            if (status.includes("CLEAN")) color = "text-green-500";
                            if (status.includes("ERROR")) color = "text-yellow-500";
                            return <span className={color}>{status}</span>;
                          },
                        },
                        {
                          accessorKey: "details",
                          header: "Details",
                        },
                        {
                          id: "actions",
                          cell: ({ row }) => {
                            const steamId = row.getValue("steam_id") as string;
                            return (
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => window.open(`https://steamcommunity.com/profiles/${steamId}`, "_blank")}
                              >
                                View Profile
                              </Button>
                            );
                          },
                        },
                      ]}
                      data={filteredResults}
                      filterColumn="steam_id"
                      filterPlaceholder="Filter by Steam ID..."
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
        {/* Results Tab */}
        <TabsContent value="results" className="space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div>
                <CardTitle>Saved Results</CardTitle>
                <CardDescription>
                  View results from your previous ban checks. These are stored locally in your browser.
                </CardDescription>
              </div>
              {storedResults.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearStoredResults}
                >
                  Clear All Results
                </Button>
              )}
            </CardHeader>
            <CardContent className="space-y-5">
              {storedResults.length === 0 ? (
                <div className="text-center p-8">
                  <p className="text-muted-foreground">No saved results found. Check some Steam IDs or upload a CSV file to see results here.</p>
                </div>
              ) : (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="saved-results">Select a saved result</Label>
                    <select
                      id="saved-results"
                      className="w-full p-2 border rounded-md"
                      value={selectedStoredResult?.task_id || ""}
                      onChange={(e) => {
                        const selected = storedResults.find(r => r.task_id === e.target.value);
                        setSelectedStoredResult(selected || null);
                        setStatusFilter("all");
                      }}
                    >
                      <option value="">-- Select a result --</option>
                      {storedResults.map((result) => (
                        <option key={result.task_id} value={result.task_id}>
                          {new Date(result.created_at || Date.now()).toLocaleString()} - {result.results?.length || 0} Steam IDs
                        </option>
                      ))}
                    </select>
                  </div>

                  {selectedStoredResult && selectedStoredResult.results && selectedStoredResult.results.length > 0 && (
                    <div className="space-y-5">
                      <div className="flex justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => exportResultsToCSV(selectedStoredResult.results)}
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Export to CSV
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Total Checked</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold">{selectedStoredResult.results.length}</p>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Banned</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold text-red-500">
                              {selectedStoredResult.results.filter(r =>
                                r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                              ).length}
                            </p>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Clean</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold text-green-500">
                              {selectedStoredResult.results.filter(r =>
                                r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                              ).length}
                            </p>
                          </CardContent>
                        </Card>

                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Error</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold text-yellow-500">
                              {selectedStoredResult.results.filter(r =>
                                r.status_summary.includes("ERROR")
                              ).length}
                            </p>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Custom filter component */}
                      <div className="flex items-center space-x-2">
                        <label htmlFor="status-filter-results" className="text-sm font-medium">
                          Status:
                        </label>
                        <select
                          id="status-filter-results"
                          value={statusFilter}
                          onChange={(e) => setStatusFilter(e.target.value)}
                          className="p-2 border rounded-md text-sm"
                        >
                          <option value="all">All ({selectedStoredResult.results.length})</option>
                          <option value="banned">Banned ({selectedStoredResult.results.filter(r =>
                            r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                          ).length})</option>
                          <option value="clean">Clean ({selectedStoredResult.results.filter(r =>
                            r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                          ).length})</option>
                        </select>
                      </div>

                      {/* Results table */}
                      <DataTable
                        columns={[
                          {
                            accessorKey: "steam_id",
                            header: "Steam ID",
                          },
                          {
                            accessorKey: "status_summary",
                            header: "Status",
                            cell: ({ row }) => {
                              const status = row.getValue("status_summary") as string;
                              let color = "text-gray-500";
                              if (status.includes("BANNED")) color = "text-red-500";
                              if (status.includes("CLEAN")) color = "text-green-500";
                              if (status.includes("ERROR")) color = "text-yellow-500";
                              return <span className={color}>{status}</span>;
                            },
                          },
                          {
                            accessorKey: "details",
                            header: "Details",
                          },
                          {
                            id: "actions",
                            cell: ({ row }) => {
                              const steamId = row.getValue("steam_id") as string;
                              return (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => window.open(`https://steamcommunity.com/profiles/${steamId}`, "_blank")}
                                >
                                  View Profile
                                </Button>
                              );
                            },
                          },
                        ]}
                        data={selectedStoredResult.results.filter(result => {
                          if (statusFilter === "all") return true;
                          if (statusFilter === "banned") {
                            return result.status_summary.includes("BANNED") && !result.details.includes("No bans detected");
                          }
                          if (statusFilter === "clean") {
                            return result.status_summary.includes("CLEAN") || result.details.includes("No bans detected");
                          }
                          return true;
                        })}
                        filterColumn="steam_id"
                        filterPlaceholder="Filter by Steam ID..."
                      />
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Advanced Options Dialog */}
      <AdvancedOptionsDialog
        open={advancedOptionsOpen}
        onOpenChange={setAdvancedOptionsOpen}
        options={advancedOptions}
        onOptionsChange={setAdvancedOptions}
      />
    </div>
  )
}
