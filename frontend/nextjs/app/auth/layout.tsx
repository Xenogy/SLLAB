"use client"

import { Toaster } from "@/components/ui/toaster"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from "@/lib/auth-provider"
import { ReactCompatInitializer } from "../react-compat-initializer"

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <AuthProvider>
        <ReactCompatInitializer />
        <div className="min-h-screen">
          {children}
        </div>
        <Toaster />
      </AuthProvider>
    </ThemeProvider>
  )
}
