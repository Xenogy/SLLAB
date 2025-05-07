"use client"

import { useState } from "react"
import { LogEntry } from "@/lib/logs-api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Copy } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface LogDetailDialogProps {
  log: LogEntry | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function LogDetailDialog({ log, open, onOpenChange }: LogDetailDialogProps) {
  const { toast } = useToast()

  // Helper function to get color for log level
  const getLevelColor = (level: string): string => {
    switch (level) {
      case 'DEBUG':
        return 'bg-gray-500 hover:bg-gray-600'
      case 'INFO':
        return 'bg-blue-500 hover:bg-blue-600'
      case 'WARNING':
        return 'bg-yellow-500 hover:bg-yellow-600'
      case 'ERROR':
        return 'bg-red-500 hover:bg-red-600'
      case 'CRITICAL':
        return 'bg-red-800 hover:bg-red-900'
      default:
        return 'bg-gray-500 hover:bg-gray-600'
    }
  }

  // Function to copy log details to clipboard
  const copyToClipboard = () => {
    if (!log) return

    const logText = `
Log ID: ${log.id}
Timestamp: ${new Date(log.timestamp).toLocaleString()}
Level: ${log.level}
Category: ${log.category || '-'}
Source: ${log.source || '-'}
Message: ${log.message}
Entity: ${log.entity_type ? `${log.entity_type}:${log.entity_id}` : '-'}
User ID: ${log.user_id || '-'}
Trace ID: ${log.trace_id || '-'}
Details: ${log.details ? JSON.stringify(log.details, null, 2) : '-'}
    `.trim()

    navigator.clipboard.writeText(logText).then(() => {
      toast({
        title: "Copied to clipboard",
        description: "Log details have been copied to clipboard",
      })
    }).catch(err => {
      console.error('Failed to copy: ', err)
      toast({
        title: "Failed to copy",
        description: "Could not copy log details to clipboard",
        variant: "destructive",
      })
    })
  }

  if (!log) return null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Log Details</span>
            <Button variant="outline" size="sm" onClick={copyToClipboard}>
              <Copy className="h-4 w-4 mr-2" />
              Copy
            </Button>
          </DialogTitle>
          <DialogDescription>
            Log entry from {new Date(log.timestamp).toLocaleString()}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Basic Information */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">ID</h3>
              <p>{log.id}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Level</h3>
              <Badge className={`${getLevelColor(log.level)} text-white mt-1`}>
                {log.level}
              </Badge>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Category</h3>
              <p>{log.category || '-'}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Source</h3>
              <p>{log.source || '-'}</p>
            </div>
          </div>

          {/* Message */}
          <div>
            <h3 className="text-sm font-medium text-muted-foreground">Message</h3>
            <div className="p-2 bg-muted rounded-md mt-1 whitespace-pre-wrap">
              {log.message}
            </div>
          </div>

          {/* Entity Information */}
          {(log.entity_type || log.entity_id) && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Entity</h3>
              <div className="grid grid-cols-2 gap-4 mt-1">
                <div>
                  <h4 className="text-xs text-muted-foreground">Type</h4>
                  <p>{log.entity_type || '-'}</p>
                </div>
                <div>
                  <h4 className="text-xs text-muted-foreground">ID</h4>
                  <p>{log.entity_id || '-'}</p>
                </div>
              </div>
            </div>
          )}

          {/* User Information */}
          {log.user_id && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">User ID</h3>
              <p>{log.user_id}</p>
            </div>
          )}

          {/* Trace Information */}
          {(log.trace_id || log.span_id || log.parent_span_id) && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Trace Information</h3>
              <div className="grid grid-cols-3 gap-4 mt-1">
                <div>
                  <h4 className="text-xs text-muted-foreground">Trace ID</h4>
                  <p className="text-xs overflow-hidden text-ellipsis">{log.trace_id || '-'}</p>
                </div>
                <div>
                  <h4 className="text-xs text-muted-foreground">Span ID</h4>
                  <p className="text-xs overflow-hidden text-ellipsis">{log.span_id || '-'}</p>
                </div>
                <div>
                  <h4 className="text-xs text-muted-foreground">Parent Span ID</h4>
                  <p className="text-xs overflow-hidden text-ellipsis">{log.parent_span_id || '-'}</p>
                </div>
              </div>
            </div>
          )}

          {/* Details */}
          {log.details && (
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Details</h3>
              <pre className="p-2 bg-muted rounded-md mt-1 overflow-x-auto text-xs">
                {JSON.stringify(log.details, null, 2)}
              </pre>
            </div>
          )}

          {/* Timestamps */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Timestamp</h3>
              <p>{new Date(log.timestamp).toLocaleString()}</p>
            </div>
            <div>
              <h3 className="text-sm font-medium text-muted-foreground">Created At</h3>
              <p>{new Date(log.created_at).toLocaleString()}</p>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
