import { NextRequest, NextResponse } from 'next/server'
import { AUTH_CONFIG, API_CONFIG } from '@/lib/config'

export async function POST(req: NextRequest) {
  try {
    // Get token from cookies
    const token = req.cookies.get(AUTH_CONFIG.tokenKey)?.value
    
    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Call backend API
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.baseUrl
    const response = await fetch(`${apiUrl}/timeseries/collect-metrics`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })

    // Return response
    const data = await response.json()
    if (!response.ok) {
      return NextResponse.json({ error: data.detail || 'Failed to collect metrics' }, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Error collecting metrics:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
