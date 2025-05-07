"use client"

import { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Info, AlertCircle, Bug, FileText } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { LogEntry, LogLevel } from "@/lib/logs-api"
import { formatDistanceToNow } from "date-fns"

// Define the props for the columns
export type LogColumnsProps = {
  onViewDetails: (log: LogEntry) => void
}

// Helper function to get color for log level
const getLevelColor = (level: LogLevel): string => {
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

// Helper function to get icon for log level
const getLevelIcon = (level: LogLevel) => {
  switch (level) {
    case 'DEBUG':
      return <Bug className="h-4 w-4" />
    case 'INFO':
      return <Info className="h-4 w-4" />
    case 'WARNING':
      return <AlertCircle className="h-4 w-4" />
    case 'ERROR':
      return <AlertCircle className="h-4 w-4" />
    case 'CRITICAL':
      return <AlertCircle className="h-4 w-4" />
    default:
      return <Info className="h-4 w-4" />
  }
}

// Create columns with actions
export const createColumns = ({ onViewDetails }: LogColumnsProps): ColumnDef<LogEntry>[] => [
  {
    accessorKey: "timestamp",
    header: "Time",
    cell: ({ row }) => {
      const timestamp = row.getValue("timestamp") as string
      const date = new Date(timestamp)
      return (
        <div className="flex flex-col">
          <span className="text-xs">{date.toLocaleTimeString()}</span>
          <span className="text-xs text-muted-foreground">{formatDistanceToNow(date, { addSuffix: true })}</span>
        </div>
      )
    },
  },
  {
    accessorKey: "level",
    header: "Level",
    cell: ({ row }) => {
      const level = row.getValue("level") as LogLevel
      return (
        <Badge className={`${getLevelColor(level)} text-white`}>
          <span className="flex items-center">
            {getLevelIcon(level)}
            <span className="ml-1">{level}</span>
          </span>
        </Badge>
      )
    },
  },
  {
    accessorKey: "category",
    header: "Category",
    cell: ({ row }) => {
      const category = row.getValue("category") as string | null
      return category || <span className="text-muted-foreground text-xs">-</span>
    },
  },
  {
    accessorKey: "source",
    header: "Source",
    cell: ({ row }) => {
      const source = row.getValue("source") as string | null
      return source || <span className="text-muted-foreground text-xs">-</span>
    },
  },
  {
    accessorKey: "message",
    header: "Message",
    cell: ({ row }) => {
      const message = row.getValue("message") as string
      // Truncate message if too long
      const truncatedMessage = message.length > 100 ? `${message.substring(0, 100)}...` : message
      return <span className="whitespace-normal break-words">{truncatedMessage}</span>
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const log = row.original
      
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
            <DropdownMenuItem onClick={() => onViewDetails(log)}>
              <FileText className="mr-2 h-4 w-4" />
              View Details
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
]
