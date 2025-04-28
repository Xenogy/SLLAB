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
    
    // Call the backend API to get VMs from a specific Proxmox node
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://cs2.drandex.org'
    const response = await fetch(`${apiUrl}/vms/proxmox/${nodeId}`, {
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
        { error: 'Failed to fetch VMs from Proxmox node' },
        { status: response.status }
      )
    }
    
    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching VMs from Proxmox node:', error)
    return NextResponse.json(
      { error: 'Failed to fetch VMs from Proxmox node' },
      { status: 500 }
    )
  }
}
