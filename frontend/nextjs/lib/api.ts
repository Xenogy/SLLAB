import { API_CONFIG, AUTH_CONFIG } from "./config"

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE"
  headers?: Record<string, string>
  body?: any
  cache?: RequestCache
  params?: Record<string, string | number | boolean>
  isPublic?: boolean  // Flag to indicate if the endpoint is public (no auth required)
}

// Get auth token from localStorage or cookie
const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    // First try to get token from localStorage
    const token = localStorage.getItem(AUTH_CONFIG.tokenKey)
    if (token) {
      // Log token for debugging (first 10 chars only for security)
      const tokenPreview = token.substring(0, 10) + '...'
      console.log(`Retrieved token from localStorage: ${tokenPreview}`)
      return token
    }

    // If not in localStorage, try to get from cookie
    const cookies = document.cookie.split(';').map(cookie => cookie.trim())
    const tokenCookie = cookies.find(cookie => cookie.startsWith(`${AUTH_CONFIG.tokenKey}=`))
    if (tokenCookie) {
      const cookieToken = tokenCookie.split('=')[1]
      if (cookieToken) {
        // Store in localStorage for future use
        localStorage.setItem(AUTH_CONFIG.tokenKey, cookieToken)

        // Log token for debugging (first 10 chars only for security)
        const tokenPreview = cookieToken.substring(0, 10) + '...'
        console.log(`Retrieved token from cookie: ${tokenPreview}`)
        return cookieToken
      }
    }

    console.warn('No auth token found in localStorage or cookies')
    return null
  }
  console.warn('Window object not available (SSR context)')
  return null
}

export async function fetchAPI<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", headers = {}, body, cache = "default", params = {}, isPublic = false } = options

  const requestHeaders: HeadersInit = {
    ...API_CONFIG.defaultHeaders,
    ...headers,
  }

  // Add auth token to all requests unless it's a public endpoint
  if (!isPublic) {
    const token = getAuthToken()
    if (token) {
      // Use Bearer token for authorization
      requestHeaders.Authorization = `Bearer ${token}`

      // Log the token for debugging
      console.log(`Using token for ${endpoint}: ${token.substring(0, 10)}...`)

      // For backward compatibility with existing endpoints that use token as a query param
      // Note: We're keeping this for compatibility, but the Bearer token should be the primary method
      if (endpoint.startsWith('/accounts') ||
          endpoint.startsWith('/cards') ||
          endpoint.startsWith('/hardware') ||
          endpoint.startsWith('/steam') ||
          endpoint.startsWith('/account-status') ||
          endpoint.startsWith('/upload') ||
          endpoint.startsWith('/logs')) {  // Add logs endpoint to use token as query param
        params.token = token
      }
    } else {
      console.warn(`No auth token found for request to ${endpoint}`)
      // If this is not a public endpoint and we don't have a token, we might want to redirect to login
      if (endpoint !== '/auth/signup-status' && !endpoint.startsWith('/auth/register')) {
        console.warn('Non-public endpoint requested without authentication token')

        // For debugging - check if we have a cookie with the token
        if (typeof document !== 'undefined') {
          const cookies = document.cookie.split(';').map(cookie => cookie.trim())
          const tokenCookie = cookies.find(cookie => cookie.startsWith(`${AUTH_CONFIG.tokenKey}=`))
          if (tokenCookie) {
            console.log(`Found token cookie: ${tokenCookie.substring(0, 20)}...`)
          } else {
            console.warn('No token cookie found either')
          }
        }
      }
    }
  } else {
    console.log(`Public endpoint requested: ${endpoint}`)
  }

  // Build URL with query parameters
  const url = new URL(`${API_CONFIG.baseUrl}${endpoint}`)
  Object.entries(params).forEach(([key, value]) => {
    url.searchParams.append(key, String(value))
  })

  const requestOptions: RequestInit = {
    method,
    headers: requestHeaders,
    cache,
    ...(body ? { body: JSON.stringify(body) } : {}),
  }

  try {
    console.log(`Fetching ${method} ${url.toString()}`)
    const response = await fetch(url.toString(), requestOptions)

    // Handle HTTP errors
    if (!response.ok) {
      // Try to get detailed error information
      const errorText = await response.text()
      let errorDetail = `API error: ${response.status}`

      try {
        // Try to parse as JSON
        const errorData = JSON.parse(errorText)

        // Extract the detail message
        if (errorData.detail) {
          console.log("Error detail from API:", errorData.detail)
          errorDetail = errorData.detail
        } else {
          console.log("Error data from API:", errorData)
          errorDetail = JSON.stringify(errorData)
        }
      } catch (e) {
        // If not valid JSON, use the raw text
        console.log("Error text from API (not JSON):", errorText)
        if (errorText) {
          errorDetail = errorText
        }
      }

      // Special handling for authentication errors
      if (response.status === 401) {
        console.error('Authentication error. Token may be invalid or expired.')
        // Clear the token if it's an authentication error
        if (typeof window !== 'undefined') {
          localStorage.removeItem(AUTH_CONFIG.tokenKey)
        }
        errorDetail = 'Not authenticated. Please log in again.'
      }

      // Special handling for registration errors
      if (response.status === 400 && endpoint === '/auth/register') {
        console.error('Registration error:', errorDetail)
      }

      // Special handling for server errors during registration
      if (response.status === 500 && endpoint === '/auth/register') {
        console.error('Server error during registration:', errorDetail)
        // If it's a database connection error, provide a more user-friendly message
        if (errorDetail === 'Database connection error') {
          errorDetail = 'Registration failed. The username or email may already be registered.'
        }
      }

      console.error(`API error (${response.status}): ${errorDetail}`)
      throw new Error(errorDetail)
    }

    // Parse JSON response
    const data = await response.json()
    return data as T
  } catch (error) {
    console.error(`API request failed: ${endpoint}`, error)
    throw error
  }
}

// Authentication API endpoints
export const authAPI = {
  // Login to get access token
  login: (username: string, password: string): Promise<any> => {
    const formData = new URLSearchParams()
    formData.append("username", username)
    formData.append("password", password)

    return fetch(`${API_CONFIG.baseUrl}/auth/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error("Authentication failed")
      return res.json()
    })
  },

  // Register a new user (public endpoint, no auth required)
  register: (userData: { username: string; email: string; password: string; full_name?: string }): Promise<any> =>
    fetchAPI<any>(`/auth/register`, {
      method: "POST",
      body: userData,
      isPublic: true  // Mark as public endpoint
    }),

  // Get current user information
  getCurrentUser: (): Promise<any> =>
    fetchAPI<any>(`/auth/me`),

  // Change password
  changePassword: (oldPassword: string, newPassword: string): Promise<any> =>
    fetchAPI<any>(`/auth/change-password`, {
      method: "POST",
      body: { old_password: oldPassword, new_password: newPassword },
    }),

  // Check if signups are enabled (public endpoint, no auth required)
  getSignupStatus: (): Promise<{ signups_enabled: boolean }> =>
    fetchAPI<{ signups_enabled: boolean }>(`/auth/signup-status`, {
      isPublic: true  // Mark as public endpoint
    }),
}

// Types for account list API
export interface AccountListParams {
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
  filter_prime?: boolean;
  filter_lock?: boolean;
  filter_perm_lock?: boolean;
}

export interface AccountResponse {
  acc_id: string;
  acc_username: string;
  acc_email_address: string;
  prime: boolean;
  lock: boolean;
  perm_lock: boolean;
  acc_created_at: number;
}

export interface AccountListResponse {
  accounts: AccountResponse[];
  total: number;
  limit: number;
  offset: number;
}

// Upload response types
export interface ValidationErrorDetail {
  loc: string[];
  msg: string;
  type: string;
}

export interface AccountValidationError {
  account_id?: string;
  row_number?: number;
  errors: ValidationErrorDetail[];
}

export interface UploadResponse {
  status: string;
  message: string;
  total_processed: number;
  successful_count: number;
  failed_count: number;
  successful_accounts: string[];
  failed_accounts: AccountValidationError[];
}

// API endpoints for accounts
export const accountsAPI = {
  // Get accounts with pagination, sorting, and filtering (GET method)
  getAccounts: (params: AccountListParams = {}): Promise<AccountListResponse> =>
    fetchAPI<AccountListResponse>(`/accounts/list`, {
      params: params as Record<string, string | number | boolean>,
    }),

  // Get accounts with pagination, sorting, and filtering (POST method)
  getAccountsPost: (params: AccountListParams = {}): Promise<AccountListResponse> =>
    fetchAPI<AccountListResponse>(`/accounts/list`, {
      method: "POST",
      body: params,
    }),

  // Get account by ID
  getAccount: (id: string): Promise<any> =>
    fetchAPI<any>(`/accounts/${id}`),

  // Create a new account
  createAccounts: (accountData: any): Promise<any> =>
    fetchAPI<any>(`/accounts/new/bulk`, {
      method: "POST",
      body: accountData,
    }),

  // Update an account
  updateAccount: (id: string, accountData: any): Promise<any> =>
    fetchAPI<any>(`/accounts/${id}`, {
      method: "PUT",
      body: accountData,
    }),

  // Delete an account
  deleteAccount: (id: string): Promise<void> =>
    fetchAPI<void>(`/accounts/${id}`, {
      method: "DELETE",
    }),

  // Upload accounts from CSV file
  uploadCSV: (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAuthToken();

    return fetch(`${API_CONFIG.baseUrl}/upload/csv?token=${token}`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(res => {
      if (!res.ok) throw new Error("Failed to upload CSV file");
      return res.json();
    });
  },

  // Upload accounts from JSON file
  uploadJSON: (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const token = getAuthToken();

    return fetch(`${API_CONFIG.baseUrl}/upload/json?token=${token}`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(res => {
      if (!res.ok) throw new Error("Failed to upload JSON file");
      return res.json();
    });
  },
}

// API endpoints for hardware
export const hardwareAPI = {
  // Get all hardware profiles
  getHardwareProfiles: (): Promise<any[]> =>
    fetchAPI<any[]>(`/hardware`),

  // Get hardware profile by ID
  getHardwareProfile: (id: string): Promise<any> =>
    fetchAPI<any>(`/hardware/${id}`),

  // Create a new hardware profile
  createHardwareProfile: (hardwareData: any): Promise<any> =>
    fetchAPI<any>(`/hardware/new`, {
      method: "POST",
      body: hardwareData,
    }),

  // Update a hardware profile
  updateHardwareProfile: (id: string, hardwareData: any): Promise<any> =>
    fetchAPI<any>(`/hardware/${id}`, {
      method: "PUT",
      body: hardwareData,
    }),

  // Delete a hardware profile
  deleteHardwareProfile: (id: string): Promise<void> =>
    fetchAPI<void>(`/hardware/${id}`, {
      method: "DELETE",
    }),
}

// Hardware types
export type HardwareResponse = {
  id: string;
  name: string;
  cpu: string;
  gpu: string;
  ram: string;
  storage: string;
  os: string;
  created_at: string;
  updated_at: string;
}

// VM types
export type VMStatus = 'running' | 'stopped' | 'error';

export type VMResponse = {
  id: number;
  vmid: number;
  name: string;
  ip_address: string | null;
  status: VMStatus;
  cpu_cores: number | null;
  cpu_usage_percent: number | null;
  memory_mb: number | null;
  disk_gb: number | null;
  uptime_seconds: number | null;
  proxmox_node_id: number | null;
  proxmox_node: string | null;
  template_id: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  owner_id: number;
}

export type VMListParams = {
  limit?: number;
  offset?: number;
  search?: string;
  status?: VMStatus;
}

export type VMListResponse = {
  vms: VMResponse[];
  total: number;
  limit: number;
  offset: number;
}

export type VMCreateParams = {
  vmid: number;
  name: string;
  ip_address?: string;
  status?: VMStatus;
  cpu_cores?: number;
  cpu_usage_percent?: number;
  memory_mb?: number;
  disk_gb?: number;
  uptime_seconds?: number;
  proxmox_node_id?: number;
  proxmox_node?: string;  // For backward compatibility
  template_id?: number;
  notes?: string;
}

// API endpoints for VMs
export const vmsAPI = {
  // Get VMs with pagination and filtering
  getVMs: (params: VMListParams = {}): Promise<VMListResponse> =>
    fetchAPI<VMListResponse>(`/vms`, {
      params: params as Record<string, string | number | boolean>,
    }),

  // Get VM by ID
  getVM: (id: number): Promise<VMResponse> =>
    fetchAPI<VMResponse>(`/vms/${id}`),

  // Create a new VM
  createVM: (vmData: VMCreateParams): Promise<VMResponse> =>
    fetchAPI<VMResponse>(`/vms`, {
      method: "POST",
      body: vmData,
    }),

  // Update a VM
  updateVM: (id: number, vmData: VMCreateParams): Promise<VMResponse> =>
    fetchAPI<VMResponse>(`/vms/${id}`, {
      method: "PUT",
      body: vmData,
    }),

  // Delete a VM
  deleteVM: (id: number): Promise<void> =>
    fetchAPI<void>(`/vms/${id}`, {
      method: "DELETE",
    }),

  // Get VMs from all connected Proxmox nodes
  getProxmoxVMs: (): Promise<VMResponse[]> =>
    fetchAPI<VMResponse[]>(`/vms/proxmox`),

  // Get VMs from a specific Proxmox node
  getProxmoxNodeVMs: (nodeId: number): Promise<VMResponse[]> =>
    fetchAPI<VMResponse[]>(`/vms/proxmox/${nodeId}`),
}

// Proxmox Node types
export type ProxmoxNodeStatus = 'connected' | 'disconnected' | 'error';

export type ProxmoxNodeResponse = {
  id: number;
  name: string;
  hostname: string;
  port: number;
  status: ProxmoxNodeStatus;
  api_key: string;
  whitelist: number[];
  last_seen: string | null;
  created_at: string;
  updated_at: string;
  owner_id: number;
}

export type ProxmoxNodeListParams = {
  limit?: number;
  offset?: number;
  search?: string;
  status?: ProxmoxNodeStatus;
}

export type ProxmoxNodeListResponse = {
  nodes: ProxmoxNodeResponse[];
  total: number;
  limit: number;
  offset: number;
}

export type ProxmoxNodeCreateParams = {
  name: string;
  hostname: string;
  port?: number;
}

export type ProxmoxNodeVerifyResponse = {
  success: boolean;
  message: string;
  node_id: number;
  status: ProxmoxNodeStatus;
}

export type VMIDWhitelistParams = {
  node_id: number;
  vmids: number[];
}

// User Settings types
export type UserSettings = {
  id: number;
  user_id: number;
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  date_format: string;
  time_format: '12h' | '24h';
  notifications_enabled: boolean;
  email_notifications: boolean;
  auto_refresh_interval: number;
  items_per_page: number;
  created_at: string;
  updated_at: string;
}

export type UserSettingsUpdateParams = Partial<Omit<UserSettings, 'id' | 'user_id' | 'created_at' | 'updated_at'>>;

// API Key types
export type APIKey = {
  id: number;
  user_id: number;
  key_name: string;
  api_key_prefix: string;
  scopes: string[];
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
  revoked: boolean;
  key_type?: string;
  resource_id?: number;
}

export type APIKeyWithFullKey = APIKey & {
  api_key: string;
}

export type APIKeyCreateParams = {
  key_name: string;
  key_type?: string;
  resource_id?: number;
  expires_in_days?: number;
  scopes?: string[];
}

export type APIKeyListResponse = {
  api_keys: APIKey[];
  total: number;
}

export type ResourceAPIKeyCreateParams = {
  resource_type: string;
  resource_id: number;
}

// API endpoints for Settings
export const settingsAPI = {
  // Get user settings
  getUserSettings: (): Promise<UserSettings> =>
    fetchAPI<UserSettings>(`/settings/user`),

  // Update user settings
  updateUserSettings: (settings: UserSettingsUpdateParams): Promise<UserSettings> =>
    fetchAPI<UserSettings>(`/settings/user`, {
      method: "PATCH",
      body: settings,
    }),

  // List API keys
  listAPIKeys: (limit: number = 10, offset: number = 0, includeRevoked: boolean = false): Promise<APIKeyListResponse> =>
    fetchAPI<APIKeyListResponse>(`/settings/api-keys`, {
      params: { limit, offset, include_revoked: includeRevoked },
    }),

  // Create API key
  createAPIKey: (params: APIKeyCreateParams): Promise<APIKeyWithFullKey> =>
    fetchAPI<APIKeyWithFullKey>(`/settings/api-keys`, {
      method: "POST",
      body: params,
    }),

  // Revoke API key
  revokeAPIKey: (keyId: number): Promise<APIKey> =>
    fetchAPI<APIKey>(`/settings/api-keys/${keyId}`, {
      method: "DELETE",
    }),

  // List resource API keys
  listResourceAPIKeys: (
    resourceType: string,
    resourceId: number,
    limit: number = 10,
    offset: number = 0,
    includeRevoked: boolean = false
  ): Promise<APIKeyListResponse> =>
    fetchAPI<APIKeyListResponse>(`/settings/resource-api-keys`, {
      params: {
        resource_type: resourceType,
        resource_id: resourceId,
        limit,
        offset,
        include_revoked: includeRevoked
      },
    }),

  // Create a resource API key
  createResourceAPIKey: (params: ResourceAPIKeyCreateParams): Promise<APIKeyWithFullKey> =>
    fetchAPI<APIKeyWithFullKey>(`/settings/resource-api-keys`, {
      method: "POST",
      body: params,
    }),
}

// API endpoints for Proxmox Nodes
export const proxmoxNodesAPI = {
  // Get Proxmox Nodes with pagination and filtering
  getNodes: (params: ProxmoxNodeListParams = {}): Promise<ProxmoxNodeListResponse> =>
    fetchAPI<ProxmoxNodeListResponse>(`/proxmox-nodes`, {
      params: params as Record<string, string | number | boolean>,
    }),

  // Get Proxmox Node by ID
  getNode: (id: number): Promise<ProxmoxNodeResponse> =>
    fetchAPI<ProxmoxNodeResponse>(`/proxmox-nodes/${id}`),

  // Create a new Proxmox Node
  createNode: (nodeData: ProxmoxNodeCreateParams): Promise<ProxmoxNodeResponse> =>
    fetchAPI<ProxmoxNodeResponse>(`/proxmox-nodes`, {
      method: "POST",
      body: nodeData,
    }),

  // Update a Proxmox Node
  updateNode: (id: number, nodeData: ProxmoxNodeCreateParams): Promise<ProxmoxNodeResponse> =>
    fetchAPI<ProxmoxNodeResponse>(`/proxmox-nodes/${id}`, {
      method: "PUT",
      body: nodeData,
    }),

  // Delete a Proxmox Node
  deleteNode: (id: number): Promise<void> =>
    fetchAPI<void>(`/proxmox-nodes/${id}`, {
      method: "DELETE",
    }),

  // Regenerate API key for a Proxmox Node
  regenerateApiKey: (id: number): Promise<ProxmoxNodeResponse> =>
    fetchAPI<ProxmoxNodeResponse>(`/proxmox-nodes/${id}/regenerate-api-key`, {
      method: "POST",
    }),

  // Verify connection to a Proxmox Node
  verifyConnection: (id: number, apiKey: string): Promise<ProxmoxNodeVerifyResponse> =>
    fetchAPI<ProxmoxNodeVerifyResponse>(`/proxmox-nodes/verify`, {
      method: "POST",
      params: { node_id: id, api_key: apiKey },
    }),

  // Set VMID whitelist for a Proxmox Node
  setVMIDWhitelist: (params: VMIDWhitelistParams): Promise<{ success: boolean, message: string }> =>
    fetchAPI<{ success: boolean, message: string }>(`/proxmox-nodes/whitelist`, {
      method: "POST",
      body: params,
    }),

  // Get VMID whitelist for a Proxmox Node
  getNodeWhitelist: (nodeId: number): Promise<{ node_id: number, vmids: number[], success: boolean, message: string }> =>
    fetchAPI<{ node_id: number, vmids: number[], success: boolean, message: string }>(`/proxmox-nodes/whitelist/${nodeId}`),

  // Sync VMs from a Proxmox Node
  syncNodeVMs: (nodeId: number): Promise<{ success: boolean, message: string }> =>
    fetchAPI<{ success: boolean, message: string }>(`/proxmox-nodes/${nodeId}/sync-vms`, {
      method: "POST",
    }),
}

// Timeseries types
export type TimeseriesDataPoint = {
  timestamp: string;
  value: number;
}

export type TimeseriesMetric = {
  id: number;
  name: string;
  display_name: string;
  description: string;
  unit: string;
  data_type: string;
}

export type TimeseriesCategory = {
  id: number;
  name: string;
  description: string;
  metrics: TimeseriesMetric[];
}

export type TimeseriesParams = {
  start_time?: string;
  end_time?: string;
  period?: 'raw' | 'hourly' | 'daily' | 'weekly' | 'monthly';
  entity_type?: string;
  entity_id?: string;
  limit?: number;
  offset?: number;
}

export type TimeseriesResponse = {
  metric: string;
  data: TimeseriesDataPoint[];
  start_time: string;
  end_time: string;
  period: string;
}

export type TimeseriesStatistics = {
  min: number | null;
  max: number | null;
  avg: number | null;
  sum: number | null;
  count: number;
}

export type TimeseriesStatisticsResponse = {
  metric: string;
  statistics: TimeseriesStatistics;
  start_time: string;
  end_time: string;
  entity_type: string | null;
  entity_id: string | null;
}

export type TimeseriesSystemOverviewResponse = {
  cpu_usage: TimeseriesDataPoint[];
  memory_usage: TimeseriesDataPoint[];
  disk_usage: TimeseriesDataPoint[];
  vm_count: TimeseriesDataPoint[];
  account_count: TimeseriesDataPoint[];
  period: string;
  start_time: string;
  end_time: string;
}

// API endpoints for Timeseries
// Windows VM Agent types
export type WindowsVMAgentStatus = 'registered' | 'running' | 'stopped' | 'error';

export type WindowsVMAgentResponse = {
  vm_id: string;
  vm_name: string | null;
  status: WindowsVMAgentStatus;
  ip_address: string | null;
  cpu_usage_percent: number | null;
  memory_usage_percent: number | null;
  disk_usage_percent: number | null;
  uptime_seconds: number | null;
  last_seen: string | null;
  created_at: string;
  updated_at: string;
}

export type WindowsVMAgentListParams = {
  limit?: number;
  offset?: number;
  search?: string;
  status?: WindowsVMAgentStatus;
}

export type WindowsVMAgentListResponse = {
  agents: WindowsVMAgentResponse[];
  total: number;
  limit: number;
  offset: number;
}

// API endpoints for Windows VM Agent
export const windowsVMAgentAPI = {
  // Get agent status for a specific VM
  getAgentStatus: (vmId: string): Promise<WindowsVMAgentResponse> =>
    fetchAPI<WindowsVMAgentResponse>(`/windows-vm-agent/status/${vmId}`),

  // Get all agents with pagination and filtering
  getAgents: (params: WindowsVMAgentListParams = {}): Promise<WindowsVMAgentListResponse> =>
    fetchAPI<WindowsVMAgentListResponse>(`/windows-vm-agent/agents`, {
      params: params as Record<string, string | number | boolean>,
    }),

  // Register a new Windows VM agent
  registerAgent: (vmId: string, vmName?: string): Promise<{
    vm_id: string;
    api_key: string;
    message: string;
    powershell_command: string;
    powershell_script: string;
  }> =>
    fetchAPI(`/windows-vm-agent/register`, {
      method: 'POST',
      params: {
        vm_id: vmId,
        ...(vmName ? { vm_name: vmName } : {}),
      },
    }),
}

// Types for ban check API
export interface BanCheckTaskParams {
  limit?: number;
  offset?: number;
  status?: string;
}

export interface BanCheckTask {
  task_id: string;
  status: string;
  message?: string;
  progress?: number;
  results?: BanCheckResult[];
  proxy_stats?: any;
  created_at?: string;
  updated_at?: string;
  owner_id?: number;
}

export interface BanCheckResult {
  steam_id: string;
  status_summary: string;
  details: string;
  proxy_used?: string;
  batch_id?: any;
}

export interface BanCheckTaskListResponse {
  tasks: BanCheckTask[];
  total: number;
  limit: number;
  offset: number;
}

// API endpoints for ban checker
export const banCheckAPI = {
  // Check Steam IDs for bans
  checkSteamIDs: (steamIDs: string[], options: any = {}): Promise<BanCheckTask> => {
    const formData = new FormData();
    steamIDs.forEach(id => formData.append('steam_ids', id));

    // Add proxy list if provided
    if (options.proxy_list_str) formData.append('proxy_list_str', options.proxy_list_str);

    // If auto-balancing is enabled, don't send the parameters
    if (!options.use_auto_balancing) {
      // Add optional parameters
      if (options.logical_batch_size) formData.append('logical_batch_size', options.logical_batch_size.toString());
      if (options.max_concurrent_batches) formData.append('max_concurrent_batches', options.max_concurrent_batches.toString());
      if (options.max_workers_per_batch) formData.append('max_workers_per_batch', options.max_workers_per_batch.toString());
      if (options.inter_request_submit_delay) formData.append('inter_request_submit_delay', options.inter_request_submit_delay.toString());
      if (options.max_retries_per_url) formData.append('max_retries_per_url', options.max_retries_per_url.toString());
      if (options.retry_delay_seconds) formData.append('retry_delay_seconds', options.retry_delay_seconds.toString());
    }

    const token = getAuthToken();
    return fetch(`${API_CONFIG.baseUrl}/ban-check/check/steamids`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(res => {
      if (!res.ok) throw new Error("Failed to submit Steam IDs for ban check");
      return res.json();
    });
  },

  // Check CSV file for bans
  checkCSV: (file: File, steamIdColumn: string, options: any = {}): Promise<BanCheckTask> => {
    const formData = new FormData();
    formData.append('csv_file', file);
    formData.append('steam_id_column', steamIdColumn);

    // Add proxy list if provided
    if (options.proxy_list_str) formData.append('proxy_list_str', options.proxy_list_str);

    // If auto-balancing is enabled, don't send the parameters
    if (!options.use_auto_balancing) {
      // Add optional parameters
      if (options.logical_batch_size) formData.append('logical_batch_size', options.logical_batch_size.toString());
      if (options.max_concurrent_batches) formData.append('max_concurrent_batches', options.max_concurrent_batches.toString());
      if (options.max_workers_per_batch) formData.append('max_workers_per_batch', options.max_workers_per_batch.toString());
      if (options.inter_request_submit_delay) formData.append('inter_request_submit_delay', options.inter_request_submit_delay.toString());
      if (options.max_retries_per_url) formData.append('max_retries_per_url', options.max_retries_per_url.toString());
      if (options.retry_delay_seconds) formData.append('retry_delay_seconds', options.retry_delay_seconds.toString());
    }

    const token = getAuthToken();
    return fetch(`${API_CONFIG.baseUrl}/ban-check/check/csv`, {
      method: "POST",
      body: formData,
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }).then(res => {
      if (!res.ok) throw new Error("Failed to submit CSV for ban check");
      return res.json();
    });
  },

  // Get list of tasks
  getTasks: (params: BanCheckTaskParams = {}): Promise<BanCheckTaskListResponse> =>
    fetchAPI<BanCheckTaskListResponse>(`/ban-check/tasks`, {
      params: {
        limit: 50, // Default to a higher limit to get more tasks
        ...params as Record<string, string | number | boolean>,
      },
    }),

  // Get task by ID
  getTask: (taskId: string): Promise<BanCheckTask> =>
    fetchAPI<BanCheckTask>(`/ban-check/tasks/${taskId}`),
};

export const timeseriesAPI = {
  // Get available metrics
  getMetrics: (): Promise<TimeseriesCategory[]> =>
    fetchAPI<TimeseriesCategory[]>(`/timeseries/metrics`),

  // Get timeseries data for a specific metric
  getMetricData: (metricName: string, params: TimeseriesParams = {}): Promise<TimeseriesResponse> =>
    fetchAPI<TimeseriesResponse>(`/timeseries/data/${metricName}`, {
      params: params as Record<string, string | number | boolean>,
    }),

  // Get latest value for a specific metric
  getLatestMetricValue: (metricName: string, entityType?: string, entityId?: string): Promise<{ value: number | null }> =>
    fetchAPI<{ value: number | null }>(`/timeseries/latest/${metricName}`, {
      params: {
        ...(entityType && { entity_type: entityType }),
        ...(entityId && { entity_id: entityId }),
      },
    }),

  // Get statistics for a specific metric
  getMetricStatistics: (metricName: string, params: TimeseriesParams = {}): Promise<TimeseriesStatisticsResponse> =>
    fetchAPI<TimeseriesStatisticsResponse>(`/timeseries/statistics/${metricName}`, {
      params: params as Record<string, string | number | boolean>,
    }),

  // Get system overview metrics
  getSystemOverview: (period: string = 'hourly', duration: string = 'day'): Promise<TimeseriesSystemOverviewResponse> => {
    console.log(`API call: getSystemOverview(${period}, ${duration})`)
    return fetchAPI<TimeseriesSystemOverviewResponse>(`/timeseries/system/overview`, {
      params: { period, duration },
    }).then(response => {
      console.log('System overview API response:', response)
      return response
    }).catch(error => {
      console.error('System overview API error:', error)
      throw error
    })
  },

  // Get VM metrics
  getVMMetrics: (vmId: number, metricName: string, params: TimeseriesParams = {}): Promise<TimeseriesResponse> =>
    fetchAPI<TimeseriesResponse>(`/timeseries/vm/${vmId}/${metricName}`, {
      params: params as Record<string, string | number | boolean>,
    }),
}