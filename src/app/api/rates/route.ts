import { NextRequest, NextResponse } from "next/server";
import { getLatestRate } from "@/lib/frankfurter";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const from = searchParams.get("from");
    const to = searchParams.get("to");

    if (!from || !to) {
      return NextResponse.json(
        { error: "Missing required query parameters: from and to" },
        { status: 400 }
      );
    }

    const { rate, date } = await getLatestRate(from.toUpperCase(), to.toUpperCase());

    return NextResponse.json({ rate, date });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to fetch exchange rate";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
