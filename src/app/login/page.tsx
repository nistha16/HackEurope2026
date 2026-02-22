"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = React.useState("");

  function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    login(email.trim());
    router.push("/compare");
  }

  return (
    <main className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold text-gray-900">
            Fibre<span className="text-emerald-600">Transfer</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            Sign in to track your Premium subscription
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email"
            required
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
          />
          <Button
            type="submit"
            className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            Continue with email
          </Button>
        </form>

        <div className="text-center space-y-2">
          <p className="text-xs text-zinc-400">or</p>
          <Button asChild variant="outline" className="w-full rounded-xl">
            <Link href="/compare">Continue as guest</Link>
          </Button>
        </div>

        <p className="text-center text-xs text-zinc-400">
          Don&apos;t have an account?{" "}
          <Link href="/subscribe" className="text-emerald-600 hover:underline">
            Subscribe for €2.99/month
          </Link>
        </p>
      </div>
    </main>
  );
}
