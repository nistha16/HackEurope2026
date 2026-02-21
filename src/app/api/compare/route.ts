import { NextRequest, NextResponse } from "next/server";
import { getLatestRate } from "@/lib/frankfurter";
import { compareProviders } from "@/lib/providers";
import type { ComparisonResponse } from "@/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { source_currency, target_currency, amount } = body;

    // --- Validation ---
    if (!source_currency || !target_currency || !amount) {
      return NextResponse.json(
        { error: "Missing required fields: source_currency, target_currency, amount" },
        { status: 400 }
      );
    }

    const src = String(source_currency).toUpperCase();
    const tgt = String(target_currency).toUpperCase();
    const numAmount = Number(amount);

    if (isNaN(numAmount) || numAmount <= 0) {
      return NextResponse.json(
        { error: "amount must be a positive number" },
        { status: 400 }
      );
    }

    if (src === tgt) {
      return NextResponse.json(
        { error: "Source and target currencies must be different." },
        { status: 400 }
      );
    }

    // --- Step 1: Get mid-market rate (Frankfurter → Open ER fallback) ---
    const { rate: midMarketRate } = await getLatestRate(src, tgt);

    // --- Step 2: Run comparison engine ---
    const results = compareProviders(numAmount, src, tgt, midMarketRate);

    if (results.length === 0) {
      return NextResponse.json(
        { error: `No providers available for ${src}→${tgt} at amount ${numAmount}. Check corridor support and amount limits.` },
        { status: 404 }
      );
    }

    // --- Step 3: Calculate savings ---
    const cheapest = results[0];
    const mostExpensive = results[results.length - 1];
    const potentialSavings =
      Math.round((mostExpensive.total_real_cost - cheapest.total_real_cost) * 100) / 100;

    // --- Step 4: Build response ---
    const response: ComparisonResponse = {
      results,
      mid_market_rate: midMarketRate,
      source_currency: src,
      target_currency: tgt,
      amount: numAmount,
      best_provider: cheapest.provider.name,
      potential_savings: potentialSavings,
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(response, {
      headers: {
        "Cache-Control": "public, max-age=300, s-maxage=300",
      },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to compare providers";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
