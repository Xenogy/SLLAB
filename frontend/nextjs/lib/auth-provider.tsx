"use client"

import { createContext, useContext, useState, useEffect, type ReactNode } from "react"
import { AUTH_CONFIG } from "./config"
import { API_CONFIG } from "./config"

type User = {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  is_active: boolean
  created_at: string
  last_login?: string
  avatar_url?: string
} | null

type AuthContextType = {
  user: User
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
  loading: boolean
  token: string | null
  error: string | null
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      try {
        // Get token from localStorage
        const storedToken = localStorage.getItem(AUTH_CONFIG.tokenKey)
        if (storedToken) {
          setToken(storedToken)

          // Validate the token by fetching user info
          const response = await fetch(`${API_CONFIG.baseUrl}/auth/me`, {
            headers: {
              Authorization: `Bearer ${storedToken}`,
            },
            credentials: "include",
          })

          if (response.ok) {
            const userData = await response.json()
            setUser(userData)
          } else {
            // Token is invalid or expired
            localStorage.removeItem(AUTH_CONFIG.tokenKey)
            setToken(null)
          }
        }
      } catch (error) {
        console.error("Authentication error:", error)
        localStorage.removeItem(AUTH_CONFIG.tokenKey)
        setToken(null)
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (username: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      console.log(`Attempting to login with username: ${username}`)
      console.log(`API base URL: ${API_CONFIG.baseUrl}`)

      // Create form data for OAuth2 password flow
      const formData = new URLSearchParams()
      formData.append("username", username)
      formData.append("password", password)

      // Call the API to authenticate
      const loginUrl = `${API_CONFIG.baseUrl}/auth/token`
      console.log(`Sending login request to: ${loginUrl}`)

      const response = await fetch(loginUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
        // Use 'same-origin' for credentials when the API is on the same domain
        // Use 'include' when the API is on a different domain
        credentials: "include",
      })

      console.log(`Login response status: ${response.status}`)

      if (!response.ok) {
        const errorText = await response.text()
        console.error(`Login failed with status ${response.status}:`, errorText)

        let errorDetail = "Login failed"
        try {
          const errorData = JSON.parse(errorText)
          errorDetail = errorData.detail || "Login failed"
        } catch (e) {
          // If the response is not valid JSON, use the raw text
          errorDetail = errorText || "Login failed"
        }

        throw new Error(errorDetail)
      }

      const data = await response.json()
      console.log("Login successful, received token and user data")

      // Store token in localStorage and as a cookie
      localStorage.setItem(AUTH_CONFIG.tokenKey, data.access_token)

      // Set a cookie for the token as well (for middleware)
      document.cookie = `${AUTH_CONFIG.tokenKey}=${data.access_token}; path=/; max-age=86400; SameSite=Lax`

      setToken(data.access_token)

      // Set user information
      setUser(data.user)
    } catch (error) {
      console.error("Login error:", error)
      setError(error instanceof Error ? error.message : "Login failed")
      throw error
    } finally {
      setLoading(false)
    }
  }

  const register = async (username: string, email: string, password: string, fullName?: string) => {
    setLoading(true)
    setError(null)
    try {
      // Call the API to register
      const response = await fetch(`${API_CONFIG.baseUrl}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
          full_name: fullName,
        }),
        credentials: "include",
      })

      if (!response.ok) {
        const errorData = await response.json()
        console.error("Registration API error:", errorData)
        throw new Error(errorData.detail || "Registration failed")
      }

      // Log the successful registration
      console.log("Registration successful, attempting login")

      // After registration, automatically log in
      try {
        await login(username, password)
      } catch (loginError) {
        console.error("Auto-login after registration failed:", loginError)
        // Even if auto-login fails, registration was successful
        // We'll just throw a more specific error
        throw new Error("Registration successful, but automatic login failed. Please try logging in manually.")
      }
    } catch (error) {
      console.error("Registration error:", error)
      setError(error instanceof Error ? error.message : "Registration failed")
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    // Remove token from localStorage
    localStorage.removeItem(AUTH_CONFIG.tokenKey)

    // Remove token from cookies
    document.cookie = `${AUTH_CONFIG.tokenKey}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax`

    // Clear auth state
    setToken(null)
    setUser(null)

    console.log("User logged out successfully")
  }

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, token, error }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
