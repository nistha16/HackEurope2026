"use client";

import * as React from "react";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { TransparencyScore } from "@/components/TransparencyScore";
import { HiddenFeeAlert } from "@/components/HiddenFeeAlert";
import { cn } from "@/lib/utils";
import type { ComparisonResult } from "@/types";

type Props = {
  result: ComparisonResult;
  sourceCurrency: string;
  targetCurrency: string;
  isBestValue?: boolean;
  isFastest?: boolean;
};

function formatSpeed(hours: number): string {
  if (hours === 0) return "⚡ Instant";
  if (hours < 1) return "⚡ Instant";
  if (hours <= 2) return `⚡ ${hours}h`;
  if (hours <= 24) return `🕐 ${hours}h`;
  const days = Math.round(hours / 24);
  return `🐢 ${days} day${days > 1 ? "s" : ""}`;
}

export function ProviderCard({
  result,
  sourceCurrency,
  targetCurrency,
  isBestValue,
  isFastest,
}: Props) {
  const [expanded, setExpanded] = React.useState(false);
  const { provider } = result;

  return (
    <div
      className={cn(
        "rounded-2xl border bg-white p-4 sm:p-5 shadow-sm transition-shadow hover:shadow-md",
        isBestValue && "border-green-400 ring-1 ring-green-400"
      )}
    >
      {/* Badges */}
      {(isBestValue || isFastest) && (
        <div className="flex gap-2 mb-3">
          {isBestValue && (
            <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
              Best Value
            </span>
          )}
          {isFastest && (
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">
              Fastest
            </span>
          )}
        </div>
      )}

      {/* Main row */}
      <div className="flex items-center justify-between gap-4">
        {/* Provider info */}
        <div className="flex items-center gap-3 min-w-0">
          {provider.logo_url ? (
            <img
              src={provider.logo_url}
              alt={provider.name}
              className="h-8 w-8 rounded-full object-contain flex-shrink-0"
            />
          ) : (
            <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 flex-shrink-0">
              {provider.name.charAt(0)}
            </div>
          )}
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-semibold text-gray-900 truncate">
                {provider.name}
              </p>
              <TransparencyScore score={result.transparency_score} />
            </div>
            <p className="text-xs text-muted-foreground">
              {formatSpeed(provider.speed_hours)}
            </p>
          </div>
        </div>

        {/* Recipient gets */}
        <div className="text-right flex-shrink-0">
          <p className="text-2xl font-bold text-gray-900">
            {result.recipient_gets.toFixed(2)}
          </p>
          <p className="text-xs text-muted-foreground">{targetCurrency} received</p>
        </div>
      </div>

      {/* Fee summary */}
      <div className="mt-3 flex items-center justify-between text-sm text-muted-foreground">
        <span>
          Total fee:{" "}
          <span className="font-medium text-gray-800">
            {sourceCurrency} {result.total_real_cost.toFixed(2)}
          </span>
        </span>
        <span>Rate: {result.provider_rate.toFixed(4)}</span>
      </div>

      {/* Hidden fee alert */}
      {result.hidden_cost > 0 && (
        <HiddenFeeAlert
          hiddenCost={result.hidden_cost}
          markupPercent={provider.fx_markup_percent}
          currency={sourceCurrency}
          className="mt-3"
        />
      )}

      {/* Fee breakdown toggle */}
      <div className="mt-3 border-t pt-3">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-gray-700 transition-colors"
        >
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
          Fee breakdown
        </button>

        {expanded && (
          <div className="mt-2 space-y-1 text-xs text-gray-600">
            <div className="flex justify-between">
              <span>Flat fee</span>
              <span>
                {sourceCurrency} {result.flat_fee.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between">
              <span>
                Percent fee ({provider.fee_percent}%)
              </span>
              <span>
                {sourceCurrency} {result.percent_fee.toFixed(2)}
              </span>
            </div>
            <div
              className={cn(
                "flex justify-between",
                result.hidden_cost > 0 && "text-orange-600 font-medium"
              )}
            >
              <span>
                Hidden FX markup ({provider.fx_markup_percent}% worse than mid-market)
              </span>
              <span>
                {sourceCurrency} {result.fx_markup_cost.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between font-semibold text-gray-800 border-t pt-1 mt-1">
              <span>Total real cost</span>
              <span>
                {sourceCurrency} {result.total_real_cost.toFixed(2)}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="mt-3">
        <Button
          asChild
          className="w-full rounded-xl"
          variant={isBestValue ? "default" : "outline"}
        >
          <a
            href={provider.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2"
          >
            Send with {provider.name}
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </Button>
      </div>
    </div>
  );
}
