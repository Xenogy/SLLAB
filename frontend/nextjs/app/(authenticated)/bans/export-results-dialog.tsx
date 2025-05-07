"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Download } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

// Define the available columns for export
const AVAILABLE_COLUMNS = [
  { id: "steam_id", label: "Steam ID", default: true },
  { id: "status_summary", label: "Status", default: true },
  { id: "details", label: "Details", default: true },
  { id: "proxy_used", label: "Proxy Used", default: false },
  { id: "batch_id", label: "Batch ID", default: false },
]

export interface ExportResultsDialogProps {
  isOpen: boolean
  onClose: () => void
  results: any[] // The results to export
  taskId: string // The task ID for the filename
}

export function ExportResultsDialog({ isOpen, onClose, results, taskId }: ExportResultsDialogProps) {
  // State for selected columns
  const [selectedColumns, setSelectedColumns] = useState<Record<string, boolean>>(
    AVAILABLE_COLUMNS.reduce((acc, col) => ({ ...acc, [col.id]: col.default }), {})
  )
  
  // State for export format
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv")
  
  // Toast for notifications
  const { toast } = useToast()

  // Handle column selection
  const handleColumnToggle = (columnId: string) => {
    setSelectedColumns(prev => ({
      ...prev,
      [columnId]: !prev[columnId]
    }))
  }

  // Handle export
  const handleExport = () => {
    // Get selected column IDs
    const columnsToExport = Object.entries(selectedColumns)
      .filter(([_, isSelected]) => isSelected)
      .map(([columnId]) => columnId)
    
    if (columnsToExport.length === 0) {
      toast({
        title: "No columns selected",
        description: "Please select at least one column to export.",
        variant: "destructive",
      })
      return
    }
    
    try {
      if (exportFormat === "csv") {
        exportAsCSV(columnsToExport)
      } else {
        exportAsJSON(columnsToExport)
      }
      
      // Close the dialog
      onClose()
      
      // Show success toast
      toast({
        title: "Export successful",
        description: `Results exported as ${exportFormat.toUpperCase()}.`,
      })
    } catch (error) {
      console.error("Export error:", error)
      toast({
        title: "Export failed",
        description: "An error occurred while exporting the results.",
        variant: "destructive",
      })
    }
  }
  
  // Export as CSV
  const exportAsCSV = (columns: string[]) => {
    // Create CSV header
    const header = columns.join(",")
    
    // Create CSV rows
    const rows = results.map(result => 
      columns.map(column => {
        // Handle special characters in CSV (escape quotes, etc.)
        const value = result[column]?.toString() || ""
        return `"${value.replace(/"/g, '""')}"`
      }).join(",")
    )
    
    // Combine header and rows
    const csvContent = [header, ...rows].join("\n")
    
    // Create a blob and download
    downloadFile(csvContent, `ban_check_results_${taskId.substring(0, 8)}.csv`, "text/csv")
  }
  
  // Export as JSON
  const exportAsJSON = (columns: string[]) => {
    // Create filtered JSON objects with only selected columns
    const jsonData = results.map(result => {
      const filteredResult: Record<string, any> = {}
      columns.forEach(column => {
        filteredResult[column] = result[column]
      })
      return filteredResult
    })
    
    // Convert to JSON string
    const jsonContent = JSON.stringify(jsonData, null, 2)
    
    // Create a blob and download
    downloadFile(jsonContent, `ban_check_results_${taskId.substring(0, 8)}.json`, "application/json")
  }
  
  // Helper function to download a file
  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: `${mimeType};charset=utf-8;` })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.setAttribute("href", url)
    link.setAttribute("download", filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Results</DialogTitle>
          <DialogDescription>
            Select the columns you want to include in the export.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4 space-y-4">
          <div className="space-y-2">
            <Label className="text-base">Export Format</Label>
            <div className="flex space-x-4">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="format-csv"
                  name="export-format"
                  value="csv"
                  checked={exportFormat === "csv"}
                  onChange={() => setExportFormat("csv")}
                />
                <Label htmlFor="format-csv">CSV</Label>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="format-json"
                  name="export-format"
                  value="json"
                  checked={exportFormat === "json"}
                  onChange={() => setExportFormat("json")}
                />
                <Label htmlFor="format-json">JSON</Label>
              </div>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label className="text-base">Columns to Export</Label>
            <div className="grid grid-cols-2 gap-2">
              {AVAILABLE_COLUMNS.map(column => (
                <div key={column.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={`column-${column.id}`}
                    checked={selectedColumns[column.id]}
                    onCheckedChange={() => handleColumnToggle(column.id)}
                  />
                  <Label htmlFor={`column-${column.id}`}>{column.label}</Label>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleExport}>
            <Download className="mr-2 h-4 w-4" />
            Export
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
