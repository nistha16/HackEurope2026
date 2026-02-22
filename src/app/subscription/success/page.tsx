"use client";

import * as React from "react";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export default function SubscriptionSuccessPage() {
  const { user, upgradeToPremium } = useAuth();
  const [email, setEmail] = React.useState("");
  const [saved, setSaved] = React.useState(false);

  React.useEffect(() => {
    if (user) {
      upgradeToPremium(user.email);
      setSaved(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSave(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!email.trim()) return;
    upgradeToPremium(email.trim());
    setSaved(true);
  }

  return (
    <main className="min-h-screen bg-zinc-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center space-y-5">
        <div className="flex justify-center">
          <CheckCircle2 className="h-14 w-14 text-emerald-500" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome to Premium!
        </h1>
        <p className="text-muted-foreground text-sm">
          Your subscription is active. You now have access to smart timing
          alerts, full historical charts, receipt scanning, and daily market
          briefings.
        </p>

        {!saved ? (
          <form onSubmit={handleSave} className="space-y-3">
            <p className="text-sm font-medium text-gray-700">
              Save your email to access Premium on any device
            </p>
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
              Save & continue
            </Button>
            <Link
              href="/compare"
              className="block text-xs text-zinc-400 hover:text-zinc-600"
            >
              Continue as guest
            </Link>
          </form>
        ) : (
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button asChild className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
              <Link href="/compare">Start comparing</Link>
            </Button>
            <Button asChild variant="outline" className="rounded-xl">
              <Link href="/compare">Back to Compare</Link>
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
