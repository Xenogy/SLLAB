// Log environment variables for debugging
if (typeof window !== 'undefined') {
  console.log('Client-side NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
} else {
  console.log('Server-side NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
}

// API configuration
export const API_CONFIG = {
  // Use the environment variable for the API URL
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",

  // Default request timeout in milliseconds
  timeout: 30000,

  // Default headers
  defaultHeaders: {
    "Content-Type": "application/json",
  },
}

// Auth configuration
export const AUTH_CONFIG = {
  // Local storage key for the auth token
  tokenKey: "accountdb_auth_token",

  // Token expiration time in milliseconds (default: 24 hours)
  tokenExpiration: 24 * 60 * 60 * 1000,
}
