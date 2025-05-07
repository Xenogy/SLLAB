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
      console.log('Fetching whitelist for node:', node.id);

      // Use the API function from lib/api.ts to get the whitelist
      try {
        // First try to use the dedicated whitelist endpoint
        const result = await proxmoxNodesAPI.getNodeWhitelist(parseInt(node.id));
        console.log('Whitelist API response:', result);

        if (result && result.vmids && Array.isArray(result.vmids)) {
          console.log('Setting whitelist from dedicated endpoint:', result.vmids);
          setVmids(result.vmids);
          return; // Exit early if we got the whitelist successfully
        } else {
          console.log('Whitelist endpoint returned invalid data, falling back to node details');
        }
      } catch (whitelistError) {
        console.error('Error fetching from whitelist endpoint:', whitelistError);
        console.log('Falling back to node details endpoint');
      }

      // Fallback: Try to get the node details which should include the whitelist
      try {
        const nodeDetails = await proxmoxNodesAPI.getNode(parseInt(node.id));
        console.log('Node details API response:', nodeDetails);

        if (nodeDetails && nodeDetails.whitelist && Array.isArray(nodeDetails.whitelist)) {
          console.log('Setting whitelist from node details:', nodeDetails.whitelist);
          setVmids(nodeDetails.whitelist);
        } else {
          console.log('Node details do not contain a valid whitelist, setting empty array');
          setVmids([]);
        }
      } catch (nodeError) {
        console.error('Error fetching node details:', nodeError);
        toast({
          title: 'Warning',
          description: 'Could not load existing whitelist. Starting with empty list.',
          variant: 'default',
        });
        setVmids([]);
      }
    } catch (error) {
      console.error('Error in fetchWhitelist:', error);
      toast({
        title: 'Error',
        description: 'Failed to load existing whitelist',
        variant: 'destructive',
      });
      setVmids([]);
    } finally {
      setInitialLoading(false);
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
      await proxmoxNodesAPI.setVMIDWhitelist({
        node_id: parseInt(node.id),
        vmids: vmids,
      });

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
    if (newOpen) {
      // Clear the input field when dialog is opened
      setVmidInput("")
      // The whitelist will be fetched in the useEffect
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
