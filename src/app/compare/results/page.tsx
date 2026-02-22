"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProviderRanking } from "@/components/ProviderRanking";
import type { ComparisonResponse } from "@/types";

export default function ResultsPage() {
  const router = useRouter();
  const [data, setData] = React.useState<ComparisonResponse | null>(null);

  React.useEffect(() => {
    const raw = localStorage.getItem("compareResult");
    if (!raw) {
      router.replace("/compare");
      return;
    }
    try {
      setData(JSON.parse(raw) as ComparisonResponse);
    } catch {
      router.replace("/compare");
    }
  }, [router]);

  if (!data) return null;

  return (
    <main className="min-h-screen bg-zinc-50 px-4 py-8">
      <div className="w-full max-w-2xl mx-auto space-y-6">
        {/* Back button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/compare")}
          className="gap-1.5 -ml-1"
        >
          <ArrowLeft className="h-4 w-4" />
          New comparison
        </Button>

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {data.source_currency} {data.amount.toLocaleString()} →{" "}
            {data.target_currency}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Mid-market rate:{" "}
            <span className="font-medium text-gray-700">
              {data.mid_market_rate.toFixed(4)}
            </span>
            <span className="ml-2 text-xs text-gray-400">
              (the real rate, no markup)
            </span>
          </p>
        </div>

        {/* Rankings */}
        <ProviderRanking
          results={data.results}
          sourceCurrency={data.source_currency}
          targetCurrency={data.target_currency}
          potentialSavings={data.potential_savings}
        />
      </div>
    </main>
  );
}
