import { NextRequest, NextResponse } from "next/server";
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

    if (!results?.length || !amount || !source_currency || !target_currency) {
      return NextResponse.json(
        { error: "results, amount, source_currency, and target_currency are required" },
        { status: 400 }
      );
    }

    const best = results[0];
    const worst = results[results.length - 1];
    const savings = worst.total_real_cost - best.total_real_cost;

    const providerLines = results
      .map(
        (r, i) =>
          `${i + 1}. ${r.provider.name} — recipient gets ${r.recipient_gets.toFixed(2)} ${target_currency}, total cost ${r.total_real_cost.toFixed(2)} ${source_currency} (transparency: ${r.transparency_score})`
      )
      .join("\n");

    const hiddenMarkupProviders = results.filter(
      (r) => r.provider.fx_markup_percent > 1
    );
    const hiddenFeeSection =
      hiddenMarkupProviders.length > 0
        ? hiddenMarkupProviders
            .map(
              (r) =>
                `${r.provider.name} charges a ${r.provider.fx_markup_percent}% FX markup, costing you an extra ${r.fx_markup_cost.toFixed(2)} ${source_currency} in hidden fees.`
            )
            .join("\n")
        : "No providers in this comparison charge a significant hidden FX markup (>1%). Good news — you can compare rates confidently.";

    const analysis = `## Executive Summary
Sending ${amount} ${source_currency} to ${target_currency}, the best option is ${best.provider.name} — your recipient gets ${best.recipient_gets.toFixed(2)} ${target_currency}. By switching from the most expensive provider (${worst.provider.name}) you save ${savings.toFixed(2)} ${source_currency}.

## Provider Rankings
${providerLines}

## Best Choice: ${best.provider.name}
${best.provider.name} offers the best deal with a total cost of ${best.total_real_cost.toFixed(2)} ${source_currency}. The recipient receives ${best.recipient_gets.toFixed(2)} ${target_currency} — that's ${(best.recipient_gets - worst.recipient_gets).toFixed(2)} ${target_currency} more than the cheapest alternative. Transparency score: ${best.transparency_score}.

## Hidden Fee Warning
${hiddenFeeSection}

## When to Send
Exchange rates fluctuate daily — sending at the right moment can save as much as a provider switch. FibreTransfer Premium includes smart timing alerts that notify you when the rate hits your target, so you never miss a good window.

## Personalised Recommendation
Use ${best.provider.name} for this transfer. ${savings > 0 ? `You'll save ${savings.toFixed(2)} ${source_currency} compared to ${worst.provider.name}.` : ""} Check the timing score on the Compare page before sending to maximise what your recipient receives.`;

    return NextResponse.json({ analysis });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Report generation failed: ${message}` },
      { status: 500 }
    );
  }
}
