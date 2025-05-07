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
import { Textarea } from "@/components/ui/textarea"
import { Slider } from "@/components/ui/slider"
import { Checkbox } from "@/components/ui/checkbox"

interface AdvancedOptionsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  options: {
    use_auto_balancing: boolean
    proxy_list_str: string
    logical_batch_size: number
    max_concurrent_batches: number
    max_workers_per_batch: number
    inter_request_submit_delay: number
    max_retries_per_url: number
    retry_delay_seconds: number
  }
  onOptionsChange: (options: any) => void
}

export function AdvancedOptionsDialog({
  open,
  onOpenChange,
  options,
  onOptionsChange,
}: AdvancedOptionsDialogProps) {
  const [localOptions, setLocalOptions] = useState({ ...options })

  const handleSave = () => {
    onOptionsChange(localOptions)
    onOpenChange(false)
  }

  const handleReset = () => {
    setLocalOptions({
      use_auto_balancing: true,
      proxy_list_str: "",
      logical_batch_size: 20,
      max_concurrent_batches: 3,
      max_workers_per_batch: 3,
      inter_request_submit_delay: 0.1,
      max_retries_per_url: 2,
      retry_delay_seconds: 5.0
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Advanced Options</DialogTitle>
          <DialogDescription>
            Configure advanced options for the ban checker.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="flex items-center space-x-2 mb-4">
            <Checkbox
              id="auto-balancing"
              checked={localOptions.use_auto_balancing}
              onCheckedChange={(checked) =>
                setLocalOptions({ ...localOptions, use_auto_balancing: checked === true })
              }
            />
            <div className="grid gap-1.5 leading-none">
              <Label
                htmlFor="auto-balancing"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Use Automatic Parameter Balancing
              </Label>
              <p className="text-xs text-muted-foreground">
                Automatically optimize parameters based on the number of accounts being checked.
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="proxy-list">Proxy List</Label>
            <Textarea
              id="proxy-list"
              placeholder="Enter proxies, one per line (e.g., http://user:pass@host:port)"
              value={localOptions.proxy_list_str}
              onChange={(e) => setLocalOptions({ ...localOptions, proxy_list_str: e.target.value })}
              rows={5}
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              Optional. If not provided, the system will use default proxies.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="batch-size" className={localOptions.use_auto_balancing ? "text-muted-foreground" : ""}>Batch Size</Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="batch-size"
                  min={1}
                  max={50}
                  step={1}
                  value={[localOptions.logical_batch_size]}
                  onValueChange={(value) => setLocalOptions({ ...localOptions, logical_batch_size: value[0] })}
                  disabled={localOptions.use_auto_balancing}
                />
                <Input
                  type="number"
                  value={localOptions.logical_batch_size}
                  onChange={(e) => setLocalOptions({ ...localOptions, logical_batch_size: parseInt(e.target.value) || 1 })}
                  className="w-16"
                  disabled={localOptions.use_auto_balancing}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                URLs per processing unit/task.
                {localOptions.use_auto_balancing && " (Auto-balanced)"}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="concurrent-batches" className={localOptions.use_auto_balancing ? "text-muted-foreground" : ""}>Concurrent Batches</Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="concurrent-batches"
                  min={1}
                  max={10}
                  step={1}
                  value={[localOptions.max_concurrent_batches]}
                  onValueChange={(value) => setLocalOptions({ ...localOptions, max_concurrent_batches: value[0] })}
                  disabled={localOptions.use_auto_balancing}
                />
                <Input
                  type="number"
                  value={localOptions.max_concurrent_batches}
                  onChange={(e) => setLocalOptions({ ...localOptions, max_concurrent_batches: parseInt(e.target.value) || 1 })}
                  className="w-16"
                  disabled={localOptions.use_auto_balancing}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                How many batch tasks run in parallel.
                {localOptions.use_auto_balancing && " (Auto-balanced)"}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="workers-per-batch" className={localOptions.use_auto_balancing ? "text-muted-foreground" : ""}>Workers Per Batch</Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="workers-per-batch"
                  min={1}
                  max={10}
                  step={1}
                  value={[localOptions.max_workers_per_batch]}
                  onValueChange={(value) => setLocalOptions({ ...localOptions, max_workers_per_batch: value[0] })}
                  disabled={localOptions.use_auto_balancing}
                />
                <Input
                  type="number"
                  value={localOptions.max_workers_per_batch}
                  onChange={(e) => setLocalOptions({ ...localOptions, max_workers_per_batch: parseInt(e.target.value) || 1 })}
                  className="w-16"
                  disabled={localOptions.use_auto_balancing}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Threads for URLs within one batch.
                {localOptions.use_auto_balancing && " (Auto-balanced)"}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="submit-delay" className={localOptions.use_auto_balancing ? "text-muted-foreground" : ""}>Submit Delay (s)</Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="submit-delay"
                  min={0}
                  max={1}
                  step={0.1}
                  value={[localOptions.inter_request_submit_delay]}
                  onValueChange={(value) => setLocalOptions({ ...localOptions, inter_request_submit_delay: value[0] })}
                  disabled={localOptions.use_auto_balancing}
                />
                <Input
                  type="number"
                  value={localOptions.inter_request_submit_delay}
                  onChange={(e) => setLocalOptions({ ...localOptions, inter_request_submit_delay: parseFloat(e.target.value) || 0 })}
                  className="w-16"
                  step={0.1}
                  disabled={localOptions.use_auto_balancing}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Delay (s) submitting requests.
                {localOptions.use_auto_balancing && " (Auto-balanced)"}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-retries" className={localOptions.use_auto_balancing ? "text-muted-foreground" : ""}>Max Retries</Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="max-retries"
                  min={0}
                  max={5}
                  step={1}
                  value={[localOptions.max_retries_per_url]}
                  onValueChange={(value) => setLocalOptions({ ...localOptions, max_retries_per_url: value[0] })}
                  disabled={localOptions.use_auto_balancing}
                />
                <Input
                  type="number"
                  value={localOptions.max_retries_per_url}
                  onChange={(e) => setLocalOptions({ ...localOptions, max_retries_per_url: parseInt(e.target.value) || 0 })}
                  className="w-16"
                  disabled={localOptions.use_auto_balancing}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Retries per URL on failure.
                {localOptions.use_auto_balancing && " (Auto-balanced)"}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="retry-delay" className={localOptions.use_auto_balancing ? "text-muted-foreground" : ""}>Retry Delay (s)</Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="retry-delay"
                  min={0}
                  max={10}
                  step={0.5}
                  value={[localOptions.retry_delay_seconds]}
                  onValueChange={(value) => setLocalOptions({ ...localOptions, retry_delay_seconds: value[0] })}
                  disabled={localOptions.use_auto_balancing}
                />
                <Input
                  type="number"
                  value={localOptions.retry_delay_seconds}
                  onChange={(e) => setLocalOptions({ ...localOptions, retry_delay_seconds: parseFloat(e.target.value) || 0 })}
                  className="w-16"
                  step={0.5}
                  disabled={localOptions.use_auto_balancing}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Delay (s) between retries.
                {localOptions.use_auto_balancing && " (Auto-balanced)"}
              </p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleReset}>
            Reset to Defaults
          </Button>
          <Button onClick={handleSave}>Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
