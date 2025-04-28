"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Edit, Trash, RefreshCw, Key, Server, List } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

// Import the Node type from the page component
import { ProxmoxNodeTableData } from "./page"

// Define the column actions interface
export interface ColumnActions {
  onRefresh: (node: ProxmoxNodeTableData) => void;
  onEdit: (node: ProxmoxNodeTableData) => void;
  onRegenerateApiKey: (node: ProxmoxNodeTableData) => void;
  onManageWhitelist: (node: ProxmoxNodeTableData) => void;
  onDelete: (node: ProxmoxNodeTableData) => void;
}

// Create a function that returns the columns with actions
export const createColumns = (actions: ColumnActions): ColumnDef<ProxmoxNodeTableData>[] => [
  {
    accessorKey: "name",
    header: "Name",
  },
  {
    accessorKey: "hostname",
    header: "Hostname",
  },
  {
    accessorKey: "port",
    header: "Port",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string

      return (
        <Badge variant={status === "connected" ? "default" : status === "disconnected" ? "secondary" : "destructive"}>
          {status}
        </Badge>
      )
    },
  },
  {
    accessorKey: "lastSeen",
    header: "Last Seen",
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const node = row.original

      return (
        <div className="flex items-center justify-end gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => actions.onRefresh(node)}
          >
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
              <DropdownMenuItem onClick={() => actions.onEdit(node)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => actions.onRegenerateApiKey(node)}>
                <Key className="mr-2 h-4 w-4" />
                Regenerate API Key
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => actions.onManageWhitelist(node)}>
                <List className="mr-2 h-4 w-4" />
                Manage VMID Whitelist
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => actions.onDelete(node)}
              >
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
