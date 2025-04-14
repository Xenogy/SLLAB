"use client"

import type { ColumnDef } from "@tanstack/react-table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { MoreHorizontal, Edit, Trash, Lock, Unlock, Shield } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { formatDistanceToNow } from "date-fns"

export type Account = {
  acc_id: string
  acc_username: string
  acc_email_address: string
  prime: boolean
  lock: boolean
  perm_lock: boolean
  status?: "active" | "inactive" | "banned"
  type?: "prime" | "trade" | "marketplace"
  lastLogin?: string
  createdAt?: string
}

export const columns: ColumnDef<Account>[] = [
  {
    accessorKey: "acc_username",
    header: "Username",
  },
  {
    accessorKey: "acc_email_address",
    header: "Email",
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = (row.getValue("status") as string) || (row.original.lock ? "inactive" : "active")

      return (
        <Badge variant={status === "active" ? "default" : status === "inactive" ? "secondary" : "destructive"}>
          {status}
        </Badge>
      )
    },
  },
  {
    accessorKey: "prime",
    header: "Prime",
    cell: ({ row }) => {
      const isPrime = row.getValue("prime") as boolean

      return (
        <Badge variant={isPrime ? "default" : "outline"} className={isPrime ? "bg-green-500 hover:bg-green-600" : ""}>
          {isPrime ? "Prime" : "Standard"}
        </Badge>
      )
    },
  },
  {
    accessorKey: "type",
    header: "Type",
    cell: ({ row }) => {
      const type = (row.getValue("type") as string) || (row.original.prime ? "prime" : "standard")
      return <div>{type}</div>
    },
  },
  {
    accessorKey: "lastLogin",
    header: "Last Login",
    cell: ({ row }) => {
      const date = row.getValue("lastLogin") as string
      if (!date) return <div className="text-muted-foreground">Unknown</div>
      return <div>{formatDistanceToNow(new Date(date), { addSuffix: true })}</div>
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const account = row.original
      const isLocked = account.lock
      const isPermanentlyLocked = account.perm_lock

      return (
        <div className="flex items-center justify-end gap-2">
          {!isPermanentlyLocked && (
            <Button variant="ghost" size="icon" className={isLocked ? "text-emerald-500" : "text-amber-500"}>
              {isLocked ? <Unlock className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
            </Button>
          )}

          {isPermanentlyLocked && (
            <Button variant="ghost" size="icon" className="text-red-500" disabled>
              <Shield className="h-4 w-4" />
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
              <DropdownMenuItem>
                {account.prime ? (
                  <>
                    <Shield className="mr-2 h-4 w-4" />
                    Remove Prime
                  </>
                ) : (
                  <>
                    <Shield className="mr-2 h-4 w-4" />
                    Set Prime
                  </>
                )}
              </DropdownMenuItem>
              <DropdownMenuItem>
                {isLocked ? (
                  <>
                    <Unlock className="mr-2 h-4 w-4" />
                    Unlock Account
                  </>
                ) : (
                  <>
                    <Lock className="mr-2 h-4 w-4" />
                    Lock Account
                  </>
                )}
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
