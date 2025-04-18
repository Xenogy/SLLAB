"use client"

import type React from "react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Bot, Server, Activity, BarChart, RefreshCw, Home, Settings } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {}

export default function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname()

  return (
    <div className={cn("pb-12 w-64 border-r bg-background hidden md:block", className)}>
      <div className="space-y-4 py-4">
        <div className="px-4 py-2">
          <h2 className="mb-2 px-2 text-xl font-semibold tracking-tight">Steam Farm</h2>
          <div className="space-y-1">
            <Button
              variant={pathname === "/" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start"
              asChild
            >
              <Link href="/">
                <Home className="mr-2 h-4 w-4" />
                Dashboard
              </Link>
            </Button>
          </div>
        </div>
        <div className="px-4 py-2">
          <h2 className="mb-2 px-2 text-lg font-semibold tracking-tight">Automation</h2>
          <div className="space-y-1">
            <Button
              variant={pathname === "/automation/accounts" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start"
              asChild
            >
              <Link href="/automation/accounts">
                <Bot className="mr-2 h-4 w-4" />
                Accounts
              </Link>
            </Button>
            <Button
              variant={pathname === "/automation/accounts/prime" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/automation/accounts/prime">Prime</Link>
            </Button>
            <Button
              variant={pathname === "/automation/accounts/trade" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/automation/accounts/trade">Trade</Link>
            </Button>
            <Button
              variant={pathname === "/automation/accounts/marketplace" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/automation/accounts/marketplace">Marketplace</Link>
            </Button>
            <Button
              variant={pathname === "/automation/farmlabs" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start"
              asChild
            >
              <Link href="/automation/farmlabs">
                <Activity className="mr-2 h-4 w-4" />
                Farmlabs
              </Link>
            </Button>
            <Button
              variant={pathname === "/automation/farmlabs/upload" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/automation/farmlabs/upload">Upload</Link>
            </Button>
            <Button
              variant={pathname === "/automation/farmlabs/management" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/automation/farmlabs/management">Management</Link>
            </Button>
            <Button
              variant={pathname === "/automation/farmlabs/jobs" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/automation/farmlabs/jobs">Jobs</Link>
            </Button>
          </div>
        </div>
        <div className="px-4 py-2">
          <h2 className="mb-2 px-2 text-lg font-semibold tracking-tight">Virtual Machines</h2>
          <div className="space-y-1">
            <Button
              variant={pathname === "/vms" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start"
              asChild
            >
              <Link href="/vms">
                <Server className="mr-2 h-4 w-4" />
                VM Management
              </Link>
            </Button>
            <Button
              variant={pathname === "/vms/proxy" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/vms/proxy">Proxy Settings</Link>
            </Button>
            <Button
              variant={pathname === "/vms/statistics" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start"
              asChild
            >
              <Link href="/vms/statistics">
                <BarChart className="mr-2 h-4 w-4" />
                Statistics
              </Link>
            </Button>
            <Button
              variant={pathname === "/vms/statistics/hw-profiler" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/vms/statistics/hw-profiler">HW Profiler</Link>
            </Button>
            <Button
              variant={pathname === "/vms/statistics/errors" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/vms/statistics/errors">Errors</Link>
            </Button>
            <Button
              variant={pathname === "/vms/statistics/job-tracking" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start pl-8"
              asChild
            >
              <Link href="/vms/statistics/job-tracking">Job Tracking</Link>
            </Button>
            <Button
              variant={pathname === "/vms/restarts" ? "secondary" : "ghost"}
              size="sm"
              className="w-full justify-start"
              asChild
            >
              <Link href="/vms/restarts">
                <RefreshCw className="mr-2 h-4 w-4" />
                Dynamic Restarts
              </Link>
            </Button>
          </div>
        </div>
        <div className="px-4 py-2">
          <h2 className="mb-2 px-2 text-lg font-semibold tracking-tight">Settings</h2>
          <Button
            variant={pathname === "/settings" ? "secondary" : "ghost"}
            size="sm"
            className="w-full justify-start"
            asChild
          >
            <Link href="/settings">
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
