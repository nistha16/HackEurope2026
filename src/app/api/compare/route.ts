import { NextRequest, NextResponse } from "next/server";
import { getLatestRate, SUPPORTED_CURRENCIES } from "@/lib/frankfurter";
import { compareProviders } from "@/lib/providers";
import type { ComparisonResponse } from "@/types";

// Fallback mid-market rates for currencies the ECB doesn't track.
// Sources: xe.com indicative rates, Feb 2026. Used when Frankfurter is
// unavailable (non-ECB currency or API down). Updated periodically.
const FALLBACK_RATES: Record<string, number> = {
  "EUR-MAD": 10.85,
  "EUR-NGN": 1750.0,
  "EUR-BDT": 128.5,
  "EUR-EGP": 52.75,
  "EUR-KES": 165.0,
  "GBP-INR": 105.8,
  "GBP-PKR": 380.0,
  "GBP-GHS": 17.5,
  "USD-PHP": 56.2,
  "USD-MXN": 17.25,
  "USD-BRL": 5.48,
};

async function getMidMarketRate(
  source: string,
  target: string
): Promise<{ rate: number; source: "frankfurter" | "fallback" }> {
  // Try live ECB rate first
  if (SUPPORTED_CURRENCIES.has(source) && SUPPORTED_CURRENCIES.has(target)) {
    try {
      const { rate } = await getLatestRate(source, target);
      return { rate, source: "frankfurter" };
    } catch {
      // Frankfurter API down — fall through to fallback
    }
  }

  // Fallback for non-ECB currencies or API failure
  const corridor = `${source}-${target}`;
  const fallbackRate = FALLBACK_RATES[corridor];
  if (fallbackRate) {
    return { rate: fallbackRate, source: "fallback" };
  }

  // Try reverse corridor
  const reverseRate = FALLBACK_RATES[`${target}-${source}`];
  if (reverseRate) {
    return { rate: 1 / reverseRate, source: "fallback" };
  }

  throw new Error(
    `No exchange rate available for ${source}→${target}. ` +
      `This currency pair is not supported by the ECB and has no fallback rate.`
  );
}

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

    // --- Step 1: Get mid-market rate ---
    const { rate: midMarketRate } = await getMidMarketRate(src, tgt);

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
