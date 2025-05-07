"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { RefreshCw, Trash2 } from "lucide-react"
import { logsAPI } from "@/lib/logs-api"
import { useToast } from "@/components/ui/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"

export function LogsCleanup() {
  const { toast } = useToast()
  const [loading, setLoading] = useState(false)
  const [dryRun, setDryRun] = useState(true)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [cleanupStats, setCleanupStats] = useState<{
    dry_run: boolean,
    deleted_count?: number,
    would_delete_count?: number,
    counts_by_level?: Array<{ level: string, retention_days: number, count: number }>
  } | null>(null)

  const handleCleanup = async () => {
    setLoading(true)
    try {
      const result = await logsAPI.cleanupLogs(dryRun)
      setCleanupStats(result)

      if (dryRun) {
        toast({
          title: "Dry Run Completed",
          description: `Would delete ${result.would_delete_count} log entries.`,
        })
      } else {
        toast({
          title: "Logs Cleaned Up",
          description: `Successfully deleted ${result.deleted_count} log entries.`,
        })
      }
    } catch (error) {
      console.error("Error cleaning up logs:", error)
      toast({
        title: "Error",
        description: "Failed to clean up logs. Please try again.",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
      setConfirmOpen(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Log Cleanup</CardTitle>
        <CardDescription>
          Clean up old logs based on retention policies
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Switch
              id="dry-run"
              checked={dryRun}
              onCheckedChange={setDryRun}
            />
            <Label htmlFor="dry-run">Dry Run (simulate cleanup without deleting)</Label>
          </div>

          <div className="text-sm text-muted-foreground">
            <p>Log cleanup will delete old logs based on the configured retention policies:</p>
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>DEBUG logs: 7 days</li>
              <li>INFO logs: 30 days</li>
              <li>WARNING logs: 90 days</li>
              <li>ERROR and CRITICAL logs: 365 days</li>
              <li>Security and Audit logs: 730 days (2 years)</li>
            </ul>
          </div>

          {cleanupStats && (
            <div className="mt-4 p-4 border rounded-md bg-muted/20">
              <h4 className="font-medium mb-2">
                {cleanupStats.dry_run ? "Dry Run Results" : "Cleanup Results"}
              </h4>

              {cleanupStats.dry_run ? (
                <>
                  <p className="text-sm mb-2">
                    Would delete <span className="font-bold">{cleanupStats.would_delete_count}</span> log entries
                  </p>

                  {cleanupStats.counts_by_level && cleanupStats.counts_by_level.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium mb-1">Breakdown by level:</p>
                      <ul className="text-xs space-y-1">
                        {cleanupStats.counts_by_level.map((item, index) => (
                          <li key={index} className="flex justify-between">
                            <span>{item.level} logs (older than {item.retention_days} days):</span>
                            <span className="font-medium">{item.count}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <p className="text-sm">
                  Successfully deleted <span className="font-bold">{cleanupStats.deleted_count}</span> log entries
                </p>
              )}
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter>
        <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
          <AlertDialogTrigger asChild>
            <Button variant="destructive" disabled={loading}>
              {loading ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              {dryRun ? "Simulate Cleanup" : "Clean Up Logs"}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                {dryRun ? (
                  "This will simulate cleaning up old logs based on retention policies. No logs will be deleted."
                ) : (
                  "This will permanently delete old logs based on retention policies. This action cannot be undone."
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleCleanup}>
                {dryRun ? "Simulate" : "Delete"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </CardFooter>
    </Card>
  )
}
