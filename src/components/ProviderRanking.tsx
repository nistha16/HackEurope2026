import * as React from "react";
import { ProviderCard } from "@/components/ProviderCard";
import type { ComparisonResult } from "@/types";

type Props = {
  results: ComparisonResult[];
  sourceCurrency: string;
  targetCurrency: string;
  potentialSavings: number;
};

export function ProviderRanking({ results, sourceCurrency, targetCurrency, potentialSavings }: Props) {
  if (results.length === 0) return null;

  const best = results[0];
  const worst = results[results.length - 1];

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {/* Savings banner */}
      {potentialSavings > 0 && (
        <div className="rounded-2xl bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-800">
          <span className="font-semibold">
            Switch to {best.provider.name} and save {sourceCurrency} {potentialSavings.toFixed(2)}
          </span>{" "}
          vs {worst.provider.name}
        </div>
      )}

      {/* Provider cards */}
      <div className="space-y-3">
        {results.map((result, index) => (
          <ProviderCard
            key={result.provider.id}
            result={result}
            sourceCurrency={sourceCurrency}
            targetCurrency={targetCurrency}
            isBestValue={index === 0}
          />
        ))}
      </div>
    </div>
  );
}
