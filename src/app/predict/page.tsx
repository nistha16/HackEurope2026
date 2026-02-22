"use client";

import * as React from "react";
import { CurrencySelector } from "@/components/currencySelector";
import { Navbar } from "@/components/Navbar";
import { Button } from "@/components/ui/button";
import { CURRENCIES, type PredictionResponse } from "@/types";
import {
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Minus,
  Clock,
  Activity,
  Loader2,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from "recharts";

/* ─── Recommendation badge ─── */

function RecommendationBadge({
  rec,
}: {
  rec: "SEND_NOW" | "WAIT" | "NEUTRAL";
}) {
  const config = {
    SEND_NOW: {
      label: "Send Now",
      icon: TrendingUp,
      bg: "bg-emerald-50 border-emerald-200",
      text: "text-emerald-700",
    },
    WAIT: {
      label: "Wait",
      icon: Clock,
      bg: "bg-amber-50 border-amber-200",
      text: "text-amber-700",
    },
    NEUTRAL: {
      label: "Neutral",
      icon: Minus,
      bg: "bg-zinc-100 border-zinc-200",
      text: "text-zinc-600",
    },
  }[rec];

  const Icon = config.icon;

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold ${config.bg} ${config.text}`}
    >
      <Icon className="h-4 w-4" />
      {config.label}
    </div>
  );
}

/* ─── Timing Score Bar ─── */

function TimingBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 65 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-400" : "bg-red-400";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-zinc-500">Timing score</span>
        <span className="font-semibold text-zinc-900">{pct}/100</span>
      </div>
      <div className="h-2 rounded-full bg-zinc-100 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-zinc-400">
        Higher = better time to send (percentile vs. last 60 days)
      </p>
    </div>
  );
}

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

  // Format chart data — show only every Nth label to avoid crowding
  const chartData = React.useMemo(() => {
    if (!data?.historical_rates) return [];
    return data.historical_rates.map((r) => ({
      date: r.date,
      rate: r.rate,
      label: new Date(r.date).toLocaleDateString("en-GB", {
        month: "short",
        day: "numeric",
      }),
    }));
  }, [data]);

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
            {/* Recommendation card */}
            <div className="rounded-2xl border bg-white p-5 sm:p-6 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <p className="text-sm text-zinc-500">
                    1 {source} ={" "}
                    <span className="text-lg font-bold text-zinc-900">
                      {data.current_rate.toFixed(4)} {target}
                    </span>
                  </p>
                </div>
                <RecommendationBadge rec={data.recommendation} />
              </div>

              <p className="text-sm text-zinc-600 leading-relaxed">
                {data.reasoning}
              </p>

              <TimingBar score={data.timing_score} />
            </div>

            {/* Market insights */}
            <div className="rounded-2xl border bg-white p-5 sm:p-6">
              <h3 className="font-semibold text-zinc-900 mb-4 flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-600" />
                Market Insights
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                <div>
                  <p className="text-xs text-zinc-400">60-Day High</p>
                  <p className="font-semibold text-zinc-900">
                    {data.market_insights.two_month_high.toFixed(4)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400">60-Day Low</p>
                  <p className="font-semibold text-zinc-900">
                    {data.market_insights.two_month_low.toFixed(4)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400">60-Day Avg</p>
                  <p className="font-semibold text-zinc-900">
                    {data.market_insights.two_month_avg.toFixed(4)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-zinc-400">1-Year Trend</p>
                  <p className="font-semibold flex items-center justify-center gap-1">
                    {data.market_insights.one_year_trend === "UP" ? (
                      <>
                        <TrendingUp className="h-4 w-4 text-emerald-500" />
                        <span className="text-emerald-600">Up</span>
                      </>
                    ) : (
                      <>
                        <TrendingDown className="h-4 w-4 text-red-500" />
                        <span className="text-red-600">Down</span>
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Rate chart */}
            {chartData.length > 0 && (
              <div className="rounded-2xl border bg-white p-5 sm:p-6">
                <h3 className="font-semibold text-zinc-900 mb-4">
                  {source}/{target} — 1 Year
                </h3>
                <div className="h-64 sm:h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient
                          id="rateGradient"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="0%"
                            stopColor="#059669"
                            stopOpacity={0.2}
                          />
                          <stop
                            offset="95%"
                            stopColor="#059669"
                            stopOpacity={0}
                          />
                        </linearGradient>
                      </defs>
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#e4e4e7"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="label"
                        tick={{ fontSize: 11, fill: "#a1a1aa" }}
                        tickLine={false}
                        axisLine={false}
                        interval={Math.floor(chartData.length / 6)}
                      />
                      <YAxis
                        domain={["auto", "auto"]}
                        tick={{ fontSize: 11, fill: "#a1a1aa" }}
                        tickLine={false}
                        axisLine={false}
                        width={55}
                        tickFormatter={(v: number) => v.toFixed(2)}
                      />
                      <Tooltip
                        contentStyle={{
                          borderRadius: "12px",
                          border: "1px solid #e4e4e7",
                          fontSize: "13px",
                        }}
                        formatter={(value) => [
                          Number(value).toFixed(4),
                          "Rate",
                        ]}
                        labelFormatter={(label) => String(label)}
                      />
                      <ReferenceLine
                        y={data.current_rate}
                        stroke="#059669"
                        strokeDasharray="4 4"
                        label={{
                          value: "Current",
                          position: "right",
                          fill: "#059669",
                          fontSize: 11,
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="rate"
                        stroke="#059669"
                        strokeWidth={2}
                        fill="url(#rateGradient)"
                        dot={false}
                        activeDot={{ r: 4, fill: "#059669" }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}
