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
import { Copy, Check } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"

interface ApiKeyDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  nodeId: string
  nodeName: string
  apiKey: string
  isRegenerating?: boolean
}

export function ApiKeyDialog({ 
  open, 
  onOpenChange, 
  nodeId, 
  nodeName, 
  apiKey,
  isRegenerating = false
}: ApiKeyDialogProps) {
  const [copied, setCopied] = useState(false)
  const { toast } = useToast()

  const handleCopy = () => {
    navigator.clipboard.writeText(apiKey)
    setCopied(true)
    
    toast({
      title: "Copied to clipboard",
      description: "API key has been copied to clipboard",
    })
    
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {isRegenerating ? "API Key Regenerated" : "Node Added Successfully"}
          </DialogTitle>
          <DialogDescription>
            {isRegenerating 
              ? `Your API key for ${nodeName} has been regenerated. Please update the configuration on your Proxmox host.`
              : `Your node ${nodeName} has been added successfully. Use the following information to configure your Proxmox host agent.`
            }
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="node-id" className="text-right">
              Node ID
            </Label>
            <Input
              id="node-id"
              value={nodeId}
              readOnly
              className="col-span-3"
            />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="api-key" className="text-right">
              API Key
            </Label>
            <div className="col-span-3 flex gap-2">
              <Input
                id="api-key"
                value={apiKey}
                readOnly
                className="font-mono"
              />
              <Button 
                variant="outline" 
                size="icon"
                onClick={handleCopy}
              >
                {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              </Button>
            </div>
          </div>
          <div className="col-span-4 mt-2">
            <p className="text-sm text-muted-foreground">
              Configure your Proxmox host agent with these values in the .env file:
            </p>
            <pre className="mt-2 rounded-md bg-muted p-4 overflow-x-auto text-sm">
              <code>
{`ACCOUNTDB_NODE_ID=${nodeId}
ACCOUNTDB_API_KEY=${apiKey}`}
              </code>
            </pre>
          </div>
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
