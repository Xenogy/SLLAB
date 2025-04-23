"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Download, Upload, RefreshCw } from "lucide-react"
import { DataTable } from "@/components/data-table"
import { columns, type Account } from "./columns"
import { useToast } from "@/components/ui/use-toast"
import { ImportAccountsModal } from "@/components/import-accounts-modal"
import { accountsAPI } from "@/lib/api"

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const { toast } = useToast()

  // Mock data for fallback when API fails
  const getMockAccounts = (): Account[] => [
    {
      acc_id: "1",
      acc_username: "steamuser1",
      acc_email_address: "user1@example.com",
      prime: true,
      lock: false,
      perm_lock: false,
      status: "active",
      type: "prime",
      lastLogin: new Date(Date.now() - 86400000).toISOString(),
      createdAt: new Date(Date.now() - 2592000000).toISOString(),
    },
    {
      acc_id: "2",
      acc_username: "steamuser2",
      acc_email_address: "user2@example.com",
      prime: false,
      lock: true,
      perm_lock: false,
      status: "inactive",
      type: "trade",
      lastLogin: new Date(Date.now() - 172800000).toISOString(),
      createdAt: new Date(Date.now() - 5184000000).toISOString(),
    },
    {
      acc_id: "3",
      acc_username: "steamuser3",
      acc_email_address: "user3@example.com",
      prime: false,
      lock: false,
      perm_lock: false,
      status: "active",
      type: "marketplace",
      lastLogin: new Date(Date.now() - 259200000).toISOString(),
      createdAt: new Date(Date.now() - 7776000000).toISOString(),
    },
    {
      acc_id: "4",
      acc_username: "steamuser4",
      acc_email_address: "user4@example.com",
      prime: true,
      lock: false,
      perm_lock: true,
      status: "banned",
      type: "prime",
      lastLogin: new Date(Date.now() - 345600000).toISOString(),
      createdAt: new Date(Date.now() - 10368000000).toISOString(),
    },
    {
      acc_id: "5",
      acc_username: "steamuser5",
      acc_email_address: "user5@example.com",
      prime: false,
      lock: false,
      perm_lock: false,
      status: "active",
      type: "trade",
      lastLogin: new Date(Date.now() - 432000000).toISOString(),
      createdAt: new Date(Date.now() - 12960000000).toISOString(),
    },
  ];

  // Fetch accounts from the API
  const fetchAccounts = async () => {
    setLoading(true)
    try {
      // Call the API to get accounts
      const apiAccounts = await accountsAPI.getAccountsPost()

      // Map the API response to the Account type
      const formattedAccounts: Account[] = apiAccounts.accounts.map(account => ({
        acc_id: account.acc_id || '',
        acc_username: account.acc_username || '',
        acc_email_address: account.acc_email_address || '',
        prime: account.prime || false,
        lock: account.lock || false,
        perm_lock: account.perm_lock || false,
        status: (account.lock ? 'inactive' : 'active'),
        type: (account.prime ? 'prime' : undefined),
        lastLogin: undefined,
        createdAt: account.acc_created_at.toString() || undefined,
      }))

      setAccounts(formattedAccounts)
    } catch (error) {
      console.error("Failed to fetch accounts:", error)

      // Fall back to mock data
      const mockAccounts = getMockAccounts();
      setAccounts(mockAccounts)

      toast({
        title: "Using Demo Data",
        description: "Could not connect to the API server. Using demo data instead.",
        variant: "warning",
      })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAccounts()
  }, [])

  const handleRefresh = () => {
    fetchAccounts()
  }


  const handleImportSuccess = () => {
    fetchAccounts()
    toast({
      title: "Import successful",
      description: "Accounts have been imported successfully.",
    })
  }

  const handleExport = () => {
    // Create CSV content
    const headers = ["acc_id", "acc_username", "acc_email_address", "prime", "lock", "perm_lock"].join(",")

    const rows = accounts.map((account) =>
      [
        account.acc_id,
        account.acc_username,
        account.acc_email_address,
        account.prime,
        account.lock,
        account.perm_lock,
      ].join(","),
    )

    const csvContent = [headers, ...rows].join("\n")

    // Create a blob and download
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", `steam_accounts_${new Date().toISOString().split("T")[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const primeAccounts = accounts.filter((account) => account.prime || account.type === "prime")
  const tradeAccounts = accounts.filter((account) => account.type === "trade")
  const marketplaceAccounts = accounts.filter((account) => account.type === "marketplace")

  const activeAccounts = accounts.filter((account) => !account.lock && !account.perm_lock)
  const inactiveAccounts = accounts.filter((account) => account.lock && !account.perm_lock)
  const bannedAccounts = accounts.filter((account) => account.perm_lock)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Account Management</h1>
        <div className="flex items-center gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Add Account
          </Button>
          <Button variant="outline" onClick={() => setIsImportModalOpen(true)}>
            <Upload className="mr-2 h-4 w-4" />
            Import
          </Button>
          <Button variant="outline" onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
          <Button variant="ghost" size="icon" onClick={handleRefresh} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Accounts</TabsTrigger>
          <TabsTrigger value="prime">Prime</TabsTrigger>
          <TabsTrigger value="trade">Trade</TabsTrigger>
          <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
        </TabsList>
        <TabsContent value="all" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{accounts.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Active Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{activeAccounts.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Inactive Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{inactiveAccounts.length}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Banned Accounts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{bannedAccounts.length}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Accounts</CardTitle>
              <CardDescription>Manage your Steam accounts</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={accounts}
                filterColumn="acc_username"
                filterPlaceholder="Filter by username..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="prime" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Prime Accounts</CardTitle>
              <CardDescription>Manage your Steam Prime accounts</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={primeAccounts}
                filterColumn="acc_username"
                filterPlaceholder="Filter by username..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trade" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Trade Accounts</CardTitle>
              <CardDescription>Manage your Steam Trade accounts</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={tradeAccounts}
                filterColumn="acc_username"
                filterPlaceholder="Filter by username..."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="marketplace" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Marketplace Accounts</CardTitle>
              <CardDescription>Manage your Steam Marketplace accounts</CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={columns}
                data={marketplaceAccounts}
                filterColumn="acc_username"
                filterPlaceholder="Filter by username..."
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <ImportAccountsModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onSuccess={handleImportSuccess}
      />
    </div>
  )
}
