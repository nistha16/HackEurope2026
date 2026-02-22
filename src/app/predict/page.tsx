"use client";

import * as React from "react";
import Link from "next/link";
import { CurrencySelector } from "@/components/currencySelector";
import { Navbar } from "@/components/Navbar";
import { RatePredictionChart } from "@/components/RatePredictionChart";
import { TimingScore } from "@/components/TimingScore";
import { Button } from "@/components/ui/button";
import { CURRENCIES, type PredictionResponse } from "@/types";
import { ArrowRight, ArrowLeftRight, Loader2 } from "lucide-react";

/* ─── Main page ─── */

export default function PredictPage() {
  const [source, setSource] = React.useState("EUR");
  const [target, setTarget] = React.useState("MAD");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<PredictionResponse | null>(null);

  async function handlePredict() {
    if (source === target) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_currency: source,
          target_currency: target,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || `Request failed (${res.status})`);
      }
      setData(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-zinc-50">
      <Navbar />

      <div className="max-w-3xl mx-auto px-4 py-10 sm:py-14 space-y-8">
        {/* Header */}
        <div className="text-center space-y-1">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900">
            Send Now or Wait?
          </h1>
          <p className="text-muted-foreground text-sm sm:text-base">
            ML-powered timing prediction based on 25 years of ECB data.
          </p>
        </div>

        {/* Currency picker */}
        <div className="rounded-2xl border bg-white p-5 sm:p-6 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] gap-3 items-end">
            <CurrencySelector
              label="From"
              value={source}
              onValueChange={setSource}
              currencies={CURRENCIES}
            />
            <div className="hidden sm:flex items-center justify-center pt-6">
              <ArrowRight className="h-5 w-5 text-zinc-400" />
            </div>
            <CurrencySelector
              label="To"
              value={target}
              onValueChange={setTarget}
              currencies={CURRENCIES}
            />
          </div>

          <Button
            onClick={handlePredict}
            disabled={loading || source === target}
            className="w-full h-12 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analysing rates...
              </>
            ) : (
              "Predict"
            )}
          </Button>
        </div>

        {/* Error */}
        {error && (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Results */}
        {data && !loading && (
          <div className="space-y-6">
            {/* Timing Score card (circular gauge + recommendation + market insights) */}
            <TimingScore
              timingScore={data.timing_score}
              recommendation={data.recommendation}
              reasoning={data.reasoning}
              currentRate={data.current_rate}
              marketInsights={data.market_insights}
              sourceCurrency={source}
              targetCurrency={target}
            />

            {/* Historical rate chart (solid line + today marker + 2-month band) */}
            <RatePredictionChart
              historicalRates={data.historical_rates}
              currentRate={data.current_rate}
              marketInsights={data.market_insights}
              sourceCurrency={source}
              targetCurrency={target}
            />

            {/* Link to compare */}
            <div className="text-center pt-2">
              <Link href="/compare">
                <Button variant="outline" className="rounded-2xl gap-2">
                  <ArrowLeftRight className="h-4 w-4" />
                  Compare providers for {source} → {target}
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
