"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Edit, Trash, Play, Pause, RefreshCw, Terminal } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export type VM = {
  id: string
  name: string
  status: "running" | "stopped" | "error"
  ip: string
  cpu: string
  memory: string
  uptime: string
}

export const columns: ColumnDef<VM>[] = [
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
        <Badge variant={status === "running" ? "default" : status === "stopped" ? "secondary" : "destructive"}>
          {status}
        </Badge>
      )
    },
  },
  {
    accessorKey: "ip",
    header: "IP Address",
  },
  {
    accessorKey: "cpu",
    header: "CPU Usage",
  },
  {
    accessorKey: "memory",
    header: "Memory",
  },
  {
    accessorKey: "uptime",
    header: "Uptime",
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const vm = row.original
      const isRunning = vm.status === "running"

      return (
        <div className="flex items-center justify-end gap-2">
          <Button variant="ghost" size="icon" className={isRunning ? "text-amber-500" : "text-emerald-500"}>
            {isRunning ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>

          <Button variant="ghost" size="icon">
            <RefreshCw className="h-4 w-4" />
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Actions</DropdownMenuLabel>
              <DropdownMenuItem>
                <Terminal className="mr-2 h-4 w-4" />
                Console
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
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
