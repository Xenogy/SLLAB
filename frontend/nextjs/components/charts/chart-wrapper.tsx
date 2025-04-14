import type React from "react"

interface ChartWrapperProps {
  children: React.ReactNode
  title?: string
  className?: string
}

export function ChartWrapper({ children, title, className = "" }: ChartWrapperProps) {
  return (
    <div className={`w-full h-full ${className}`}>
      {title && <span className="sr-only">{title}</span>}
      {children}
    </div>
  )
}
