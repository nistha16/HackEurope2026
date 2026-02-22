"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

function LoginForm() {
  const { signIn, signUp } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/compare";
  const initialMode = searchParams.get("mode") === "signup" ? "signup" : "signin";

  const [mode, setMode] = React.useState<"signin" | "signup">(initialMode);
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setLoading(true);
    setError(null);

    const { error } = mode === "signin"
      ? await signIn(email.trim(), password)
      : await signUp(email.trim(), password);

    setLoading(false);
    if (error) {
      setError(error);
    } else {
      router.push(next);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">

        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold text-gray-900">
            Fibre<span className="text-emerald-600">Transfer</span>
          </h1>
          <p className="text-sm text-muted-foreground">
            {mode === "signin" ? "Welcome back" : "Create your free account"}
          </p>
        </div>

        {/* Sign in / Create account tabs */}
        <div className="flex rounded-xl border bg-white p-1 gap-1">
          <button
            onClick={() => { setMode("signin"); setError(null); }}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
              mode === "signin" ? "bg-zinc-900 text-white" : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            Sign in
          </button>
          <button
            onClick={() => { setMode("signup"); setError(null); }}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
              mode === "signup" ? "bg-zinc-900 text-white" : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            Create account
          </button>
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
          <input
            type="password"
            required
            minLength={6}
            placeholder="Password (min 6 characters)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400"
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <Button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white"
          >
            {loading ? "Please wait..." : mode === "signin" ? "Sign in" : "Create account"}
          </Button>
        </form>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs text-zinc-400">
            <span className="bg-zinc-50 px-2">or</span>
          </div>
        </div>

        <Button asChild variant="outline" className="w-full rounded-xl">
          <Link href="/compare">Continue as guest</Link>
        </Button>

        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 space-y-1">
          <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">
            Premium member?
          </p>
          <p className="text-xs text-emerald-600">
            Sign in above — your Premium badge activates automatically.
            Not subscribed yet?{" "}
            <Link href="/subscribe" className="font-medium underline underline-offset-2">
              Subscribe for €2.99/month →
            </Link>
          </p>
        </div>

      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <React.Suspense>
      <LoginForm />
    </React.Suspense>
  );
}
