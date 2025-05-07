import { Metadata } from "next"
import { StatisticsPageClient } from "./client-components"

export const metadata: Metadata = {
  title: "Statistics | Account Manager",
  description: "Account Manager Statistics",
}

export default function StatisticsPage() {
  return <StatisticsPageClient />
}
