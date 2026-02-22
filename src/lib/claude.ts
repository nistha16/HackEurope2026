import Anthropic from "@anthropic-ai/sdk";
import type { ComparisonResult } from "@/types";

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

export async function explainComparison(
  results: ComparisonResult[],
  amount: number,
  sourceCurrency: string,
  targetCurrency: string
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

    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: `You are a financial advisor helping someone send ${amount} ${sourceCurrency} to ${targetCurrency}. Here are the comparison results from different money transfer providers, ranked by total real cost (cheapest first):

${comparisonSummary}

Please explain in plain, friendly language:
1. Which provider is the best option and why
2. How much money they could save compared to the worst option
3. Any hidden fees or markups users should be aware of
4. A brief recommendation based on their needs (cheapest vs fastest vs most transparent)

Keep your response concise and easy to understand. Avoid jargon. Use specific numbers from the data.`,
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
