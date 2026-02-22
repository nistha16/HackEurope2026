"use client";

import * as React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
} from "recharts";
import type { MarketInsights } from "@/types";

type HistoricalRate = { date: string; rate: number };

type Props = {
  historicalRates: HistoricalRate[];
  currentRate: number;
  marketInsights: MarketInsights;
  sourceCurrency: string;
  targetCurrency: string;
};

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function formatDateFull(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) {
  if (!active || !payload?.length || !label) return null;
  return (
    <div className="rounded-xl border bg-white px-3 py-2 shadow-md text-sm">
      <p className="text-muted-foreground text-xs">{formatDateFull(label)}</p>
      <p className="font-semibold">{payload[0].value.toFixed(4)}</p>
    </div>
  );
}

export function RatePredictionChart({
  historicalRates,
  currentRate,
  marketInsights,
  sourceCurrency,
  targetCurrency,
}: Props) {
  if (!historicalRates.length) {
    return (
      <div className="rounded-2xl border bg-white p-6 text-center text-muted-foreground">
        No historical data available for this currency pair.
      </div>
    );
  }

  const todayStr = historicalRates[historicalRates.length - 1]?.date;

  // Find 2-month boundary for the shaded band
  const twoMonthsAgo = new Date();
  twoMonthsAgo.setMonth(twoMonthsAgo.getMonth() - 2);
  const twoMonthStr = twoMonthsAgo.toISOString().split("T")[0];
  const bandStart =
    historicalRates.find((r) => r.date >= twoMonthStr)?.date ?? todayStr;

  // Compute Y-axis domain with padding
  const allRates = historicalRates.map((r) => r.rate);
  const minRate = Math.min(...allRates);
  const maxRate = Math.max(...allRates);
  const padding = (maxRate - minRate) * 0.08;

  // Thin out tick labels for readability
  const tickCount = 6;
  const step = Math.max(1, Math.floor(historicalRates.length / tickCount));
  const ticks = historicalRates
    .filter((_, i) => i % step === 0)
    .map((r) => r.date);

  return (
    <div className="rounded-2xl border bg-white p-4 sm:p-6 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">
          {sourceCurrency}/{targetCurrency} — 1 Year
        </h3>
        <span className="text-sm text-muted-foreground">
          Today: <span className="font-semibold text-gray-900">{currentRate.toFixed(4)}</span>
        </span>
      </div>

      <div className="h-64 sm:h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={historicalRates}
            margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
          >
            {/* 2-month high/low shaded band */}
            <ReferenceArea
              x1={bandStart}
              x2={todayStr}
              y1={marketInsights.two_month_low}
              y2={marketInsights.two_month_high}
              fill="#10b981"
              fillOpacity={0.08}
              stroke="none"
            />

            <XAxis
              dataKey="date"
              tickFormatter={formatDate}
              ticks={ticks}
              tick={{ fontSize: 11, fill: "#888" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              domain={[minRate - padding, maxRate + padding]}
              tickFormatter={(v: number) => v.toFixed(2)}
              tick={{ fontSize: 11, fill: "#888" }}
              axisLine={false}
              tickLine={false}
              width={52}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Today marker */}
            <ReferenceLine
              x={todayStr}
              stroke="#6366f1"
              strokeDasharray="4 3"
              strokeWidth={1.5}
              label={{
                value: "Today",
                position: "top",
                fill: "#6366f1",
                fontSize: 11,
                fontWeight: 600,
              }}
            />

            <Line
              type="monotone"
              dataKey="rate"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: "#10b981", stroke: "#fff", strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-4 bg-emerald-500 rounded" />
          Historical rate
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded bg-emerald-500/10 border border-emerald-500/20" />
          2-month range
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-0.5 bg-indigo-500 rounded" />
          Today
        </span>
      </div>
    </div>
  );
}
