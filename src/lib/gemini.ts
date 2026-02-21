import { GoogleGenerativeAI } from "@google/generative-ai";
import type { ReceiptScanResult } from "@/types";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");

export async function scanReceipt(
  imageBase64: string
): Promise<Omit<ReceiptScanResult, "overpay_amount" | "best_alternative_cost" | "best_alternative_provider">> {
  try {
    const model = genAI.getGenerativeModel({ model: "gemini-2.0-flash" });

    const prompt = `Analyze this money transfer receipt image and extract the following information. Return ONLY a valid JSON object with these exact fields:

{
  "provider_name": "string - the name of the transfer provider",
  "amount_sent": number - the amount that was sent,
  "currency_sent": "string - 3-letter currency code of the sent amount",
  "amount_received": number - the amount received by the recipient,
  "currency_received": "string - 3-letter currency code of the received amount",
  "fee_paid": number - the fee charged for the transfer,
  "rate_used": number - the exchange rate applied,
  "date": "string - the date of the transaction in YYYY-MM-DD format"
}

If any field cannot be determined from the receipt, use reasonable defaults:
- For missing strings, use "UNKNOWN"
- For missing numbers, use 0
- For missing dates, use today's date

Return ONLY the JSON object, no markdown formatting, no code blocks, no additional text.`;

    const result = await model.generateContent([
      prompt,
      {
        inlineData: {
          mimeType: "image/jpeg",
          data: imageBase64,
        },
      },
    ]);

    const response = result.response;
    const text = response.text();

    const cleanedText = text
      .replace(/```json\s*/g, "")
      .replace(/```\s*/g, "")
      .trim();

    const parsed = JSON.parse(cleanedText);

    return {
      provider_name: String(parsed.provider_name || "UNKNOWN"),
      amount_sent: Number(parsed.amount_sent) || 0,
      currency_sent: String(parsed.currency_sent || "UNKNOWN"),
      amount_received: Number(parsed.amount_received) || 0,
      currency_received: String(parsed.currency_received || "UNKNOWN"),
      fee_paid: Number(parsed.fee_paid) || 0,
      rate_used: Number(parsed.rate_used) || 0,
      date: String(parsed.date || new Date().toISOString().split("T")[0]),
    };
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Gemini API error: ${error.message}`);
    }
    throw new Error("Gemini API error: Unknown error");
  }
}
