import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { AUTH_CONFIG } from "./lib/config"

export function middleware(request: NextRequest) {
  // Get the token from cookies
  const token = request.cookies.get(AUTH_CONFIG.tokenKey)?.value

  // Get the pathname from the request URL
  const { pathname } = request.nextUrl

  // Log the request for debugging
  console.log(`Middleware processing: ${pathname}, token: ${token ? 'exists' : 'none'}`)

  // Define public paths that don't require authentication
  const publicPaths = ["/auth/login", "/auth/register", "/auth/forgot-password"]

  // Check if the path is public
  const isPublicPath = publicPaths.some((path) => pathname.startsWith(path))

  // If the path is not public and there's no token, redirect to login
  if (!isPublicPath && !token) {
    console.log(`Redirecting to login: ${pathname}`)
    const url = new URL("/auth/login", request.url)
    url.searchParams.set("callbackUrl", encodeURI(pathname))
    return NextResponse.redirect(url)
  }

  // If the path is login/register and there's a token, redirect to dashboard
  if (isPublicPath && token) {
    console.log(`Redirecting to dashboard: ${pathname}`)
    return NextResponse.redirect(new URL("/dashboard", request.url))
  }

  // No need to redirect dashboard or test-page paths
  // They should work directly with the route structure

  return NextResponse.next()
}

// See "Matching Paths" below to learn more
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
}
