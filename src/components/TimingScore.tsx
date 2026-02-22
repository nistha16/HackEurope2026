"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import type { MarketInsights } from "@/types";
import { TrendingUp, TrendingDown, Activity } from "lucide-react";

type Recommendation = "SEND_NOW" | "WAIT" | "NEUTRAL";

type Props = {
  timingScore: number;
  recommendation: Recommendation;
  reasoning: string;
  currentRate: number;
  marketInsights: MarketInsights;
  sourceCurrency: string;
  targetCurrency: string;
};

const SCORE_COLORS = {
  green: { ring: "text-emerald-500", bg: "bg-emerald-50", track: "text-emerald-100" },
  amber: { ring: "text-amber-500", bg: "bg-amber-50", track: "text-amber-100" },
  red: { ring: "text-red-500", bg: "bg-red-50", track: "text-red-100" },
} as const;

function getScoreColor(score: number) {
  if (score >= 0.8) return SCORE_COLORS.green;
  if (score >= 0.5) return SCORE_COLORS.amber;
  return SCORE_COLORS.red;
}

const RECOMMENDATION_STYLES: Record<
  Recommendation,
  { label: string; className: string }
> = {
  SEND_NOW: {
    label: "Send Now",
    className: "bg-emerald-100 text-emerald-800 border-emerald-200",
  },
  NEUTRAL: {
    label: "Neutral",
    className: "bg-amber-100 text-amber-800 border-amber-200",
  },
  WAIT: {
    label: "Wait",
    className: "bg-red-100 text-red-800 border-red-200",
  },
};

function CircularScore({ score }: { score: number }) {
  const color = getScoreColor(score);
  const percent = score * 100;
  // SVG circle math: r=45, circumference = 282.74
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" viewBox="0 0 100 100">
        {/* Track */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          className={cn("stroke-current", color.track)}
        />
        {/* Progress arc */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          className={cn("stroke-current transition-all duration-700", color.ring)}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 50 50)"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={cn("text-3xl font-bold", color.ring)}>
          {score.toFixed(2)}
        </span>
        <span className="text-xs text-muted-foreground">/ 1.00</span>
      </div>
    </div>
  );
}

const VOLATILITY_LABELS: Record<string, { label: string; icon: typeof Activity }> = {
  HIGH: { label: "High volatility", icon: Activity },
  MEDIUM: { label: "Moderate volatility", icon: Activity },
  LOW: { label: "Low volatility", icon: Activity },
};

export function TimingScore({
  timingScore,
  recommendation,
  reasoning,
  currentRate,
  marketInsights,
  sourceCurrency,
  targetCurrency,
}: Props) {
  const recStyle = RECOMMENDATION_STYLES[recommendation];
  const percentLabel = Math.round(timingScore * 100);
  const TrendIcon =
    marketInsights.one_year_trend === "UP" ? TrendingUp : TrendingDown;
  const volInfo = VOLATILITY_LABELS[marketInsights.volatility] ?? VOLATILITY_LABELS.LOW;

  return (
    <div className="rounded-2xl border bg-white p-4 sm:p-6 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Market Timing Score</h3>
        <span
          className={cn(
            "inline-flex items-center rounded-full border px-3 py-0.5 text-xs font-semibold",
            recStyle.className
          )}
        >
          {recStyle.label}
        </span>
      </div>

      {/* Score ring + label */}
      <div className="flex flex-col items-center gap-2">
        <CircularScore score={timingScore} />
        <p className="text-sm text-center text-muted-foreground max-w-xs">
          Today is better than <span className="font-semibold text-gray-800">{percentLabel}%</span>{" "}
          of days in the past 2 months
        </p>
      </div>

      {/* Reasoning */}
      <p className="text-sm text-gray-600 leading-relaxed">{reasoning}</p>

      {/* Market insights */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Market Insights
        </h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="rounded-xl bg-zinc-50 px-3 py-2">
            <p className="text-xs text-muted-foreground">2-Month High</p>
            <p className="font-semibold">
              {marketInsights.two_month_high.toFixed(4)}{" "}
              <span className="text-xs text-muted-foreground">{targetCurrency}</span>
            </p>
          </div>
          <div className="rounded-xl bg-zinc-50 px-3 py-2">
            <p className="text-xs text-muted-foreground">2-Month Low</p>
            <p className="font-semibold">
              {marketInsights.two_month_low.toFixed(4)}{" "}
              <span className="text-xs text-muted-foreground">{targetCurrency}</span>
            </p>
          </div>
          <div className="rounded-xl bg-zinc-50 px-3 py-2">
            <p className="text-xs text-muted-foreground">2-Month Avg</p>
            <p className="font-semibold">
              {marketInsights.two_month_avg.toFixed(4)}{" "}
              <span className="text-xs text-muted-foreground">{targetCurrency}</span>
            </p>
          </div>
          <div className="rounded-xl bg-zinc-50 px-3 py-2">
            <p className="text-xs text-muted-foreground">Current Rate</p>
            <p className="font-semibold">
              {currentRate.toFixed(4)}{" "}
              <span className="text-xs text-muted-foreground">{targetCurrency}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 pt-1 text-sm text-gray-600">
          <span className="inline-flex items-center gap-1">
            <TrendIcon className="h-4 w-4" />
            1-year trend: {marketInsights.one_year_trend === "UP" ? "Upward" : "Downward"}
          </span>
          <span className="inline-flex items-center gap-1">
            <volInfo.icon className="h-4 w-4" />
            {volInfo.label}
          </span>
        </div>
      </div>
    </div>
  );
}
