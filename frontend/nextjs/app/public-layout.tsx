"use client"

import { Toaster } from "@/components/ui/toaster"
import { ReactCompatInitializer } from "./react-compat-initializer"

export default function PublicLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <>
      <ReactCompatInitializer />
      <div className="min-h-screen p-4 md:p-6 max-w-7xl mx-auto">
        {children}
      </div>
      <Toaster />
    </>
  )
}
