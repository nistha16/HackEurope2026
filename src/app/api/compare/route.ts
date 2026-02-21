import { NextRequest, NextResponse } from "next/server";
import { getLatestRate } from "@/lib/frankfurter";
import { compareProviders } from "@/lib/providers";
import type { ComparisonResponse } from "@/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { source_currency, target_currency, amount } = body;

    if (!source_currency || !target_currency || !amount) {
      return NextResponse.json(
        {
          error:
            "Missing required fields: source_currency, target_currency, amount",
        },
        { status: 400 }
      );
    }

    if (typeof amount !== "number" || amount <= 0) {
      return NextResponse.json(
        { error: "amount must be a positive number" },
        { status: 400 }
      );
    }

    // 1. Fetch mid-market rate
    const { rate: midMarketRate } = await getLatestRate(
      source_currency.toUpperCase(),
      target_currency.toUpperCase()
    );

    // 2. Compare providers (already sorted by total_real_cost ascending)
    const results = compareProviders(
      amount,
      source_currency.toUpperCase(),
      target_currency.toUpperCase(),
      midMarketRate
    );

    if (results.length === 0) {
      return NextResponse.json(
        {
          error:
            "No providers available for this corridor or amount range",
        },
        { status: 404 }
      );
    }

    // 3. Calculate potential savings (difference between most and least expensive)
    const cheapest = results[0];
    const mostExpensive = results[results.length - 1];
    const potentialSavings =
      mostExpensive.total_real_cost - cheapest.total_real_cost;

    const response: ComparisonResponse = {
      results,
      mid_market_rate: midMarketRate,
      source_currency: source_currency.toUpperCase(),
      target_currency: target_currency.toUpperCase(),
      amount,
      best_provider: cheapest.provider.name,
      potential_savings: Math.round(potentialSavings * 100) / 100,
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(response);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to compare providers";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
