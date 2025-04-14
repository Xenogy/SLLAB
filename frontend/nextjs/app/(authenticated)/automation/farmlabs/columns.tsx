"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Edit, Trash, Play, Pause, StopCircle } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Progress } from "@/components/ui/progress"
import { formatDistanceToNow } from "date-fns"

export type Job = {
  id: string
  name: string
  status: "running" | "completed" | "queued" | "failed" | "paused"
  progress: string
  startTime: string | null
  estimatedEnd: string | null
  assignedVMs: number
}

export const columns: ColumnDef<Job>[] = [
  {
    accessorKey: "name",
    header: "Name",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string

      return (
        <Badge
          variant={
            status === "running"
              ? "default"
              : status === "completed"
                ? "success"
                : status === "queued"
                  ? "secondary"
                  : status === "paused"
                    ? "outline"
                    : "destructive"
          }
        >
          {status}
        </Badge>
      )
    },
  },
  {
    accessorKey: "progress",
    header: "Progress",
    cell: ({ row }) => {
      const progress = Number.parseInt(row.getValue("progress") as string)

      return (
        <div className="w-full max-w-xs">
          <Progress value={progress} className="h-2" />
          <span className="text-xs text-muted-foreground mt-1">{progress}%</span>
        </div>
      )
    },
  },
  {
    accessorKey: "startTime",
    header: "Started",
    cell: ({ row }) => {
      const startTime = row.getValue("startTime") as string | null

      if (!startTime) return <div className="text-muted-foreground">Not started</div>

      const date = new Date(startTime)
      return <div>{formatDistanceToNow(date, { addSuffix: true })}</div>
    },
  },
  {
    accessorKey: "assignedVMs",
    header: "VMs",
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const job = row.original
      const isRunning = job.status === "running"
      const isPaused = job.status === "paused"

      return (
        <div className="flex items-center justify-end gap-2">
          {(isRunning || isPaused) && (
            <Button variant="ghost" size="icon" className={isRunning ? "text-amber-500" : "text-emerald-500"}>
              {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
          )}

          {(isRunning || isPaused) && (
            <Button variant="ghost" size="icon" className="text-red-500">
              <StopCircle className="h-4 w-4" />
            </Button>
          )}

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem>View Details</DropdownMenuItem>
              <DropdownMenuItem>Clone</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive">
                <Trash className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )
    },
  },
]
