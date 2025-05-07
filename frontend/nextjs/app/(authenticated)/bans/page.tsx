import { Metadata } from "next"
import { BansPageClient } from "./client-components"

export const metadata: Metadata = {
  title: "Steam Ban Checker | Account Manager",
  description: "Check Steam accounts for bans",
}

export default function BansPage() {
  return <BansPageClient />
}
