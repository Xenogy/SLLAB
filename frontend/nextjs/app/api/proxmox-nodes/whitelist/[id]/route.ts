import { NextRequest, NextResponse } from 'next/server'
import { cookies } from 'next/headers'
import { fetchAPI } from '@/lib/api'
import { AUTH_CONFIG } from '@/lib/config'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const nodeId = params.id

    // Get the auth token from cookies
    const cookieStore = cookies()
    const token = cookieStore.get(AUTH_CONFIG.tokenKey)?.value

    if (!token) {
      console.error('No auth token found in cookies')
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      )
    }

    // Call the backend API to get the whitelist with the token
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://cs2.drandex.org'
    const response = await fetch(`${apiUrl}/proxmox-nodes/whitelist/${nodeId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error(`Error from API: ${response.status} - ${errorText}`)

      // If it's an auth error, return 401
      if (response.status === 401) {
        return NextResponse.json(
          { error: 'Authentication required' },
          { status: 401 }
        )
      }

      return NextResponse.json(
        { error: 'Failed to fetch whitelist from API' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching whitelist:', error)
    return NextResponse.json(
      { error: 'Failed to fetch whitelist' },
      { status: 500 }
    )
  }
}
