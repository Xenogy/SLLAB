"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Eye, RefreshCw, AlertTriangle } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { BanCheckTask } from "@/lib/api"
import { formatDistanceToNow } from "date-fns"

interface ColumnActionsProps {
  onSelect?: (task: BanCheckTask) => void;
}

export function createColumns(actions: ColumnActionsProps = {}) {
  return [
    {
      accessorKey: "task_id",
      header: "Task ID",
      cell: ({ row }) => {
        const taskId = row.getValue("task_id") as string;
        return <span className="font-mono text-xs">{taskId.substring(0, 8)}...</span>;
      },
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const status = row.getValue("status") as string;
        return (
          <div>
            {status === "COMPLETED" && (
              <Badge variant="success">Completed</Badge>
            )}
            {status === "PROCESSING" && (
              <Badge variant="default" className="bg-blue-500">
                <RefreshCw className="mr-1 h-3 w-3 animate-spin" />
                Processing
              </Badge>
            )}
            {status === "PENDING" && (
              <Badge variant="secondary">Pending</Badge>
            )}
            {status === "FAILED" && (
              <Badge variant="destructive">
                <AlertTriangle className="mr-1 h-3 w-3" />
                Failed
              </Badge>
            )}
          </div>
        );
      },
    },
    {
      accessorKey: "progress",
      header: "Progress",
      cell: ({ row }) => {
        const progress = row.getValue("progress") as number;
        const status = row.getValue("status") as string;
        
        if (status === "COMPLETED") {
          return <span>100%</span>;
        }
        
        if (status === "FAILED") {
          return <span>Failed</span>;
        }
        
        return <span>{progress ? `${Math.round(progress)}%` : "0%"}</span>;
      },
    },
    {
      accessorKey: "created_at",
      header: "Created",
      cell: ({ row }) => {
        const createdAt = row.getValue("created_at") as string;
        if (!createdAt) return <span>N/A</span>;
        
        try {
          const date = new Date(createdAt);
          return <span title={date.toLocaleString()}>{formatDistanceToNow(date, { addSuffix: true })}</span>;
        } catch (e) {
          return <span>Invalid date</span>;
        }
      },
    },
    {
      id: "actions",
      cell: ({ row }) => {
        const task = row.original as BanCheckTask;
        
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-8 w-8 p-0">
                <span className="sr-only">Open menu</span>
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => actions.onSelect?.(task)}>
                <Eye className="mr-2 h-4 w-4" />
                View Results
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ] as ColumnDef<BanCheckTask>[];
}
