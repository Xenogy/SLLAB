"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Plus, Search, RefreshCw, Copy } from "lucide-react"
import { hardwareAPI, type HardwareResponse } from "@/lib/api"
import { useToast } from "@/components/ui/use-toast"

export default function HardwareProfilePage() {
  const [searchType, setSearchType] = useState<string>("mac_address")
  const [searchValue, setSearchValue] = useState<string>("")
  const [searchResults, setSearchResults] = useState<HardwareResponse[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const { toast } = useToast()

  const handleSearch = async () => {
    if (!searchValue.trim()) {
      toast({
        title: "Error",
        description: "Please enter a search value",
        variant: "destructive",
      })
      return
    }

    setLoading(true)
    try {
      let results: HardwareResponse[] = []

      if (searchType === "mac_address") {
        results = await hardwareAPI.searchByMac(searchValue)
      } else if (searchType === "smbios_uuid") {
        results = await hardwareAPI.searchByUuid(searchValue)
      } else {
        results = await hardwareAPI.search(searchType, searchValue)
      }

      setSearchResults(results)

      if (results.length === 0) {
        toast({
          title: "No results",
          description: "No hardware profiles found matching your search criteria",
        })
      }
    } catch (error) {
      console.error("Search failed:", error)
      toast({
        title: "Search failed",
        description: "An error occurred while searching for hardware profiles",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copied",
      description: "Value copied to clipboard",
    })
  }

  // Mock data for demonstration
  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      setSearchResults([
        {
          id: 1,
          acc_id: "steamuser1",
          bios_vendor: "American Megatrends Inc.",
          bios_version: "2.17.1246",
          disk_serial: "S3SSNX0K912345",
          disk_model: "Samsung SSD 970 EVO 1TB",
          smbios_uuid: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
          mb_manufacturer: "ASUSTeK COMPUTER INC.",
          mb_product: "ROG STRIX Z390-E GAMING",
          mb_version: "Rev 1.xx",
          mb_serial: "123456789012",
          mac_address: "00:11:22:33:44:55",
          vmid: 1,
          pcname: "DESKTOP-ABC123",
          machine_guid: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
          hwprofile_guid: "c3d4e5f6-a7b8-9012-cdef-123456789012",
        },
      ])
    }
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Hardware Profiles</h1>
        <div className="flex items-center gap-2">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Profile
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Search Hardware Profiles</CardTitle>
          <CardDescription>Find hardware profiles by various criteria</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-2 sm:flex-row">
              <div className="w-full sm:w-1/3">
                <Label htmlFor="searchType">Search By</Label>
                <select
                  id="searchType"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                >
                  <option value="mac_address">MAC Address</option>
                  <option value="smbios_uuid">SMBIOS UUID</option>
                  <option value="pcname">PC Name</option>
                  <option value="disk_serial">Disk Serial</option>
                  <option value="mb_serial">Motherboard Serial</option>
                </select>
              </div>
              <div className="flex-1">
                <Label htmlFor="searchValue">Search Value</Label>
                <div className="flex gap-2">
                  <Input
                    id="searchValue"
                    placeholder={`Enter ${searchType.replace("_", " ")}...`}
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                  />
                  <Button onClick={handleSearch} disabled={loading}>
                    {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                    <span className="ml-2 hidden sm:inline">Search</span>
                  </Button>
                </div>
              </div>
            </div>

            <div className="mt-4">
              <h3 className="text-lg font-medium mb-2">Search Results</h3>
              {searchResults.length > 0 ? (
                <div className="space-y-4">
                  {searchResults.map((result) => (
                    <Card key={result.id}>
                      <CardHeader>
                        <CardTitle className="text-base flex justify-between">
                          <span>Profile ID: {result.id}</span>
                          <span>Account: {result.acc_id}</span>
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <Tabs defaultValue="system" className="w-full">
                          <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="system">System</TabsTrigger>
                            <TabsTrigger value="motherboard">Motherboard</TabsTrigger>
                            <TabsTrigger value="storage">Storage</TabsTrigger>
                          </TabsList>
                          <TabsContent value="system" className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">PC Name</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.pcname || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.pcname || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">MAC Address</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.mac_address || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.mac_address || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">SMBIOS UUID</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.smbios_uuid || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.smbios_uuid || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Machine GUID</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.machine_guid || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.machine_guid || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">VM ID</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.vmid || "N/A"}</span>
                                </div>
                              </div>
                            </div>
                          </TabsContent>
                          <TabsContent value="motherboard" className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Manufacturer</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.mb_manufacturer || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.mb_manufacturer || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Product</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.mb_product || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.mb_product || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Version</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.mb_version || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.mb_version || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Serial</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.mb_serial || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.mb_serial || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">BIOS Vendor</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.bios_vendor || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.bios_vendor || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">BIOS Version</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.bios_version || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.bios_version || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </TabsContent>
                          <TabsContent value="storage" className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Disk Model</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.disk_model || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.disk_model || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                              <div className="flex flex-col">
                                <Label className="text-muted-foreground">Disk Serial</Label>
                                <div className="flex items-center">
                                  <span className="text-sm">{result.disk_serial || "N/A"}</span>
                                  <Button
                                    variant="ghost"
                                    size="icon"
                                    className="ml-2 h-6 w-6"
                                    onClick={() => copyToClipboard(result.disk_serial || "")}
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </TabsContent>
                        </Tabs>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  {loading ? "Searching..." : "No results found. Try a different search."}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
