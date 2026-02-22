import { NextRequest, NextResponse } from "next/server";
import { getLatestRate, getHistoricalRates, SUPPORTED_CURRENCIES } from "@/lib/frankfurter";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const from = searchParams.get("from")?.toUpperCase();
  const to = searchParams.get("to")?.toUpperCase();
  const history = searchParams.get("history");

  // Validate required params
  if (!from || !to) {
    return NextResponse.json(
      { error: "Missing required query parameters: from and to" },
      { status: 400 }
    );
  }

  if (from === to) {
    return NextResponse.json(
      { error: "Source and target currencies must be different." },
      { status: 400 }
    );
  }

  try {
    // If history param is provided, return historical rates
    // Historical rates only available for ECB currencies (Frankfurter)
    if (history) {
      if (!SUPPORTED_CURRENCIES.has(from)) {
        return NextResponse.json(
          { error: `Historical rates unavailable for ${from}. Only ECB currencies supported for history.` },
          { status: 400 }
        );
      }
      if (!SUPPORTED_CURRENCIES.has(to)) {
        return NextResponse.json(
          { error: `Historical rates unavailable for ${to}. Only ECB currencies supported for history.` },
          { status: 400 }
        );
      }

      const days = parseInt(history, 10);
      if (isNaN(days) || days < 1 || days > 365) {
        return NextResponse.json(
          { error: "history must be a number between 1 and 365" },
          { status: 400 }
        );
      }

      const endDate = new Date().toISOString().split("T")[0];
      const startDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
        .toISOString()
        .split("T")[0];

      const rates = await getHistoricalRates(from, to, startDate, endDate);

      return NextResponse.json(
        {
          from_currency: from,
          to_currency: to,
          days: days,
          data_points: rates.length,
          rates,
        },
        {
          headers: {
            "Cache-Control": "public, max-age=300, s-maxage=300",
          },
        }
      );
    }

    // Default: return latest rate
    const { rate, date } = await getLatestRate(from, to);

    return NextResponse.json(
      {
        from_currency: from,
        to_currency: to,
        rate,
        date,
      },
      {
        headers: {
          "Cache-Control": "public, max-age=300, s-maxage=300",
        },
      }
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch exchange rate";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
