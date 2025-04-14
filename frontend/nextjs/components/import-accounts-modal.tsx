"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, FileText, AlertCircle, Check, X } from 'lucide-react'
import { useToast } from "@/components/ui/use-toast"
import { accountsAPI } from "@/lib/api"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

interface ImportAccountsModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

type AccountData = {
  id: string
  user: {
    username: string
    password: string
  }
  email?: {
    address: string
    password: string
  }
  vault: {
    address: string
    password: string
  }
  metadata: {
    createdAt: number
    sessionStart: number
    tags?: string[]
    guard: string
  }
  steamguard?: {
    deviceId: string
    shared_secret: string
    serial_number: string
    revocation_code: string
    uri: string
    server_time: string
    account_name: string
    token_gid: string
    identity_secret: string
    secret_1: string
    status: number
    confirm_type: number
  }
}

export function ImportAccountsModal({ isOpen, onClose, onSuccess }: ImportAccountsModalProps) {
  const [file, setFile] = useState<File | null>(null)
  const [importType, setImportType] = useState<"csv" | "json">("csv")
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [previewData, setPreviewData] = useState<any[] | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  const resetState = () => {
    setFile(null)
    setProgress(0)
    setError(null)
    setPreviewData(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  const handleClose = () => {
    resetState()
    onClose()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null)
    setPreviewData(null)
    
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0]
      
      // Check file type
      if (importType === "csv" && !selectedFile.name.endsWith(".csv")) {
        setError("Please select a CSV file")
        return
      }
      
      if (importType === "json" && !selectedFile.name.endsWith(".json")) {
        setError("Please select a JSON file")
        return
      }
      
      setFile(selectedFile)
      
      // Preview the file
      const reader = new FileReader()
      
      reader.onload = (event) => {
        try {
          if (importType === "json") {
            const jsonData = JSON.parse(event.target?.result as string)
            setPreviewData(Array.isArray(jsonData) ? jsonData.slice(0, 3) : [jsonData])
          } else {
            // CSV preview
            const csvData = event.target?.result as string
            const lines = csvData.split("\n")
            const headers = lines[0].split(",").map(h => h.trim())
            
            const previewRows = []
            for (let i = 1; i < Math.min(lines.length, 4); i++) {
              if (lines[i].trim()) {
                const values = lines[i].split(",").map(v => v.trim())
                const row: Record<string, string> = {}
                
                headers.forEach((header, index) => {
                  row[header] = values[index] || ""
                })
                
                previewRows.push(row)
              }
            }
            
            setPreviewData(previewRows)
          }
        } catch (err) {
          console.error("Error parsing file:", err)
          setError(`Error parsing file: ${err instanceof Error ? err.message : String(err)}`)
        }
      }
      
      reader.onerror = () => {
        setError("Error reading file")
      }
      
      if (importType === "json") {
        reader.readAsText(selectedFile)
      } else {
        reader.readAsText(selectedFile)
      }
    }
  }

  const parseCSV = (csvText: string): AccountData[] => {
    const lines = csvText.split("\n")
    const headers = lines[0].split(",").map(h => h.trim())
    const accounts: AccountData[] = []
    
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue
      
      const values = lines[i].split(",").map(v => v.trim())
      const row: Record<string, string> = {}
      
      headers.forEach((header, index) => {
        row[header] = values[index] || ""
      })
      
      // Map CSV fields to the expected API format
      const account: AccountData = {
        id: row.acc_id || `import-${Date.now()}-${i}`,
        user: {
          username: row.acc_username || "",
          password: row.acc_password || "",
        },
        vault: {
          address: row.acc_vault_address || "",
          password: row.acc_vault_password || "",
        },
        metadata: {
          createdAt: parseInt(row.acc_created_at) || Date.now(),
          sessionStart: parseInt(row.acc_session_start) || Date.now(),
          guard: "email", // Default value
        }
      }
      
      // Add email if available
      if (row.acc_email_address) {
        account.email = {
          address: row.acc_email_address,
          password: row.acc_email_password || "",
        }
      }
      
      // Add steamguard if available
      if (row.acc_steamguard_account_name) {
        account.steamguard = {
          deviceId: row.acc_device_id || "",
          shared_secret: row.acc_shared_secret || "",
          serial_number: row.acc_serial_number || "",
          revocation_code: row.acc_revocation_code || "",
          uri: row.acc_uri || "",
          server_time: row.acc_server_time || "0",
          account_name: row.acc_steamguard_account_name,
          token_gid: row.acc_token_gid || "",
          identity_secret: row.acc_identity_secret || "",
          secret_1: row.acc_secret_1 || "",
          status: parseInt(row.acc_status) || 0,
          confirm_type: parseInt(row.acc_confirm_type) || 0,
        }
      }
      
      accounts.push(account)
    }
    
    return accounts
  }

  const handleImport = async () => {
    if (!file) {
      setError("Please select a file to import")
      return
    }
    
    setIsLoading(true)
    setProgress(10)
    setError(null)
    
    try {
      const reader = new FileReader()
      
      reader.onload = async (event) => {
        try {
          let accounts: AccountData[] = []
          
          if (importType === "json") {
            const jsonData = JSON.parse(event.target?.result as string)
            accounts = Array.isArray(jsonData) ? jsonData : [jsonData]
          } else {
            // Parse CSV
            accounts = parseCSV(event.target?.result as string)
          }
          
          setProgress(50)
          
          if (accounts.length === 0) {
            throw new Error("No valid accounts found in the file")
          }
          
          // Send to API
          const response = await accountsAPI.createAccounts(accounts)
          
          setProgress(100)
          
          toast({
            title: "Import successful",
            description: `Successfully imported ${accounts.length} accounts`,
          })
          
          // Refresh the accounts list
          onSuccess()
          
          // Close the modal
          setTimeout(() => {
            handleClose()
          }, 1000)
        } catch (err) {
          console.error("Error importing accounts:", err)
          setError(`Error importing accounts: ${err instanceof Error ? err.message : String(err)}`)
          setProgress(0)
        } finally {
          setIsLoading(false)
        }
      }
      
      reader.onerror = () => {
        setError("Error reading file")
        setIsLoading(false)
        setProgress(0)
      }
      
      reader.readAsText(file)
    } catch (err) {
      console.error("Error importing accounts:", err)
      setError(`Error importing accounts: ${err instanceof Error ? err.message : String(err)}`)
      setIsLoading(false)
      setProgress(0)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] w-[95vw] p-0 overflow-hidden">
      <div className="p-4 sm:p-6 max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Import Accounts</DialogTitle>
          <DialogDescription>
            Import accounts from a CSV or JSON file. The file should contain the required account information.
          </DialogDescription>
        </DialogHeader>
        
        <Tabs defaultValue="csv" className="w-full" onValueChange={(value) => setImportType(value as "csv" | "json")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="csv">CSV File</TabsTrigger>
            <TabsTrigger value="json">JSON File</TabsTrigger>
          </TabsList>
          
          <TabsContent value="csv" className="space-y-4 pt-4 w-full">
            <div className="space-y-2 w-full">
              <Label htmlFor="csvFile">Upload CSV File</Label>
              <Input
                id="csvFile"
                type="file"
                accept=".csv"
                ref={fileInputRef}
                onChange={handleFileChange}
                disabled={isLoading}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                CSV file should have headers matching the required fields.
              </p>
            </div>
          </TabsContent>
          
          <TabsContent value="json" className="space-y-4 pt-4 w-full">
            <div className="space-y-2 w-full">
              <Label htmlFor="jsonFile">Upload JSON File</Label>
              <Input
                id="jsonFile"
                type="file"
                accept=".json"
                ref={fileInputRef}
                onChange={handleFileChange}
                disabled={isLoading}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                JSON file should contain an array of account objects or a single account object.
              </p>
            </div>
          </TabsContent>
        </Tabs>
        
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {file && !error && (
          <div className="space-y-2 w-full">
            <div className="flex items-center space-x-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span>
                {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </span>
            </div>
            
            {previewData && previewData.length > 0 && (
          <div className="space-y-2 w-full">
                <Label>Preview</Label>
                <div className="max-h-[200px] w-full overflow-y-auto rounded border p-2">
                    <div className="w-full overflow-x-auto">
                      <pre className="text-xs whitespace-pre-wrap break-all">
                        {JSON.stringify(previewData, null, 2)}
                      </pre>
                    </div>
                </div>
                <p className="text-xs text-muted-foreground">
                  {importType === "json" 
                    ? `Showing ${previewData.length} of ${Array.isArray(JSON.parse(JSON.stringify(previewData))) ? JSON.parse(JSON.stringify(previewData)).length : 1} accounts`
                    : `Showing ${previewData.length} of ${file ? "multiple" : 0} accounts`}
                </p>
              </div>
            )}
          </div>
        )}
        
        {isLoading && (
          <div className="space-y-2">
            <Label>Import Progress</Label>
            <Progress value={progress} className="h-2" />
            <p className="text-xs text-muted-foreground">
              {progress < 100 ? "Importing accounts..." : "Import complete!"}
            </p>
          </div>
        )}
        
        <DialogFooter className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleImport} disabled={!file || isLoading}>
            {isLoading ? (
              <>
                <Upload className="mr-2 h-4 w-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Check className="mr-2 h-4 w-4" />
                Import
              </>
            )}
          </Button>
        </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  )
}
