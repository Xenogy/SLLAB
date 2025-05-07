"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Separator } from "@/components/ui/separator"
import { toast } from "@/components/ui/use-toast"
import { fetchAPI, settingsAPI, UserSettings as UserSettingsType, APIKey as APIKeyType, APIKeyWithFullKey } from "@/lib/api"
import { Loader2, Save, RefreshCw, Copy, Check, X, Key, Plus, Trash2 } from "lucide-react"
import { LogsCleanup } from "./logs-cleanup"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"

// Define the form schema for user settings
const userSettingsFormSchema = z.object({
  theme: z.enum(["light", "dark", "system"], {
    required_error: "Please select a theme.",
  }),
  language: z.enum(["en", "sv", "de", "fr"], {
    required_error: "Please select a language.",
  }),
  timezone: z.string({
    required_error: "Please select a timezone.",
  }),
  date_format: z.enum(["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD.MM.YYYY"], {
    required_error: "Please select a date format.",
  }),
  time_format: z.enum(["12h", "24h"], {
    required_error: "Please select a time format.",
  }),
  notifications_enabled: z.boolean().default(true),
  email_notifications: z.boolean().default(true),
  auto_refresh_interval: z.number().min(10).max(3600),
  items_per_page: z.number().min(5).max(100),
})

// Define the form schema for API key creation
const apiKeyFormSchema = z.object({
  key_name: z.string().min(3, {
    message: "Key name must be at least 3 characters.",
  }),
  key_type: z.enum(["user", "proxmox_node", "windows_vm", "farmlabs"]).default("user"),
  resource_id: z.number().optional().nullable(),
  expires_in_days: z.number().min(0).max(365).optional(),
  scopes: z.array(z.string()).default(["read"]),
})

// Define the type for form values
type UserSettingsFormValues = z.infer<typeof userSettingsFormSchema>

export default function SettingsPage({
  searchParams,
}: {
  searchParams?: { [key: string]: string | string[] | undefined };
}) {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<string>("user-settings")
  const [loading, setLoading] = useState(true)
  const [savingSettings, setSavingSettings] = useState(false)
  const [apiKeys, setApiKeys] = useState<APIKeyType[]>([])
  const [loadingApiKeys, setLoadingApiKeys] = useState(true)
  const [newApiKey, setNewApiKey] = useState<APIKeyWithFullKey | null>(null)
  const [createApiKeyDialogOpen, setCreateApiKeyDialogOpen] = useState(false)
  const [copiedKey, setCopiedKey] = useState(false)
  const [keyToRevoke, setKeyToRevoke] = useState<number | null>(null)
  const [revokingKey, setRevokingKey] = useState(false)
  const [proxmoxNodes, setProxmoxNodes] = useState<Array<{ id: number, name: string }>>([])
  const [windowsVMs, setWindowsVMs] = useState<Array<{ id: number, name: string }>>([])
  const [loadingResources, setLoadingResources] = useState(false)

  // Set active tab based on URL parameter
  useEffect(() => {
    if (searchParams?.tab) {
      const tab = Array.isArray(searchParams.tab)
        ? searchParams.tab[0]
        : searchParams.tab;

      if (tab === "api-keys" || tab === "logs") {
        setActiveTab(tab);
      }
    }
  }, [searchParams]);

  // Initialize the form with default values
  const form = useForm<UserSettingsFormValues>({
    resolver: zodResolver(userSettingsFormSchema),
    defaultValues: {
      theme: "light",
      language: "en",
      timezone: "UTC",
      date_format: "YYYY-MM-DD",
      time_format: "24h",
      notifications_enabled: true,
      email_notifications: true,
      auto_refresh_interval: 60,
      items_per_page: 10,
    },
  })

  // Initialize the API key form
  const apiKeyForm = useForm<z.infer<typeof apiKeyFormSchema>>({
    resolver: zodResolver(apiKeyFormSchema),
    defaultValues: {
      key_name: "",
      key_type: "user",
      resource_id: undefined,
      expires_in_days: 30,
      scopes: ["read"],
    },
  })

  // Fetch user settings on component mount
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true)
        const response = await settingsAPI.getUserSettings()

        if (response) {
          // Update form values with fetched settings
          form.reset({
            theme: response.theme,
            language: response.language,
            timezone: response.timezone,
            date_format: response.date_format,
            time_format: response.time_format,
            notifications_enabled: response.notifications_enabled,
            email_notifications: response.email_notifications,
            auto_refresh_interval: response.auto_refresh_interval,
            items_per_page: response.items_per_page,
          })
        }
      } catch (error) {
        console.error("Failed to fetch settings:", error)
        toast({
          title: "Error",
          description: "Failed to load settings. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoading(false)
      }
    }

    fetchSettings()
  }, [form])

  // Fetch API keys on component mount
  useEffect(() => {
    const fetchApiKeys = async () => {
      try {
        setLoadingApiKeys(true)
        const response = await settingsAPI.listAPIKeys()

        if (response && response.api_keys) {
          setApiKeys(response.api_keys)
        }
      } catch (error) {
        console.error("Failed to fetch API keys:", error)
        toast({
          title: "Error",
          description: "Failed to load API keys. Please try again.",
          variant: "destructive",
        })
      } finally {
        setLoadingApiKeys(false)
      }
    }

    fetchApiKeys()
  }, [])

  // Fetch resources when key type changes or dialog opens
  useEffect(() => {
    const keyType = apiKeyForm.watch("key_type")

    if (keyType === "user" || !createApiKeyDialogOpen) {
      return
    }

    const fetchResources = async () => {
      setLoadingResources(true)
      try {
        if (keyType === "proxmox_node") {
          const response = await fetchAPI("/proxmox-nodes", { params: { limit: 100 } })
          setProxmoxNodes(response.nodes.map((node: any) => ({ id: node.id, name: node.name })))
        } else if (keyType === "windows_vm") {
          const response = await fetchAPI("/vms", { params: { limit: 100 } })
          setWindowsVMs(response.vms.map((vm: any) => ({ id: vm.id, name: vm.name })))
        } else if (keyType === "farmlabs") {
          // No resources to fetch for FarmLabs
        }
      } catch (error) {
        console.error(`Error fetching ${keyType} resources:`, error)
        toast({
          title: "Error",
          description: `Failed to fetch ${keyType.replace('_', ' ')} resources.`,
          variant: "destructive",
        })
      } finally {
        setLoadingResources(false)
      }
    }

    fetchResources()
  }, [apiKeyForm.watch("key_type"), createApiKeyDialogOpen])

  // Handle form submission for user settings
  const onSubmit = async (data: UserSettingsFormValues) => {
    try {
      setSavingSettings(true)
      const response = await settingsAPI.updateUserSettings(data)

      if (response) {
        toast({
          title: "Settings updated",
          description: "Your settings have been updated successfully.",
        })
      }
    } catch (error) {
      console.error("Failed to update settings:", error)
      toast({
        title: "Error",
        description: "Failed to update settings. Please try again.",
        variant: "destructive",
      })
    } finally {
      setSavingSettings(false)
    }
  }

  // Handle API key creation
  const onCreateApiKey = async (data: z.infer<typeof apiKeyFormSchema>) => {
    try {
      let response;

      if (data.key_type === "user" || data.key_type === "farmlabs") {
        // Create a user API key or FarmLabs API key
        response = await settingsAPI.createAPIKey({
          key_name: data.key_name,
          key_type: data.key_type,
          expires_in_days: data.expires_in_days,
          scopes: data.scopes,
        });
      } else {
        // Create a resource API key
        response = await fetchAPI("/settings/resource-api-keys", {
          method: "POST",
          body: {
            resource_type: data.key_type,
            resource_id: data.resource_id,
          },
        });
      }

      if (response) {
        setNewApiKey(response)
        // Add the new key to the list (without the full key)
        const { api_key, ...keyWithoutFullKey } = response
        setApiKeys([keyWithoutFullKey, ...apiKeys])
        // Reset the form
        apiKeyForm.reset({
          key_name: "",
          key_type: "user",
          resource_id: undefined,
          expires_in_days: 30,
          scopes: ["read"],
        })
      }
    } catch (error) {
      console.error("Failed to create API key:", error)
      toast({
        title: "Error",
        description: "Failed to create API key. Please try again.",
        variant: "destructive",
      })
      setCreateApiKeyDialogOpen(false)
    }
  }

  // Handle API key revocation
  const onRevokeApiKey = async (keyId: number) => {
    try {
      setRevokingKey(true)
      const response = await settingsAPI.revokeAPIKey(keyId)

      if (response) {
        // Update the key in the list
        setApiKeys(apiKeys.map(key =>
          key.id === keyId ? { ...key, revoked: true } : key
        ))

        toast({
          title: "API key revoked",
          description: "The API key has been revoked successfully.",
        })
      }
    } catch (error) {
      console.error("Failed to revoke API key:", error)
      toast({
        title: "Error",
        description: "Failed to revoke API key. Please try again.",
        variant: "destructive",
      })
    } finally {
      setRevokingKey(false)
      setKeyToRevoke(null)
    }
  }

  // Handle copying API key to clipboard
  const copyApiKey = (key: string) => {
    navigator.clipboard.writeText(key)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
  }

  // Format date for display
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never"
    return new Date(dateString).toLocaleString()
  }

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Settings</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="user-settings">User Settings</TabsTrigger>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
          <TabsTrigger value="logs">Logs</TabsTrigger>
        </TabsList>

        {/* User Settings Tab */}
        <TabsContent value="user-settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>User Settings</CardTitle>
              <CardDescription>
                Manage your account settings and preferences.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex justify-center items-center h-40">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : (
                <Form {...form}>
                  <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* Theme */}
                      <FormField
                        control={form.control}
                        name="theme"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Theme</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select a theme" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="light">Light</SelectItem>
                                <SelectItem value="dark">Dark</SelectItem>
                                <SelectItem value="system">System</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              Select your preferred theme.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      {/* Language */}
                      <FormField
                        control={form.control}
                        name="language"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Language</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select a language" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="en">English</SelectItem>
                                <SelectItem value="sv">Swedish</SelectItem>
                                <SelectItem value="de">German</SelectItem>
                                <SelectItem value="fr">French</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              Select your preferred language.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      {/* Timezone */}
                      <FormField
                        control={form.control}
                        name="timezone"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Timezone</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select a timezone" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="UTC">UTC</SelectItem>
                                <SelectItem value="Europe/Stockholm">Europe/Stockholm</SelectItem>
                                <SelectItem value="Europe/London">Europe/London</SelectItem>
                                <SelectItem value="America/New_York">America/New_York</SelectItem>
                                <SelectItem value="America/Los_Angeles">America/Los_Angeles</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              Select your timezone.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      {/* Date Format */}
                      <FormField
                        control={form.control}
                        name="date_format"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Date Format</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select a date format" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="YYYY-MM-DD">YYYY-MM-DD</SelectItem>
                                <SelectItem value="MM/DD/YYYY">MM/DD/YYYY</SelectItem>
                                <SelectItem value="DD/MM/YYYY">DD/MM/YYYY</SelectItem>
                                <SelectItem value="DD.MM.YYYY">DD.MM.YYYY</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              Select your preferred date format.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      {/* Time Format */}
                      <FormField
                        control={form.control}
                        name="time_format"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Time Format</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select a time format" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="12h">12-hour (AM/PM)</SelectItem>
                                <SelectItem value="24h">24-hour</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormDescription>
                              Select your preferred time format.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      {/* Auto Refresh Interval */}
                      <FormField
                        control={form.control}
                        name="auto_refresh_interval"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Auto Refresh Interval (seconds)</FormLabel>
                            <FormControl>
                              <Input
                                type="number"
                                min={10}
                                max={3600}
                                {...field}
                                onChange={(e) => field.onChange(parseInt(e.target.value))}
                              />
                            </FormControl>
                            <FormDescription>
                              Set the interval for auto-refreshing data (10-3600 seconds).
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      {/* Items Per Page */}
                      <FormField
                        control={form.control}
                        name="items_per_page"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Items Per Page</FormLabel>
                            <FormControl>
                              <Input
                                type="number"
                                min={5}
                                max={100}
                                {...field}
                                onChange={(e) => field.onChange(parseInt(e.target.value))}
                              />
                            </FormControl>
                            <FormDescription>
                              Set the number of items to display per page (5-100).
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <Separator className="my-6" />

                    <div className="space-y-4">
                      <h3 className="text-lg font-medium">Notifications</h3>

                      {/* Notifications Enabled */}
                      <FormField
                        control={form.control}
                        name="notifications_enabled"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                            <div className="space-y-0.5">
                              <FormLabel className="text-base">
                                Enable Notifications
                              </FormLabel>
                              <FormDescription>
                                Receive notifications about important events.
                              </FormDescription>
                            </div>
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />

                      {/* Email Notifications */}
                      <FormField
                        control={form.control}
                        name="email_notifications"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                            <div className="space-y-0.5">
                              <FormLabel className="text-base">
                                Email Notifications
                              </FormLabel>
                              <FormDescription>
                                Receive email notifications about important events.
                              </FormDescription>
                            </div>
                            <FormControl>
                              <Switch
                                checked={field.value}
                                onCheckedChange={field.onChange}
                                disabled={!form.watch("notifications_enabled")}
                              />
                            </FormControl>
                          </FormItem>
                        )}
                      />
                    </div>

                    <div className="flex justify-end">
                      <Button type="submit" disabled={savingSettings}>
                        {savingSettings ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 h-4 w-4" />
                            Save Settings
                          </>
                        )}
                      </Button>
                    </div>
                  </form>
                </Form>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>API Keys</CardTitle>
              <CardDescription>
                Manage API keys for accessing the AccountDB API programmatically.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex justify-end mb-4">
                <Dialog open={createApiKeyDialogOpen} onOpenChange={setCreateApiKeyDialogOpen}>
                  <DialogTrigger asChild>
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Create API Key
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create API Key</DialogTitle>
                      <DialogDescription>
                        Create a new API key for programmatic access to the AccountDB API.
                      </DialogDescription>
                    </DialogHeader>

                    <Form {...apiKeyForm}>
                      <form onSubmit={apiKeyForm.handleSubmit(onCreateApiKey)} className="space-y-4">
                        <FormField
                          control={apiKeyForm.control}
                          name="key_name"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Key Name</FormLabel>
                              <FormControl>
                                <Input placeholder="My API Key" {...field} />
                              </FormControl>
                              <FormDescription>
                                A descriptive name for this API key.
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={apiKeyForm.control}
                          name="key_type"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Key Type</FormLabel>
                              <Select
                                onValueChange={(value) => {
                                  field.onChange(value);
                                  // Reset resource_id when key type changes
                                  apiKeyForm.setValue("resource_id", undefined);
                                }}
                                defaultValue={field.value}
                              >
                                <FormControl>
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select key type" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  <SelectItem value="user">User (General Access)</SelectItem>
                                  <SelectItem value="proxmox_node">Proxmox Node</SelectItem>
                                  <SelectItem value="windows_vm">Windows VM</SelectItem>
                                  <SelectItem value="farmlabs">FarmLabs Integration</SelectItem>
                                </SelectContent>
                              </Select>
                              <FormDescription>
                                Select the type of API key you want to create.
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        {apiKeyForm.watch("key_type") !== "user" && apiKeyForm.watch("key_type") !== "farmlabs" && (
                          <FormField
                            control={apiKeyForm.control}
                            name="resource_id"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel>
                                  {apiKeyForm.watch("key_type") === "proxmox_node"
                                    ? "Proxmox Node"
                                    : "Windows VM"}
                                </FormLabel>
                                <Select
                                  onValueChange={(value) => field.onChange(parseInt(value))}
                                  defaultValue={field.value?.toString()}
                                >
                                  <FormControl>
                                    <SelectTrigger>
                                      <SelectValue placeholder={`Select a ${apiKeyForm.watch("key_type") === "proxmox_node" ? "node" : "VM"}`} />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {apiKeyForm.watch("key_type") === "proxmox_node"
                                      ? proxmoxNodes.map(node => (
                                          <SelectItem key={node.id} value={node.id.toString()}>
                                            {node.name}
                                          </SelectItem>
                                        ))
                                      : windowsVMs.map(vm => (
                                          <SelectItem key={vm.id} value={vm.id.toString()}>
                                            {vm.name}
                                          </SelectItem>
                                        ))
                                    }
                                  </SelectContent>
                                </Select>
                                <FormDescription>
                                  Select the resource to associate with this API key.
                                </FormDescription>
                                <FormMessage />
                              </FormItem>
                            )}
                          />
                        )}

                        {apiKeyForm.watch("key_type") === "farmlabs" && (
                          <div className="rounded-md bg-blue-50 p-4 mb-4">
                            <div className="flex">
                              <div className="ml-3">
                                <h3 className="text-sm font-medium text-blue-800">FarmLabs Integration</h3>
                                <div className="mt-2 text-sm text-blue-700">
                                  <p>
                                    This API key will be used for FarmLabs webhook integration.
                                    It will allow the FarmLabs server to send job completion notifications to AccountDB.
                                  </p>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}

                        <FormField
                          control={apiKeyForm.control}
                          name="expires_in_days"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Expiration (days)</FormLabel>
                              <FormControl>
                                <Input
                                  type="number"
                                  min={0}
                                  max={365}
                                  placeholder="30"
                                  {...field}
                                  onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : undefined)}
                                />
                              </FormControl>
                              <FormDescription>
                                Number of days until the key expires. Use 0 for no expiration.
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={apiKeyForm.control}
                          name="scopes"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel>Permissions</FormLabel>
                              <div className="space-y-2">
                                <div className="flex flex-wrap gap-2">
                                  {["read", "write", "admin"].map((scope) => (
                                    <div key={scope} className="flex items-center space-x-2">
                                      <Checkbox
                                        id={`scope-${scope}`}
                                        checked={field.value?.includes(scope)}
                                        onCheckedChange={(checked) => {
                                          const currentScopes = field.value || [];
                                          if (checked) {
                                            field.onChange([...currentScopes, scope]);
                                          } else {
                                            field.onChange(currentScopes.filter(s => s !== scope));
                                          }
                                        }}
                                      />
                                      <label
                                        htmlFor={`scope-${scope}`}
                                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                                      >
                                        {scope.charAt(0).toUpperCase() + scope.slice(1)}
                                      </label>
                                    </div>
                                  ))}
                                </div>
                              </div>
                              <FormDescription>
                                Select the permissions for this API key.
                              </FormDescription>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <DialogFooter>
                          <Button type="submit">Create API Key</Button>
                        </DialogFooter>
                      </form>
                    </Form>
                  </DialogContent>
                </Dialog>
              </div>

              {/* Display newly created API key */}
              {newApiKey && (
                <Card className="mb-6 border-2 border-primary">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg flex items-center">
                      <Key className="mr-2 h-5 w-5" />
                      New API Key Created
                    </CardTitle>
                    <CardDescription>
                      This key will only be shown once. Please copy it now.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center space-x-2 mb-4">
                      <Input
                        value={newApiKey.api_key}
                        readOnly
                        className="font-mono"
                      />
                      <Button
                        variant="outline"
                        size="icon"
                        onClick={() => copyApiKey(newApiKey.api_key)}
                      >
                        {copiedKey ? (
                          <Check className="h-4 w-4" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      <p><strong>Name:</strong> {newApiKey.key_name}</p>
                      <p><strong>Created:</strong> {formatDate(newApiKey.created_at)}</p>
                      <p><strong>Expires:</strong> {newApiKey.expires_at ? formatDate(newApiKey.expires_at) : "Never"}</p>
                    </div>
                  </CardContent>
                  <CardFooter>
                    <Button
                      variant="outline"
                      onClick={() => setNewApiKey(null)}
                      className="w-full"
                    >
                      I've Copied My Key
                    </Button>
                  </CardFooter>
                </Card>
              )}

              {/* API Keys List */}
              {loadingApiKeys ? (
                <div className="flex justify-center items-center h-40">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : apiKeys.length === 0 ? (
                <div className="text-center py-8">
                  <Key className="mx-auto h-12 w-12 text-muted-foreground" />
                  <h3 className="mt-4 text-lg font-medium">No API Keys</h3>
                  <p className="mt-2 text-sm text-muted-foreground">
                    You haven't created any API keys yet.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {apiKeys.map((key) => (
                    <Card key={key.id} className={key.revoked ? "opacity-60" : ""}>
                      <CardHeader className="pb-2">
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="text-lg">{key.key_name}</CardTitle>
                            <CardDescription>
                              {key.api_key_prefix}••••••••
                            </CardDescription>
                          </div>
                          <div className="flex flex-col items-end gap-1">
                            {key.revoked ? (
                              <Badge variant="destructive">Revoked</Badge>
                            ) : key.expires_at && new Date(key.expires_at) < new Date() ? (
                              <Badge variant="outline">Expired</Badge>
                            ) : (
                              <Badge variant="outline">Active</Badge>
                            )}

                            {key.key_type && key.key_type !== "user" && (
                              <Badge variant="secondary">
                                {key.key_type === "proxmox_node"
                                  ? "Proxmox Node"
                                  : key.key_type === "windows_vm"
                                    ? "Windows VM"
                                    : key.key_type === "farmlabs"
                                      ? "FarmLabs"
                                      : key.key_type}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <p className="text-muted-foreground">Created</p>
                            <p>{formatDate(key.created_at)}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Expires</p>
                            <p>{key.expires_at ? formatDate(key.expires_at) : "Never"}</p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Last Used</p>
                            <p>{key.last_used_at ? formatDate(key.last_used_at) : "Never"}</p>
                          </div>
                          {key.key_type && key.key_type !== "user" && key.resource_id && (
                            <div>
                              <p className="text-muted-foreground">Resource ID</p>
                              <p>{key.resource_id}</p>
                            </div>
                          )}
                        </div>
                        {key.scopes && key.scopes.length > 0 && (
                          <div className="mt-2">
                            <p className="text-muted-foreground">Permissions</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {key.scopes.map(scope => (
                                <Badge key={scope} variant="outline">{scope}</Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </CardContent>
                      <CardFooter>
                        {!key.revoked && (
                          <AlertDialog open={keyToRevoke === key.id} onOpenChange={(open) => !open && setKeyToRevoke(null)}>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => setKeyToRevoke(key.id)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Revoke
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Revoke API Key</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to revoke this API key? This action cannot be undone.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => onRevokeApiKey(key.id)}
                                  disabled={revokingKey}
                                >
                                  {revokingKey ? (
                                    <>
                                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                      Revoking...
                                    </>
                                  ) : (
                                    "Revoke"
                                  )}
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                      </CardFooter>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Log Management</CardTitle>
              <CardDescription>
                Manage log storage and retention settings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <LogsCleanup />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
