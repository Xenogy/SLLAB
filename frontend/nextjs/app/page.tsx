"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { ArrowRight, Bot, Server, Activity } from "lucide-react"
import Link from "next/link"
import { DashboardStats } from "@/components/dashboard-stats"

export default function Home() {
  const router = useRouter()
  return router.push("/dashboard")
}