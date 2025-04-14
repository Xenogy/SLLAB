import { API_CONFIG, AUTH_CONFIG } from "./config"

type RequestOptions = {
  method?: "GET" | "POST" | "PUT" | "DELETE"
  headers?: Record<string, string>
  body?: any
  cache?: RequestCache
  params?: Record<string, string | number | boolean>
}

// Get auth token from localStorage or a secure storage mechanism
const getAuthToken = (): string | null => {
  if (typeof window !== "undefined") {
    return localStorage.getItem(AUTH_CONFIG.tokenKey)
  }
  return null
}

export async function fetchAPI<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", headers = {}, body, cache = "default", params = {} } = options

  const requestHeaders: HeadersInit = {
    ...API_CONFIG.defaultHeaders,
    ...headers,
  }

  // Add auth token to all requests
  const token = getAuthToken()
  if (token) {
    // Use Bearer token for authorization
    requestHeaders.Authorization = `Bearer ${token}`

    // For backward compatibility with existing endpoints that use token as a query param
    if (endpoint.startsWith('/accounts') ||
        endpoint.startsWith('/cards') ||
        endpoint.startsWith('/hardware') ||
        endpoint.startsWith('/steam') ||
        endpoint.startsWith('/account-status')) {
      params.token = token
    }
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
    const response = await fetch(url.toString(), requestOptions)

    // Handle HTTP errors
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API error: ${response.status}`)
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

  // Register a new user
  register: (userData: { username: string; email: string; password: string; full_name?: string }): Promise<any> =>
    fetchAPI<any>(`/auth/register`, {
      method: "POST",
      body: userData,
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

  // Check if signups are enabled
  getSignupStatus: (): Promise<{ signups_enabled: boolean }> =>
    fetchAPI<{ signups_enabled: boolean }>(`/auth/signup-status`),
}

// API endpoints for accounts
export const accountsAPI = {
  // Get all accounts
  getAccounts: (): Promise<any[]> =>
    fetchAPI<any[]>(`/accounts`),

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
