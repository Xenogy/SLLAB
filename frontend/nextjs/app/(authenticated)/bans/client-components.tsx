"use client"

import { useState, useEffect, useRef, useMemo } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { DataTable } from "@/components/data-table"
import { useToast } from "@/components/ui/use-toast"
import { banCheckAPI, BanCheckTask } from "@/lib/api"
import { createColumns } from "./columns"
import { AdvancedOptionsDialog } from "./advanced-options-dialog"
import { ExportResultsDialog } from "./export-results-dialog"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle, Upload, RefreshCw, Settings, FileText, Download } from "lucide-react"

// Configuration constants
const POLLING_INTERVAL_BASE_MS = 1000; // Base polling interval in milliseconds
const POLLING_INTERVAL_RANDOM_MS = 2000; // Random additional time to avoid rate limiting
const POLLING_RETRY_DELAY_MS = 5000; // Delay for retrying after errors
const POLLING_RATE_LIMIT_DELAY_MS = 10000; // Delay for retrying after rate limiting

export function BansPageClient() {
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

  // State for export dialog
  const [exportDialogOpen, setExportDialogOpen] = useState(false)

  // State for tasks
  const [tasks, setTasks] = useState<BanCheckTask[]>([])
  const [selectedTask, setSelectedTask] = useState<BanCheckTask | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // State for results filtering
  const [statusFilter, setStatusFilter] = useState<string>("all")

  // State for polling control - for UI updates (showing polling indicators)
  const [activePolling, setActivePolling] = useState<{[key: string]: boolean}>({})

  // Ref for tracking active polling - for immediate access in async functions
  const activePollingRef = useRef<{[key: string]: boolean}>({})

  // Toast for notifications
  const { toast } = useToast()

  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Computed property for deduplicated tasks
  const uniqueTasks = useMemo(() => {
    return Array.from(new Map(tasks.map(task => [task.task_id, task])).values());
  }, [tasks]);

  // Fetch tasks on component mount
  useEffect(() => {
    fetchTasks()

    // Set up interval to refresh tasks every 30 seconds
    const intervalId = setInterval(() => {
      fetchTasks()
    }, 30000)

    // Clean up interval on unmount
    return () => clearInterval(intervalId)
  }, [])

  // Function to fetch tasks
  const fetchTasks = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await banCheckAPI.getTasks({
        limit: 50 // Increase the limit to get more tasks
      })

      // Merge new tasks with existing tasks, preserving existing ones
      setTasks(prevTasks => {
        // Create a map of existing tasks by task_id
        const existingTasksMap = new Map(prevTasks.map(task => [task.task_id, task]));

        // Add or update tasks from the response
        response.tasks.forEach(task => {
          existingTasksMap.set(task.task_id, task);
        });

        // Convert map back to array
        return Array.from(existingTasksMap.values());
      });
    } catch (err) {
      console.error("Error fetching tasks:", err)
      setError("Failed to fetch tasks. Please try again.")
      toast({
        title: "Error",
        description: "Failed to fetch tasks. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

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
      const response = await banCheckAPI.checkSteamIDs(ids, advancedOptions)

      // Show success message
      toast({
        title: "Success",
        description: `Task submitted successfully. ${ids.length} Steam IDs will be checked.`,
      })

      // Add the new task to the tasks list
      setTasks(prevTasks => {
        // Check if the task already exists in the list
        const taskExists = prevTasks.some(t => t.task_id === response.task_id);
        if (taskExists) {
          // If it exists, update it
          return prevTasks.map(t => t.task_id === response.task_id ? response : t);
        } else {
          // If it doesn't exist, add it
          return [...prevTasks, response];
        }
      });

      // Select the new task and switch to results tab
      // Use a slight delay to ensure the task is in the list
      setTimeout(() => {
        handleTaskSelect(response);
      }, 500);
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

  // Function to handle CSV file submission
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
      const response = await banCheckAPI.checkCSV(csvFile, steamIdColumn, advancedOptions)

      // Show success message
      toast({
        title: "Success",
        description: "CSV file submitted successfully.",
      })

      // Add the new task to the tasks list
      setTasks(prevTasks => {
        // Check if the task already exists in the list
        const taskExists = prevTasks.some(t => t.task_id === response.task_id);
        if (taskExists) {
          // If it exists, update it
          return prevTasks.map(t => t.task_id === response.task_id ? response : t);
        } else {
          // If it doesn't exist, add it
          return [...prevTasks, response];
        }
      });

      // Select the new task and switch to results tab
      // Use a slight delay to ensure the task is in the list
      setTimeout(() => {
        handleTaskSelect(response);
      }, 500);
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

  // Function to handle file change
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setCsvFile(e.target.files[0])
    }
  }

  // Function to handle task selection
  const handleTaskSelect = async (task: BanCheckTask) => {
    // Always fetch the full task details to ensure we have the latest data
    try {
      setLoading(true)

      // Make sure the task exists in the tasks list
      const taskExists = tasks.some(t => t.task_id === task.task_id);
      if (!taskExists) {
        // If the task doesn't exist in the list, add it
        setTasks(prevTasks => [...prevTasks, task]);
      }

      // Fetch the full task details
      console.log(`Fetching full details for task ${task.task_id}`);
      const fullTask = await banCheckAPI.getTask(task.task_id);
      console.log(`Received full task details for ${task.task_id}, status: ${fullTask.status}`);

      // Update the task in the tasks list to keep it in sync
      setTasks(prevTasks =>
        prevTasks.map(t =>
          t.task_id === task.task_id ? fullTask : t
        )
      );

      // Switch to the Results tab
      setActiveTab("results");

      // Set the selected task - this will trigger the useEffect that starts polling
      console.log(`Setting selectedTask to task ${fullTask.task_id} with status ${fullTask.status}`);
      setSelectedTask(fullTask);

      // Note: We don't need to call startPollingTaskStatus here as the useEffect will handle it
      console.log(`Task selection complete for ${fullTask.task_id}`)
    } catch (err) {
      console.error("Error fetching task details:", err)
      toast({
        title: "Error",
        description: "Failed to fetch task details. Please try again.",
        variant: "destructive",
      })
      // Still set the selected task even if we couldn't fetch the full details
      console.log(`Error fetching task details, using original task data for ${task.task_id}`);
      setSelectedTask(task);
      setActiveTab("results");

      // Note: The useEffect will handle starting the polling if needed
      console.log(`Task selection completed with error for ${task.task_id}, status: ${task.status}`)
    } finally {
      setLoading(false)
    }
  }

  // Function to start polling for task updates
  const startPollingTaskStatus = (taskId: string) => {
    console.log(`startPollingTaskStatus called for task ${taskId}`);

    // If already polling this task, don't start another polling process
    if (activePollingRef.current[taskId]) {
      console.log(`Already polling task ${taskId}, skipping`);
      return;
    }

    console.log(`Starting new polling for task ${taskId}`);

    // Mark this task as being polled in both state and ref
    activePollingRef.current[taskId] = true;

    setActivePolling(prev => {
      console.log(`Setting activePolling[${taskId}] = true, current state:`, prev);
      return {...prev, [taskId]: true};
    });

    // Start the polling process immediately
    console.log(`Calling pollTaskStatus for task ${taskId}`);
    pollTaskStatus(taskId);
  }

  // Function to stop polling for task updates
  const stopPollingTaskStatus = (taskId: string) => {
    console.log(`Stopping polling for task ${taskId}`);

    // Clear any pending timeout for this task
    clearPollingTimeout(taskId);

    // Remove from active polling ref immediately
    delete activePollingRef.current[taskId];

    // Remove from active polling state (for UI updates)
    setActivePolling(prev => {
      const newPolling = {...prev};
      delete newPolling[taskId];
      return newPolling;
    });
  }

  // Function to poll for task updates
  const pollTaskStatus = async (taskId: string) => {
    console.log(`pollTaskStatus called for task ${taskId}, activePollingRef:`, activePollingRef.current);

    // If polling has been stopped for this task, exit
    if (!activePollingRef.current[taskId]) {
      console.log(`Task ${taskId} is not in activePollingRef, exiting poll function`);
      return;
    }

    console.log(`Starting poll cycle for task ${taskId}`);

    try {
      // Add a random delay to avoid rate limiting
      const pollInterval = POLLING_INTERVAL_BASE_MS + Math.floor(Math.random() * POLLING_INTERVAL_RANDOM_MS);
      console.log(`Poll interval for task ${taskId}: ${pollInterval}ms`);

      console.log(`Fetching task ${taskId} from API...`);
      const task = await banCheckAPI.getTask(taskId);
      console.log(`Received task ${taskId} from API with status: ${task.status}`);

      // Update the selected task
      if (selectedTask && selectedTask.task_id === taskId) {
        setSelectedTask(task);
      }

      // Update the task in the tasks list
      setTasks(prevTasks => {
        // Find the task in the list
        const taskIndex = prevTasks.findIndex(t => t.task_id === taskId);

        // If the task is not in the list, add it
        if (taskIndex === -1) {
          console.log(`Adding task ${taskId} to tasks list`);
          return [...prevTasks, task];
        }

        // Otherwise, update it
        console.log(`Updating task ${taskId} in tasks list`);
        const updatedTasks = [...prevTasks];
        updatedTasks[taskIndex] = task;
        return updatedTasks;
      });

      // Continue polling if the task is still in progress
      if (task.status === "PENDING" || task.status === "PROCESSING") {
        console.log(`Task ${taskId} still in progress (${task.status}), polling again in ${pollInterval/1000} seconds`);

        // Clear any existing timeout
        clearPollingTimeout(taskId);

        // Set new timeout and store the reference
        pollingTimeoutsRef.current[taskId] = setTimeout(() => {
          // Check if we're still supposed to be polling before calling again
          if (activePollingRef.current[taskId]) {
            pollTaskStatus(taskId);
          } else {
            console.log(`Polling was stopped for task ${taskId} during timeout`);
          }
        }, pollInterval);
      } else {
        // If the task is completed, stop polling
        console.log(`Task ${taskId} completed with status: ${task.status}, stopping polling`);
        clearPollingTimeout(taskId);
        stopPollingTaskStatus(taskId);
      }
    } catch (error) {
      console.error(`Error polling task ${taskId} status:`, error);

      // If we get rate limited, try again after a longer delay
      if (error instanceof Error && error.toString().includes("429")) {
        console.log(`Rate limited for task ${taskId}, retrying after ${POLLING_RATE_LIMIT_DELAY_MS/1000} seconds`);

        // Clear any existing timeout
        clearPollingTimeout(taskId);

        // Set new timeout with longer delay
        pollingTimeoutsRef.current[taskId] = setTimeout(() => {
          // Check if we're still supposed to be polling before calling again
          if (activePollingRef.current[taskId]) {
            pollTaskStatus(taskId);
          }
        }, POLLING_RATE_LIMIT_DELAY_MS);
      } else {
        // For other errors, retry after a standard delay
        console.log(`Error for task ${taskId}, retrying after ${POLLING_RETRY_DELAY_MS/1000} seconds`);

        // Clear any existing timeout
        clearPollingTimeout(taskId);

        // Set new timeout
        pollingTimeoutsRef.current[taskId] = setTimeout(() => {
          // Check if we're still supposed to be polling before calling again
          if (activePollingRef.current[taskId]) {
            pollTaskStatus(taskId);
          }
        }, POLLING_RETRY_DELAY_MS);
      }
    }
  }

  // Start polling when a task is selected
  useEffect(() => {
    console.log("selectedTask useEffect triggered, selectedTask:", selectedTask?.task_id, "status:", selectedTask?.status);

    if (selectedTask && (selectedTask.status === "PENDING" || selectedTask.status === "PROCESSING")) {
      console.log(`Task ${selectedTask.task_id} is in progress, starting polling`);
      startPollingTaskStatus(selectedTask.task_id);
    } else if (selectedTask) {
      console.log(`Task ${selectedTask.task_id} is not in progress (status: ${selectedTask.status}), not polling`);
    }
  }, [selectedTask])

  // Store polling timeouts to clear them when needed
  const pollingTimeoutsRef = useRef<{[key: string]: NodeJS.Timeout}>({});

  // Enhanced version of stopPollingTaskStatus that also clears timeouts
  const clearPollingTimeout = (taskId: string) => {
    // Clear any pending timeout for this task
    if (pollingTimeoutsRef.current[taskId]) {
      console.log(`Clearing timeout for task ${taskId}`);
      clearTimeout(pollingTimeoutsRef.current[taskId]);
      delete pollingTimeoutsRef.current[taskId];
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

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Steam Ban Checker</h1>
        <Button variant="outline" onClick={fetchTasks} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="steam-ids">Check Steam IDs</TabsTrigger>
          <TabsTrigger value="csv">Check CSV File</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        {/* Steam IDs Tab */}
        <TabsContent value="steam-ids" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Check Steam IDs</CardTitle>
              <CardDescription>
                Enter Steam IDs to check for bans, one per line.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="steam-ids">Steam IDs</Label>
                <Textarea
                  id="steam-ids"
                  placeholder="Enter Steam IDs, one per line"
                  value={steamIDs}
                  onChange={(e) => setSteamIDs(e.target.value)}
                  rows={10}
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground">
                  Example: 76561198000000001
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

          <Card>
            <CardHeader>
              <CardTitle>Recent Tasks</CardTitle>
              <CardDescription>
                View your recent ban check tasks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={createColumns({
                  onSelect: handleTaskSelect,
                })}
                data={uniqueTasks}
                filterColumn="task_id"
                filterPlaceholder="Filter by task ID..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* CSV Tab */}
        <TabsContent value="csv" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Check CSV File</CardTitle>
              <CardDescription>
                Upload a CSV file containing Steam IDs to check for bans.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
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

          <Card>
            <CardHeader>
              <CardTitle>Recent Tasks</CardTitle>
              <CardDescription>
                View your recent ban check tasks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={createColumns({
                  onSelect: handleTaskSelect,
                })}
                data={uniqueTasks}
                filterColumn="task_id"
                filterPlaceholder="Filter by task ID..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Results Tab */}
        <TabsContent value="results" className="space-y-4">
          {uniqueTasks.length > 0 ? (
            <>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>Task Details</CardTitle>
                    <CardDescription>
                      {selectedTask ? `Details for task ${selectedTask.task_id}` : "Select a task to view details"}
                    </CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Label htmlFor="task-selector" className="mr-2">Select Task:</Label>
                    <select
                      id="task-selector"
                      className="p-2 border rounded-md"
                      value={selectedTask?.task_id || ""}
                      onChange={(e) => {
                        const taskId = e.target.value;
                        const task = uniqueTasks.find(t => t.task_id === taskId);
                        if (task) {
                          handleTaskSelect(task);
                        }
                      }}
                    >
                      <option value="" disabled>Select a task</option>
                      {uniqueTasks.map(task => (
                        <option key={task.task_id} value={task.task_id}>
                          {task.task_id.substring(0, 8)}... ({task.status || "Unknown"})
                          {activePolling[task.task_id] ? " (Polling...)" : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                </CardHeader>
                {selectedTask ? (
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium">Status</p>
                        <p className="text-sm">
                          {selectedTask.status === "COMPLETED" && (
                            <span className="text-green-500">Completed</span>
                          )}
                          {selectedTask.status === "PROCESSING" && (
                            <span className="text-blue-500">
                              Processing {activePolling[selectedTask.task_id] && "(Polling...)"}
                            </span>
                          )}
                          {selectedTask.status === "PENDING" && (
                            <span className="text-yellow-500">
                              Pending {activePolling[selectedTask.task_id] && "(Polling...)"}
                            </span>
                          )}
                          {selectedTask.status === "FAILED" && (
                            <span className="text-red-500">Failed</span>
                          )}
                          {!selectedTask.status && (
                            <span className="text-gray-500">Unknown</span>
                          )}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Created At</p>
                        <p className="text-sm">
                          {selectedTask.created_at ? new Date(selectedTask.created_at).toLocaleString() : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Updated At</p>
                        <p className="text-sm">
                          {selectedTask.updated_at ? new Date(selectedTask.updated_at).toLocaleString() : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Message</p>
                        <p className="text-sm">{selectedTask.message || "N/A"}</p>
                      </div>
                    </div>

                    {selectedTask.status && (selectedTask.status === "PROCESSING" || selectedTask.status === "PENDING") && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Progress</span>
                          <span>{selectedTask.progress ? `${Math.round(selectedTask.progress)}%` : "0%"}</span>
                        </div>
                        <Progress value={selectedTask.progress || 0} />
                      </div>
                    )}
                  </CardContent>
                ) : (
                  <CardContent>
                    <p className="text-center text-muted-foreground">Please select a task to view details</p>
                  </CardContent>
                )}
              </Card>

              {selectedTask && selectedTask.results && selectedTask.results.length > 0 && (
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div>
                      <CardTitle>Results</CardTitle>
                      <CardDescription>
                        Ban check results for {selectedTask.results.length} Steam IDs
                      </CardDescription>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setExportDialogOpen(true)}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Export
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Total Checked</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold">{selectedTask.results.length}</p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Banned</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold text-red-500">
                              {selectedTask.results.filter(r =>
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
                              {selectedTask.results.filter(r =>
                                r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                              ).length}
                            </p>
                          </CardContent>
                        </Card>
                        <Card>
                          <CardHeader className="p-4">
                            <CardTitle className="text-sm">Private/Error</CardTitle>
                          </CardHeader>
                          <CardContent className="p-4 pt-0">
                            <p className="text-2xl font-bold text-yellow-500">
                              {selectedTask.results.filter(r =>
                                r.status_summary.includes("PRIVATE") ||
                                r.status_summary.includes("ERROR")
                              ).length}
                            </p>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Status filter */}
                      {selectedTask && selectedTask.results && (
                        <>
                          {/* Filter the results based on the selected status */}
                          {(() => {
                            const filteredResults = selectedTask.results.filter(result => {
                              if (statusFilter === "all") return true;

                              const status = result.status_summary;
                              const details = result.details;

                              const isClean = details.includes("No bans detected") || status.includes("CLEAN");
                              const isBanned = status.includes("BANNED") && !details.includes("No bans detected");
                              const isPrivate = status.includes("PRIVATE");
                              const isError = status.includes("ERROR");

                              switch (statusFilter) {
                                case "banned": return isBanned;
                                case "clean": return isClean;
                                case "private": return isPrivate;
                                case "error": return isError;
                                default: return true;
                              }
                            });

                            // Custom filter component
                            const statusFilterComponent = (
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
                                  <option value="all">All ({selectedTask.results.length})</option>
                                  <option value="banned">Banned ({selectedTask.results.filter(r =>
                                    r.status_summary.includes("BANNED") && !r.details.includes("No bans detected")
                                  ).length})</option>
                                  <option value="clean">Clean ({selectedTask.results.filter(r =>
                                    r.status_summary.includes("CLEAN") || r.details.includes("No bans detected")
                                  ).length})</option>
                                  <option value="private">Private ({selectedTask.results.filter(r =>
                                    r.status_summary.includes("PRIVATE")
                                  ).length})</option>
                                  <option value="error">Error ({selectedTask.results.filter(r =>
                                    r.status_summary.includes("ERROR")
                                  ).length})</option>
                                </select>
                              </div>
                            );

                            return (
                              <>
                                <div className="mb-2 text-sm text-gray-500">
                                  Showing {filteredResults.length} of {selectedTask.results.length} results
                                  {statusFilter !== "all" && ` (filtered by: ${statusFilter})`}
                                </div>
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
                                      const details = row.getValue("details") as string;

                                      // Check if the details explicitly mention "No bans detected"
                                      const isClean = details.includes("No bans detected") || status.includes("CLEAN");
                                      const isBanned = status.includes("BANNED") && !details.includes("No bans detected");
                                      const isPrivate = status.includes("PRIVATE");
                                      const isError = status.includes("ERROR");

                                      return (
                                        <div>
                                          {isBanned && (
                                            <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded">
                                              Banned
                                            </span>
                                          )}
                                          {isClean && (
                                            <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">
                                              Clean
                                            </span>
                                          )}
                                          {isPrivate && (
                                            <span className="bg-yellow-100 text-yellow-800 text-xs font-medium px-2.5 py-0.5 rounded">
                                              Private
                                            </span>
                                          )}
                                          {isError && (
                                            <span className="bg-gray-100 text-gray-800 text-xs font-medium px-2.5 py-0.5 rounded">
                                              Error
                                            </span>
                                          )}
                                        </div>
                                      );
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
                                customFilters={statusFilterComponent}
                              />
                              </>
                            );
                          })()}
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">
                  {uniqueTasks.length === 0
                    ? "No tasks found. Create a new task by checking Steam IDs or uploading a CSV file."
                    : "Please select a task from the dropdown above to view results."}
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Advanced Options Dialog */}
      <AdvancedOptionsDialog
        open={advancedOptionsOpen}
        onOpenChange={setAdvancedOptionsOpen}
        options={advancedOptions}
        onOptionsChange={setAdvancedOptions}
      />

      {/* Export Results Dialog */}
      {selectedTask && selectedTask.results && (
        <ExportResultsDialog
          isOpen={exportDialogOpen}
          onClose={() => setExportDialogOpen(false)}
          results={selectedTask.results}
          taskId={selectedTask.task_id}
        />
      )}
    </div>
  )
}
