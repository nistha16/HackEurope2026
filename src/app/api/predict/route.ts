import { NextRequest, NextResponse } from "next/server";
import {
  getHistoricalRates,
  getLatestRate,
  SUPPORTED_CURRENCIES,
} from "@/lib/frankfurter";
import type { PredictionResponse, MarketInsights } from "@/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { source_currency, target_currency } = body;

    if (!source_currency || !target_currency) {
      return NextResponse.json(
        { error: "source_currency and target_currency are required" },
        { status: 400 }
      );
    }

    if (source_currency === target_currency) {
      return NextResponse.json(
        { error: "Source and target currencies must be different" },
        { status: 400 }
      );
    }

    // Fetch current rate (works for all currencies via Frankfurter + open.er fallback)
    const { rate: currentRate } = await getLatestRate(
      source_currency,
      target_currency
    );

    // Fetch 1 year of historical rates for charting (Frankfurter / ECB only)
    let historicalRates: { date: string; rate: number }[] = [];
    const bothSupported =
      SUPPORTED_CURRENCIES.has(source_currency) &&
      SUPPORTED_CURRENCIES.has(target_currency);

    if (bothSupported) {
      const endDate = new Date().toISOString().split("T")[0];
      const startDate = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];
      historicalRates = await getHistoricalRates(
        source_currency,
        target_currency,
        startDate,
        endDate
      );
    }

    // ── Try ML service first ──────────────────────────────────────────
    const mlServiceUrl =
      process.env.ML_SERVICE_URL || "http://localhost:8000";

    try {
      const mlResponse = await fetch(`${mlServiceUrl}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from_currency: source_currency,
          to_currency: target_currency,
        }),
        signal: AbortSignal.timeout(5000),
      });

      if (mlResponse.ok) {
        const mlData = await mlResponse.json();

        // Runtime validation: ensure ML response has required fields
        const validRecommendations = ["SEND_NOW", "WAIT", "NEUTRAL"] as const;
        if (
          typeof mlData.timing_score !== "number" ||
          !validRecommendations.includes(mlData.recommendation) ||
          typeof mlData.reasoning !== "string" ||
          !mlData.market_insights ||
          typeof mlData.market_insights.two_month_high !== "number" ||
          typeof mlData.market_insights.two_month_low !== "number" ||
          typeof mlData.market_insights.two_month_avg !== "number"
        ) {
          // Malformed ML response → fall through to fallback
          throw new Error("Invalid ML response shape");
        }

        const prediction: PredictionResponse = {
          current_rate: currentRate,
          timing_score: mlData.timing_score,
          recommendation: mlData.recommendation,
          reasoning: mlData.reasoning,
          market_insights: mlData.market_insights,
          historical_rates: historicalRates,
        };

        return NextResponse.json(prediction);
      }
      // ML returned non-OK → fall through to fallback
    } catch {
      // ML unavailable → fall through to fallback
    }

    // ── Fallback: simple percentile from Frankfurter history ──────────
    if (!bothSupported || historicalRates.length < 30) {
      return NextResponse.json(
        {
          error:
            "ML service unavailable and no historical data for this corridor. " +
            "Only ECB-supported currency pairs have a fallback.",
        },
        { status: 503 }
      );
    }

    const rates = historicalRates.map((r) => r.rate);
    const last60 = rates.slice(-60);

    // Percentile: where does today's rate sit in the last 60 days?
    const belowCount = last60.filter((r) => r <= currentRate).length;
    const timingScore = Math.round((belowCount / last60.length) * 100) / 100;

    // Recommendation
    let recommendation: "SEND_NOW" | "WAIT" | "NEUTRAL";
    let reasoning: string;

    if (timingScore > 0.8) {
      recommendation = "SEND_NOW";
      reasoning = `Good timing — today's rate is higher than ${Math.round(timingScore * 100)}% of days in the past 2 months. (Fallback: ML service unavailable)`;
    } else if (timingScore >= 0.5) {
      recommendation = "NEUTRAL";
      reasoning =
        "The rate is near its recent average — no strong signal either way. (Fallback: ML service unavailable)";
    } else {
      recommendation = "WAIT";
      reasoning = `Below-average rate (${Math.round(timingScore * 100)}th percentile over 2 months). Consider waiting for a better window. (Fallback: ML service unavailable)`;
    }

    // Market insights
    const twoMonthHigh = Math.max(...last60);
    const twoMonthLow = Math.min(...last60);
    const twoMonthAvg =
      last60.reduce((sum, r) => sum + r, 0) / last60.length;

    const yearAvg =
      rates.reduce((sum, r) => sum + r, 0) / rates.length;
    const oneYearTrend = currentRate > yearAvg ? "UP" : "DOWN";

    const std = Math.sqrt(
      last60.reduce((sum, r) => sum + (r - twoMonthAvg) ** 2, 0) /
        last60.length
    );
    const volRatio = std / twoMonthAvg;
    const volatility =
      volRatio > 0.015 ? "HIGH" : volRatio > 0.008 ? "MEDIUM" : "LOW";

    const marketInsights: MarketInsights = {
      two_month_high: Math.round(twoMonthHigh * 10000) / 10000,
      two_month_low: Math.round(twoMonthLow * 10000) / 10000,
      two_month_avg: Math.round(twoMonthAvg * 10000) / 10000,
      one_year_trend: oneYearTrend,
      volatility,
    };

    const prediction: PredictionResponse = {
      current_rate: currentRate,
      timing_score: timingScore,
      recommendation,
      reasoning,
      market_insights: marketInsights,
      historical_rates: historicalRates,
    };

    return NextResponse.json(prediction);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Prediction failed: ${message}` },
      { status: 500 }
    );
  }
}
