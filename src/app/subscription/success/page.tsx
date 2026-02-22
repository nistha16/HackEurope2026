"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";
import { getSupabaseBrowserClient } from "@/lib/supabase";

function SubscriptionSuccessContent() {
  const { user } = useAuth();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get("session_id");
  const [status, setStatus] = React.useState<"idle" | "activating" | "done" | "error">("idle");

  React.useEffect(() => {
    if (!sessionId || !user || status !== "idle") return;

    async function activate() {
      setStatus("activating");
      try {
        const supabase = getSupabaseBrowserClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) { setStatus("error"); return; }

        const res = await fetch("/api/stripe/activate-premium", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            session_id: sessionId,
            access_token: session.access_token,
          }),
        });

        if (res.ok) {
          await supabase.auth.refreshSession();
          setStatus("done");
        } else {
          setStatus("error");
        }
      } catch {
        setStatus("error");
      }
    }

    activate();
  }, [user, sessionId, status]);

  return (
    <main className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center space-y-5">
        <div className="flex justify-center">
          <CheckCircle2 className="h-14 w-14 text-emerald-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome to Premium!</h1>
        <p className="text-muted-foreground text-sm">
          Your subscription is active. You now have access to smart timing
          alerts, full historical charts, and daily market briefings.
        </p>

        {!sessionId ? (
          <p className="text-sm text-red-500">No payment session found.</p>
        ) : !user ? (
          <div className="space-y-3">
            <p className="text-sm font-medium text-gray-700">
              Create an account to activate your Premium badge
            </p>
            <p className="text-xs text-zinc-500">
              Use the email you paid with and set a password — this is how you log back in.
            </p>
            <Button asChild className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
              <Link href={`/login?mode=signup&next=${encodeURIComponent(`/subscription/success?session_id=${sessionId}`)}`}>
                Create account &amp; activate Premium
              </Link>
            </Button>
            <p className="text-xs text-zinc-400">Already have an account?{" "}
              <Link href={`/login?next=${encodeURIComponent(`/subscription/success?session_id=${sessionId}`)}`} className="underline">
                Sign in
              </Link>
            </p>
            <Link href="/compare" className="block text-xs text-zinc-400 hover:text-zinc-600">
              Continue as guest
            </Link>
          </div>
        ) : status === "activating" ? (
          <p className="text-sm text-zinc-400">Activating your Premium badge...</p>
        ) : status === "error" ? (
          <p className="text-sm text-red-500">Could not activate Premium. Please contact support.</p>
        ) : (
          <div className="space-y-3">
            <div className="flex justify-center">
              <span className="rounded-full bg-emerald-100 text-emerald-700 px-3 py-1 text-sm font-semibold ring-1 ring-emerald-300">
                ★ Premium member
              </span>
            </div>
            <p className="text-sm text-emerald-600 font-medium">
              Activated for {user.email}
            </p>
            <Button asChild className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
              <Link href="/compare">Start comparing</Link>
            </Button>
          </div>
        )}

        <p className="text-xs text-zinc-400">
          A confirmation email has been sent by Stripe.
        </p>
      </div>
    </main>
  );
}

export default function SubscriptionSuccessPage() {
  return (
    <React.Suspense>
      <SubscriptionSuccessContent />
    </React.Suspense>
  );
}
