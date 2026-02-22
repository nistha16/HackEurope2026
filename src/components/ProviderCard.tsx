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
};

function ProviderLogo({ name, websiteUrl }: { name: string; websiteUrl: string }) {
  const domain = new URL(websiteUrl).hostname.replace("www.", "");
  const src = `https://www.google.com/s2/favicons?sz=64&domain=${domain}`;
  const [failed, setFailed] = React.useState(false);

  if (failed) {
    return (
      <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 shrink-0">
        {name.charAt(0)}
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={name}
      className="h-8 w-8 rounded-full object-contain shrink-0 bg-white border border-gray-100 p-0.5"
      onError={() => setFailed(true)}
    />
  );
}

function FeeRow({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={cn("flex justify-between", className)}>
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}

export function ProviderCard({
  result,
  sourceCurrency,
  targetCurrency,
  isBestValue,
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
      {/* Best Value badge */}
      {isBestValue && (
        <div className="flex gap-2 mb-3">
          <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
            Best Value
          </span>
        </div>
      )}

      {/* Main row */}
      <div className="flex items-center justify-between gap-4">
        {/* Provider info */}
        <div className="flex items-center gap-3 min-w-0">
          <ProviderLogo name={provider.name} websiteUrl={provider.website_url} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <p className="font-semibold text-gray-900 truncate">{provider.name}</p>
              <TransparencyScore score={result.transparency_score} />
            </div>
          </div>
        </div>

        {/* Recipient gets */}
        <div className="text-right shrink-0">
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
      <HiddenFeeAlert
        hiddenCost={result.hidden_cost}
        markupPercent={provider.fx_markup_percent}
        currency={sourceCurrency}
        className="mt-3"
      />

      {/* Fee breakdown */}
      <div className="mt-3 border-t pt-3">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-gray-700 transition-colors"
          aria-expanded={expanded}
        >
          {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          Fee breakdown
        </button>

        {expanded && (
          <div className="mt-2 space-y-1 text-xs text-gray-600">
            <FeeRow
              label="Flat fee"
              value={`${sourceCurrency} ${result.flat_fee.toFixed(2)}`}
            />
            <FeeRow
              label={`Percent fee (${provider.fee_percent}%)`}
              value={`${sourceCurrency} ${result.percent_fee.toFixed(2)}`}
            />
            <FeeRow
              label={`Hidden FX markup (${provider.fx_markup_percent}% worse than mid-market)`}
              value={`${sourceCurrency} ${result.fx_markup_cost.toFixed(2)}`}
              className={result.hidden_cost > 0 ? "text-orange-600 font-medium" : undefined}
            />
            <FeeRow
              label="Total real cost"
              value={`${sourceCurrency} ${result.total_real_cost.toFixed(2)}`}
              className="border-t pt-1 mt-1 font-semibold text-gray-800"
            />
          </div>
        )}
      </div>

      {/* CTA */}
      <div className="mt-3">
        <Button
          asChild
          variant={isBestValue ? "default" : "outline"}
          className="w-full rounded-xl"
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
