import { NextRequest, NextResponse } from "next/server";
import { explainComparison } from "@/lib/claude";
import type { ComparisonResult, MarketInsights } from "@/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      results,
      amount,
      source_currency,
      target_currency,
      timing_score,
      recommendation,
      market_insights,
    } = body as {
      results: ComparisonResult[];
      amount: number;
      source_currency: string;
      target_currency: string;
      timing_score?: number;
      recommendation?: "SEND_NOW" | "WAIT" | "NEUTRAL";
      market_insights?: MarketInsights;
    };

    if (!results || !Array.isArray(results) || results.length === 0) {
      return NextResponse.json(
        { error: "results array is required and must not be empty" },
        { status: 400 }
      );
    }

    if (!amount || !source_currency || !target_currency) {
      return NextResponse.json(
        { error: "amount, source_currency, and target_currency are required" },
        { status: 400 }
      );
    }

    // Build optional timing data if all fields are present
    const timingData =
      typeof timing_score === "number" && recommendation && market_insights
        ? { timing_score, recommendation, market_insights }
        : undefined;

    const explanation = await explainComparison(
      results,
      amount,
      source_currency,
      target_currency,
      timingData
    );

    return NextResponse.json({ explanation });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Explanation failed: ${message}` },
      { status: 500 }
    );
  }
}
