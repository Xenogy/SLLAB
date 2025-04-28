"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/lib/auth-provider"
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
import { useToast } from "@/components/ui/use-toast"
import { proxmoxNodesAPI } from "@/lib/api"
import { ProxmoxNodeTableData } from "./page"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

interface WhitelistDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  node: ProxmoxNodeTableData
  onWhitelistUpdated: () => void
}

export function WhitelistDialog({ open, onOpenChange, node, onWhitelistUpdated }: WhitelistDialogProps) {
  const [vmidInput, setVmidInput] = useState("")
  const [vmids, setVmids] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(false)
  const { toast } = useToast()
  const { token } = useAuth()

  // Fetch existing whitelist when dialog opens
  useEffect(() => {
    if (open && node) {
      fetchWhitelist()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, node, token])

  // Function to fetch the existing whitelist
  const fetchWhitelist = async () => {
    setInitialLoading(true)
    try {
      // Use the token from auth context if available
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      // First try to fetch directly from the backend API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://cs2.drandex.org'
      const response = await fetch(`${apiUrl}/proxmox-nodes/whitelist/${node.id}`, {
        headers,
      })

      if (!response.ok) {
        // If direct API call fails, try through our API route
        console.log('Direct API call failed, trying through API route')
        const routeResponse = await fetch(`/api/proxmox-nodes/whitelist/${node.id}`)

        if (!routeResponse.ok) {
          // Check if it's an authentication error
          if (routeResponse.status === 401) {
            const errorData = await routeResponse.json()
            toast({
              title: 'Authentication Error',
              description: 'Please log in again to continue',
              variant: 'destructive',
            })

            // Redirect to login page
            window.location.href = '/auth/login'
            return
          }

          throw new Error('Failed to fetch whitelist')
        }

        const data = await routeResponse.json()
        setVmids(data.vmids || [])
      } else {
        const data = await response.json()
        setVmids(data.vmids || [])
      }
    } catch (error) {
      console.error('Error fetching whitelist:', error)
      toast({
        title: 'Error',
        description: 'Failed to load existing whitelist',
        variant: 'destructive',
      })
    } finally {
      setInitialLoading(false)
    }
  }

  const handleAddVmid = () => {
    const vmid = parseInt(vmidInput.trim())
    if (isNaN(vmid) || vmid <= 0) {
      toast({
        title: "Error",
        description: "Please enter a valid VMID (positive number)",
        variant: "destructive",
      })
      return
    }

    if (vmids.includes(vmid)) {
      toast({
        title: "Error",
        description: "This VMID is already in the whitelist",
        variant: "destructive",
      })
      return
    }

    setVmids([...vmids, vmid])
    setVmidInput("")
  }

  const handleRemoveVmid = (vmid: number) => {
    setVmids(vmids.filter(id => id !== vmid))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (vmids.length === 0) {
      toast({
        title: "Error",
        description: "Please add at least one VMID to the whitelist",
        variant: "destructive",
      })
      return
    }

    setLoading(true)

    try {
      const result = await proxmoxNodesAPI.setVMIDWhitelist({
        node_id: parseInt(node.id),
        vmids: vmids,
      })

      toast({
        title: "Success",
        description: `VMID whitelist updated successfully with ${vmids.length} VMIDs`,
      })

      // Notify parent
      onWhitelistUpdated()
    } catch (error) {
      console.error("Error updating VMID whitelist:", error)
      toast({
        title: "Error",
        description: "Failed to update VMID whitelist",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  // Handle dialog close
  const handleDialogChange = (newOpen: boolean) => {
    if (!newOpen) {
      // Clear the whitelist when dialog is closed
      setVmids([])
      setVmidInput("")
    }
    onOpenChange(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleDialogChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>VMID Whitelist for {node.name}</DialogTitle>
            <DialogDescription>
              Add VMIDs to whitelist for automatic synchronization.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="vmid" className="text-right">
                VMID
              </Label>
              <div className="col-span-3 flex gap-2">
                <Input
                  id="vmid"
                  value={vmidInput}
                  onChange={(e) => setVmidInput(e.target.value)}
                  placeholder="Enter VMID (e.g., 100)"
                  type="number"
                />
                <Button type="button" onClick={handleAddVmid}>
                  Add
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right pt-2">
                Whitelist
              </Label>
              <div className="col-span-3">
                {initialLoading ? (
                  <div className="text-sm text-muted-foreground">
                    Loading whitelist...
                  </div>
                ) : vmids.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    No VMIDs added yet. Add VMIDs to whitelist.
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {vmids.map(vmid => (
                      <Badge key={vmid} variant="secondary" className="flex items-center gap-1">
                        {vmid}
                        <button
                          type="button"
                          onClick={() => handleRemoveVmid(vmid)}
                          className="ml-1 rounded-full hover:bg-muted"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleDialogChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading || initialLoading}>
              {loading ? "Saving..." : "Save Whitelist"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
