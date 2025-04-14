import { RegisterForm } from "@/components/auth/register-form"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Register | Account Manager",
  description: "Create a new account",
}

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight">Account Manager</h1>
          <p className="mt-2 text-center text-sm text-muted-foreground">
            Create a new account to get started
          </p>
        </div>
        <RegisterForm />
      </div>
    </div>
  )
}
