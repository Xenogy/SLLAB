import { API_CONFIG, AUTH_CONFIG } from "./config"

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE"
  headers?: Record<string, string>
  body?: any
  cache?: RequestCache
  params?: Record<string, string | number | boolean>
  isPublic?: boolean  // Flag to indicate if the endpoint is public (no auth required)
}

// Get auth token from localStorage or a secure storage mechanism
const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem(AUTH_CONFIG.tokenKey)
    if (!token) {
      console.warn('No auth token found in localStorage')
      return null
    }

    // Log token for debugging (first 10 chars only for security)
    const tokenPreview = token.substring(0, 10) + '...'
    console.log(`Retrieved token from localStorage: ${tokenPreview}`)
    return token
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
          endpoint.startsWith('/upload')) {
        params.token = token
      }
    } else {
      console.warn(`No auth token found for request to ${endpoint}`)
      // If this is not a public endpoint and we don't have a token, we might want to redirect to login
      if (endpoint !== '/auth/signup-status' && !endpoint.startsWith('/auth/register')) {
        console.warn('Non-public endpoint requested without authentication token')
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
  memory_mb: number | null;
  disk_gb: number | null;
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
  memory_mb?: number;
  disk_gb?: number;
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
