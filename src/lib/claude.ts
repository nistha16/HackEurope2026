import Anthropic from "@anthropic-ai/sdk";
import type { ComparisonResult, MarketInsights } from "@/types";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

export interface TimingData {
  timing_score: number;
  recommendation: "SEND_NOW" | "WAIT" | "NEUTRAL";
  market_insights: MarketInsights;
}

export async function explainComparison(
  results: ComparisonResult[],
  amount: number,
  sourceCurrency: string,
  targetCurrency: string,
  timingData?: TimingData
): Promise<string> {
  try {
    const comparisonSummary = results
      .map((r, i) => {
        return [
          `${i + 1}. ${r.provider.name}:`,
          `   - Flat fee: ${r.flat_fee.toFixed(2)} ${sourceCurrency}`,
          `   - Percent fee: ${r.percent_fee.toFixed(2)} ${sourceCurrency}`,
          `   - FX markup cost: ${r.fx_markup_cost.toFixed(2)} ${sourceCurrency}`,
          `   - Total fee: ${r.total_fee.toFixed(2)} ${sourceCurrency}`,
          `   - Provider rate: ${r.provider_rate.toFixed(4)} (mid-market: ${r.exchange_rate.toFixed(4)})`,
          `   - Recipient gets: ${r.recipient_gets.toFixed(2)} ${targetCurrency}`,
          `   - Hidden cost: ${r.hidden_cost.toFixed(2)} ${targetCurrency}`,
          `   - Total real cost: ${r.total_real_cost.toFixed(2)} ${sourceCurrency}`,
          `   - Transparency score: ${r.transparency_score}`,
        ].join("\n");
      })
      .join("\n\n");

    let timingSection = "";
    if (timingData) {
      const mi = timingData.market_insights;
      timingSection = `

MARKET TIMING DATA:
- Timing score: ${timingData.timing_score} (0 = worst timing, 1 = best timing over past 2 months)
- ML recommendation: ${timingData.recommendation}
- 2-month rate range: ${mi.two_month_low.toFixed(4)} – ${mi.two_month_high.toFixed(4)} (avg: ${mi.two_month_avg.toFixed(4)})
- 1-year trend: ${mi.one_year_trend}
- Volatility: ${mi.volatility}`;
    }

    const prompt = `You are a financial advisor helping someone send ${amount} ${sourceCurrency} to ${targetCurrency}. Analyze the following data and give personalized advice.

PROVIDER COMPARISON (ranked by total real cost, cheapest first):

${comparisonSummary}${timingSection}

Perform the following multi-step analysis:

STEP 1 — FEE ANALYSIS:
a. Identify the cheapest option and explain WHY it's cheapest (low flat fee? no FX markup?)
b. Expose any hidden fees — if a provider advertises low fees but hides costs in the exchange rate markup, call it out explicitly with the exact amounts (e.g. "Western Union advertises €4.90 but hides €17.50 in a worse exchange rate")
c. Calculate the exact savings between the best and worst provider
d. Note any transparency score concerns (D or F ratings)

${timingData ? `STEP 2 — MARKET TIMING:
a. Interpret the timing score: what percentile is today's rate in? Is this a good day?
b. Factor in the trend direction and volatility
c. Give a clear send-now-or-wait recommendation with reasoning

STEP 3 — UNIFIED ADVICE:
Synthesize the fee analysis and market timing into one concise recommendation. For example: "Wise is the cheapest at €3.50 total cost AND today's rate is in the top 15% — this is a great moment to send." Or: "Wise saves you €18 vs Western Union, but the rate is below average — consider waiting 1-2 days for a better window."` : `STEP 2 — RECOMMENDATION:
Give a concise recommendation considering cost, speed, and transparency.`}

RULES:
- Use plain, friendly language. No jargon.
- Use specific numbers from the data — never say "significant" without a number.
- Keep the total response under 200 words.
- Do NOT use bullet points or numbered lists — write in short paragraphs.
- Address the user directly ("you", "your").`;

    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: prompt,
        },
      ],
    });

    const textBlock = message.content.find((block) => block.type === "text");
    if (!textBlock || textBlock.type !== "text") {
      throw new Error("No text response received from Claude");
    }

    return textBlock.text;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Claude API error: ${error.message}`);
    }
    throw new Error("Claude API error: Unknown error");
  }
}
