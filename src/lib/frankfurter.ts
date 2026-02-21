const BASE_URL = "https://api.frankfurter.dev/v1";
const OPEN_ER_BASE_URL = "https://open.er-api.com/v6/latest";

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

interface OpenERLatestResponse {
  result: string;
  base_code: string;
  time_last_update_utc: string;
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
  // Try Frankfurter first (ECB reference rates)
  try {
    const response = await fetch(
      `${BASE_URL}/latest?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`
    );
    if (response.ok) {
      const data: FrankfurterLatestResponse = await response.json();
      const rate = data.rates[to];
      if (rate !== undefined) return { rate, date: data.date };
    }
  } catch {
    // fall through to backup
  }

  // Fallback: open.er-api.com (supports 160+ currencies incl. MAD, NGN, PKR…)
  try {
    const response = await fetch(
      `${OPEN_ER_BASE_URL}/${encodeURIComponent(from)}`
    );
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    const data: OpenERLatestResponse = await response.json();
    if (data.result !== "success") throw new Error(data.result);
    const rate = data.rates[to];
    if (rate === undefined) throw new Error(`Rate not found for ${from} to ${to}`);
    const date = new Date(data.time_last_update_utc).toISOString().split("T")[0];
    return { rate, date };
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Unknown error";
    throw new Error(`Failed to fetch latest rate for ${from}→${to}: ${msg}`);
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
