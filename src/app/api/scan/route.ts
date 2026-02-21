import { NextRequest, NextResponse } from "next/server";
import { scanReceipt } from "@/lib/gemini";
import { getLatestRate } from "@/lib/frankfurter";
import { compareProviders } from "@/lib/providers";
import type { ReceiptScanResult } from "@/types";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { image } = body as { image: string };

    if (!image) {
      return NextResponse.json(
        { error: "image (base64 string) is required" },
        { status: 400 }
      );
    }

    // Step 1: Scan the receipt using Gemini vision
    const receiptData = await scanReceipt(image);

    // Step 2: Get current mid-market rate for the extracted currencies
    let midMarketRate: number;
    try {
      const { rate } = await getLatestRate(
        receiptData.currency_sent,
        receiptData.currency_received
      );
      midMarketRate = rate;
    } catch {
      // If we can't fetch the rate, use the rate from the receipt as fallback
      midMarketRate = receiptData.rate_used;
    }

    // Step 3: Compare what the best provider would cost
    const comparisonResults = compareProviders(
      receiptData.amount_sent,
      receiptData.currency_sent,
      receiptData.currency_received,
      midMarketRate
    );

    // Step 4: Calculate overpay amount
    let overpayAmount = 0;
    let bestAlternativeCost = 0;
    let bestAlternativeProvider = "N/A";

    if (comparisonResults.length > 0) {
      const bestResult = comparisonResults[0]; // Already sorted by total_real_cost ascending
      bestAlternativeProvider = bestResult.provider.name;
      bestAlternativeCost = bestResult.total_real_cost;

      // The user's actual cost: fee they paid + hidden markup cost
      // Hidden markup cost = what mid-market would have given minus what the receipt rate gave
      const idealReceivedAmount =
        (receiptData.amount_sent - receiptData.fee_paid) * midMarketRate;
      const actualReceivedAmount = receiptData.amount_received;
      const hiddenMarkupCost =
        (idealReceivedAmount - actualReceivedAmount) / midMarketRate; // Convert back to source currency
      const userTotalCost = receiptData.fee_paid + Math.max(0, hiddenMarkupCost);

      overpayAmount = Math.max(
        0,
        Number((userTotalCost - bestAlternativeCost).toFixed(2))
      );
    }

    const result: ReceiptScanResult = {
      provider_name: receiptData.provider_name,
      amount_sent: receiptData.amount_sent,
      currency_sent: receiptData.currency_sent,
      amount_received: receiptData.amount_received,
      currency_received: receiptData.currency_received,
      fee_paid: receiptData.fee_paid,
      rate_used: receiptData.rate_used,
      date: receiptData.date,
      overpay_amount: overpayAmount,
      best_alternative_cost: bestAlternativeCost,
      best_alternative_provider: bestAlternativeProvider,
    };

    return NextResponse.json(result);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Receipt scan failed: ${message}` },
      { status: 500 }
    );
  }
}
