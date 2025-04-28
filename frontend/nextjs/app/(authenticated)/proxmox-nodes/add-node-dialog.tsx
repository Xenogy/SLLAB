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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useToast } from "@/components/ui/use-toast"
import { proxmoxNodesAPI, ProxmoxNodeResponse } from "@/lib/api"

interface AddNodeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onNodeAdded: (node: ProxmoxNodeResponse) => void
}

export function AddNodeDialog({ open, onOpenChange, onNodeAdded }: AddNodeDialogProps) {
  const [name, setName] = useState("")
  const [hostname, setHostname] = useState("")
  const [port, setPort] = useState("8006")
  const [loading, setLoading] = useState(false)
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name || !hostname) {
      toast({
        title: "Error",
        description: "Please fill in all required fields",
        variant: "destructive",
      })
      return
    }

    setLoading(true)

    try {
      const node = await proxmoxNodesAPI.createNode({
        name,
        hostname,
        port: parseInt(port),
      })

      // Reset form
      setName("")
      setHostname("")
      setPort("8006")

      // Notify parent with the node data
      onNodeAdded(node)
    } catch (error) {
      console.error("Error adding node:", error)
      toast({
        title: "Error",
        description: "Failed to add Proxmox node",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add Proxmox Node</DialogTitle>
            <DialogDescription>
              Enter the details of your Proxmox host node.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name*
              </Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="col-span-3"
                placeholder="My Proxmox Node"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="hostname" className="text-right">
                Hostname*
              </Label>
              <Input
                id="hostname"
                value={hostname}
                onChange={(e) => setHostname(e.target.value)}
                className="col-span-3"
                placeholder="proxmox.example.com"
                required
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="port" className="text-right">
                Port
              </Label>
              <Input
                id="port"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                className="col-span-3"
                type="number"
                placeholder="8006"
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? "Adding..." : "Add Node"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
