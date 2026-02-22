"use client";

import * as React from "react";
import Link from "next/link";
import {
  ArrowLeft,
  Bell,
  BarChart2,
  ScanLine,
  Zap,
  Newspaper,
  Loader2,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const BENEFITS = [
  {
    icon: Zap,
    title: "Unlimited comparisons",
    desc: "Free plan: 3/day. Premium: no limits.",
  },
  {
    icon: Bell,
    title: "Smart timing alerts",
    desc: 'Get notified when the timing score hits your target (e.g. "alert me when score > 0.8").',
  },
  {
    icon: BarChart2,
    title: "Full 1-year historical charts",
    desc: "See 365 days of rate history for any corridor — not just 30 days.",
  },
  {
    icon: ScanLine,
    title: "Receipt scanner",
    desc: "Upload a receipt from any provider and instantly see how much you overpaid.",
  },
  {
    icon: Newspaper,
    title: "Daily market briefings",
    desc: "Morning email with rate movements and timing recommendations for your corridors.",
  },
];

export default function SubscribePage() {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function handleSubscribe() {
    setLoading(true);
    setError(null);
    try {
      const priceId = process.env.NEXT_PUBLIC_STRIPE_PRICE_ID ?? "";
      const res = await fetch("/api/stripe/payment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "subscription", price_id: priceId }),
      });
      const data = await res.json() as { url?: string; error?: string };
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(data.error ?? "Something went wrong. Please try again.");
        setLoading(false);
      }
    } catch {
      setError("Network error. Please try again.");
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50 px-4 py-10 sm:py-14">
      <div className="w-full max-w-lg mx-auto space-y-8">

        {/* Back */}
        <Button asChild variant="ghost" size="sm" className="gap-1.5 -ml-1">
          <Link href="/">
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </Button>

        {/* Hero */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-emerald-100 text-emerald-700 px-3 py-1 text-xs font-medium">
            FibreTransfer Premium
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Send smarter, save more
          </h1>
          <p className="text-muted-foreground text-sm">
            Everything in the free plan, plus timing alerts and full historical data.
          </p>
        </div>

        {/* Pricing card */}
        <div className="rounded-2xl border-2 border-emerald-400 bg-white p-6 shadow-sm space-y-5">
          <div className="flex items-end gap-1">
            <span className="text-4xl font-bold text-gray-900">€2.99</span>
            <span className="text-muted-foreground mb-1">/month</span>
          </div>

          <ul className="space-y-3">
            {BENEFITS.map((b) => (
              <li key={b.title} className="flex items-start gap-3">
                <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
                  <b.icon className="h-3.5 w-3.5" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{b.title}</p>
                  <p className="text-xs text-muted-foreground">{b.desc}</p>
                </div>
              </li>
            ))}
          </ul>

          {error && (
            <p className="text-sm text-red-600 rounded-xl bg-red-50 border border-red-200 px-3 py-2">
              {error}
            </p>
          )}

          <Button
            onClick={handleSubscribe}
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white gap-2"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              "Subscribe Now — €2.99/month"
            )}
          </Button>

          <p className="text-center text-xs text-zinc-400">
            Test card: 4242 4242 4242 4242 · Cancel anytime
          </p>
        </div>

        {/* Free plan comparison */}
        <div className="rounded-2xl border bg-white p-5">
          <p className="text-xs font-semibold text-zinc-500 uppercase tracking-wide mb-3">
            What&apos;s free
          </p>
          <ul className="space-y-2 text-sm text-zinc-600">
            {["3 comparisons/day", "Basic provider ranking", "Hidden fee exposure"].map((item) => (
              <li key={item} className="flex items-center gap-2">
                <Check className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </main>
  );
}
