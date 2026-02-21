const BASE_URL = "https://api.frankfurter.dev/v1";

// Currencies supported by the Frankfurter API (ECB reference rates)
export const SUPPORTED_CURRENCIES = new Set([
  "AUD", "BRL", "CAD", "CHF", "CNY", "CZK", "DKK", "EUR", "GBP", "HKD",
  "HUF", "IDR", "ILS", "INR", "ISK", "JPY", "KRW", "MXN", "MYR", "NOK",
  "NZD", "PHP", "PLN", "RON", "SEK", "SGD", "THB", "TRY", "USD", "ZAR",
]);

interface FrankfurterLatestResponse {
  amount: number;
  base: string;
  date: string;
  rates: Record<string, number>;
}

interface FrankfurterTimeSeriesResponse {
  amount: number;
  base: string;
  start_date: string;
  end_date: string;
  rates: Record<string, Record<string, number>>;
}

export async function getLatestRate(
  from: string,
  to: string
): Promise<{ rate: number; date: string }> {
  try {
    const response = await fetch(
      `${BASE_URL}/latest?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`
    );

    if (!response.ok) {
      throw new Error(
        `Frankfurter API error: ${response.status} ${response.statusText}`
      );
    }

    const data: FrankfurterLatestResponse = await response.json();
    const rate = data.rates[to];

    if (rate === undefined) {
      throw new Error(`Rate not found for ${from} to ${to}`);
    }

    return { rate, date: data.date };
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to fetch latest rate: ${error.message}`);
    }
    throw new Error("Failed to fetch latest rate: Unknown error");
  }
}

export async function getHistoricalRates(
  from: string,
  to: string,
  startDate: string,
  endDate: string
): Promise<{ date: string; rate: number }[]> {
  try {
    const response = await fetch(
      `${BASE_URL}/${encodeURIComponent(startDate)}..${encodeURIComponent(endDate)}?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`
    );

    if (!response.ok) {
      throw new Error(
        `Frankfurter API error: ${response.status} ${response.statusText}`
      );
    }

    const data: FrankfurterTimeSeriesResponse = await response.json();

    const rates: { date: string; rate: number }[] = Object.entries(data.rates)
      .map(([date, rateMap]) => ({
        date,
        rate: rateMap[to],
      }))
      .filter((entry) => entry.rate !== undefined)
      .sort((a, b) => a.date.localeCompare(b.date));

    return rates;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to fetch historical rates: ${error.message}`);
    }
    throw new Error("Failed to fetch historical rates: Unknown error");
  }
}
