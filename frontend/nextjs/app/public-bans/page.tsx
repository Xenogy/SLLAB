import { Metadata } from "next"
import { PublicBansPageClient } from "./client-components"
import PublicLayout from "../public-layout"

export const metadata: Metadata = {
  title: "Public Steam Ban Checker | Account Manager",
  description: "Check Steam accounts for bans",
}

export default function PublicBansPage() {
  return (
    <PublicLayout>
      <PublicBansPageClient />
    </PublicLayout>
  )
}
