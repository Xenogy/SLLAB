"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Upload, FileText, X, Check } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

export default function UploadScriptPage() {
  const [files, setFiles] = useState<File[]>([])
  const [scriptName, setScriptName] = useState("")
  const [scriptDescription, setScriptDescription] = useState("")
  const [uploading, setUploading] = useState(false)
  const { toast } = useToast()

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...newFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleUpload = async () => {
    if (files.length === 0) {
      toast({
        title: "Error",
        description: "Please select at least one file to upload",
        variant: "destructive",
      })
      return
    }

    if (!scriptName.trim()) {
      toast({
        title: "Error",
        description: "Please enter a script name",
        variant: "destructive",
      })
      return
    }

    setUploading(true)

    try {
      const formData = new FormData()
      formData.append("name", scriptName)
      formData.append("description", scriptDescription)

      files.forEach((file, index) => {
        formData.append(`file_${index}`, file)
      })

      // In a real implementation, you would call your API
      // await farmlabsAPI.uploadScript(formData)

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      toast({
        title: "Success",
        description: "Script uploaded successfully",
      })

      // Reset form
      setFiles([])
      setScriptName("")
      setScriptDescription("")
    } catch (error) {
      console.error("Upload failed:", error)
      toast({
        title: "Upload failed",
        description: "An error occurred while uploading the script",
        variant: "destructive",
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Upload Script</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Upload Automation Script</CardTitle>
          <CardDescription>Upload scripts for Steam account automation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="scriptName">Script Name</Label>
            <Input
              id="scriptName"
              placeholder="Enter script name"
              value={scriptName}
              onChange={(e) => setScriptName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="scriptDescription">Description</Label>
            <Textarea
              id="scriptDescription"
              placeholder="Enter script description"
              value={scriptDescription}
              onChange={(e) => setScriptDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Script Files</Label>
            <div className="border border-dashed rounded-lg p-8 text-center">
              <Input id="fileUpload" type="file" multiple className="hidden" onChange={handleFileChange} />
              <Label htmlFor="fileUpload" className="cursor-pointer flex flex-col items-center justify-center">
                <Upload className="h-10 w-10 text-muted-foreground mb-2" />
                <p className="text-sm font-medium">Click to upload or drag and drop</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Support for Python, JavaScript, and other script files
                </p>
              </Label>
            </div>
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              <Label>Selected Files</Label>
              <div className="space-y-2">
                {files.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-2 border rounded-md bg-muted/40">
                    <div className="flex items-center">
                      <FileText className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="text-sm">{file.name}</span>
                      <span className="text-xs text-muted-foreground ml-2">({(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-muted-foreground hover:text-destructive"
                      onClick={() => removeFile(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button onClick={handleUpload} disabled={uploading}>
            {uploading ? (
              <>
                <Upload className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Check className="mr-2 h-4 w-4" />
                Upload Script
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
