"use client";

import * as React from "react";
import { CompareForm } from "@/components/compareForm";
import { ProviderRanking } from "@/components/ProviderRanking";
import { Button } from "@/components/ui/button";
import type { ComparisonResponse } from "@/types";
import { Check, Copy, FileText, Info, Loader2 } from "lucide-react";

// Skeleton cards shown while fetching
function ResultsSkeleton() {
  return (
    <div className="w-full max-w-2xl mx-auto space-y-3 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-2xl border bg-background p-5 space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="h-5 w-24 bg-zinc-200 rounded" />
            <div className="h-5 w-16 bg-zinc-200 rounded" />
          </div>
          <div className="h-4 w-40 bg-zinc-200 rounded" />
          <div className="flex gap-2">
            <div className="h-8 w-28 bg-zinc-200 rounded-xl" />
            <div className="h-8 w-20 bg-zinc-200 rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ComparePage() {
  const [result, setResult] = React.useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const [reportLoading, setReportLoading] = React.useState(false);

  // Compare page always starts fresh — no auto-restore from localStorage

  function handleSuccess(data: ComparisonResponse) {
    setResult(data);
    // Smooth scroll to results
    window.setTimeout(() => {
      document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  }

  async function handleGetReport() {
    if (!result) return;
    setReportLoading(true);
    try {
      localStorage.setItem("reportData", JSON.stringify(result));
      const res = await fetch("/api/stripe/payment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "report" }),
      });
      const data = await res.json() as { url?: string; error?: string };
      if (data.url) {
        window.location.href = data.url;
      }
    } catch {
      setReportLoading(false);
    }
  }

  async function handleShare() {
    if (!result) return;
    const url = new URL(window.location.href);
    url.pathname = "/compare/results";
    url.searchParams.set("source", result.source_currency);
    url.searchParams.set("target", result.target_currency);
    url.searchParams.set("amount", String(result.amount));
    try {
      await navigator.clipboard.writeText(url.toString());
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback: select text
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50 px-4 py-10 sm:py-14">
      <div className="w-full max-w-3xl mx-auto space-y-8">

        {/* Heading */}
        <div className="text-center space-y-1">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-gray-900">
            Compare Money Transfers
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            Find the cheapest way to send money abroad — real rates, no hidden fees.
          </p>
        </div>

        {/* Form */}
        <CompareForm
          onSuccess={handleSuccess}
          onLoadingChange={setLoading}
          defaultAmount="500"
          defaultSource="EUR"
          defaultTarget="MAD"
        />

        {/* Mid-market rate banner */}
        {result && !loading && (
          <div className="flex items-start gap-2 rounded-2xl bg-blue-50 border border-blue-200 px-4 py-3 text-sm text-blue-800 max-w-3xl mx-auto">
            <Info className="h-4 w-4 mt-0.5 shrink-0" />
            <span>
              <span className="font-semibold">Mid-market rate:</span>{" "}
              1 {result.source_currency} ={" "}
              <span className="font-semibold">
                {result.mid_market_rate.toFixed(4)} {result.target_currency}
              </span>
              {" "}— the real interbank rate. Providers add a markup on top.
            </span>
          </div>
        )}

        {/* Results section */}
        <div id="results">
          {loading ? (
            <ResultsSkeleton />
          ) : result ? (
            <div className="space-y-4">
              {/* Results header with share button */}
              <div className="flex items-center justify-between max-w-2xl mx-auto">
                <p className="text-sm text-muted-foreground">
                  Showing{" "}
                  <span className="font-medium text-gray-700">
                    {result.results.length} providers
                  </span>{" "}
                  for {result.source_currency} {result.amount.toLocaleString()} →{" "}
                  {result.target_currency}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleShare}
                  className="gap-1.5 rounded-xl"
                >
                  {copied ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-green-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      Share Results
                    </>
                  )}
                </Button>
              </div>

              <ProviderRanking
                results={result.results}
                sourceCurrency={result.source_currency}
                targetCurrency={result.target_currency}
                potentialSavings={result.potential_savings}
              />

              {/* Detailed Report CTA */}
              <div className="max-w-2xl mx-auto rounded-2xl border border-violet-200 bg-violet-50 p-5">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-100 text-violet-600">
                    <FileText className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-violet-900 text-sm">
                      Get your Detailed Transfer Report
                    </p>
                    <p className="mt-0.5 text-xs text-violet-700">
                      Full provider breakdown · Claude AI analysis · Hidden fee audit · Personalised recommendation
                    </p>
                  </div>
                  <Button
                    onClick={handleGetReport}
                    disabled={reportLoading}
                    className="shrink-0 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-sm gap-1.5"
                    size="sm"
                  >
                    {reportLoading ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <>€0.99 — Get Report</>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </main>
  );
}
