"use client"

import { Toaster } from "@/components/ui/toaster"
import { AuthProvider } from "@/lib/auth-provider"
import { ReactCompatInitializer } from "../react-compat-initializer"

export default function AuthLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <AuthProvider>
      <ReactCompatInitializer />
      <div className="min-h-screen">
        {children}
      </div>
      <Toaster />
    </AuthProvider>
  )
}
