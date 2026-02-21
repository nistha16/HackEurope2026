import { NextRequest, NextResponse } from "next/server";
import { explainComparison } from "@/lib/claude";
import type { ComparisonResult } from "@/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { results, amount, source_currency, target_currency } = body as {
      results: ComparisonResult[];
      amount: number;
      source_currency: string;
      target_currency: string;
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

    const explanation = await explainComparison(
      results,
      amount,
      source_currency,
      target_currency
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
