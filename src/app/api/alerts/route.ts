import { NextRequest, NextResponse } from "next/server";
import type { RateAlert } from "@/types";

// In-memory storage for rate alerts
const alerts: RateAlert[] = [];

export async function GET() {
  return NextResponse.json(alerts);
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { source_currency, target_currency, target_rate } = body as {
      source_currency: string;
      target_currency: string;
      target_rate: number;
    };

    if (!source_currency || !target_currency || !target_rate) {
      return NextResponse.json(
        {
          error:
            "source_currency, target_currency, and target_rate are required",
        },
        { status: 400 }
      );
    }

    if (typeof target_rate !== "number" || target_rate <= 0) {
      return NextResponse.json(
        { error: "target_rate must be a positive number" },
        { status: 400 }
      );
    }

    const newAlert: RateAlert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`,
      source_currency,
      target_currency,
      target_rate,
      is_active: true,
      created_at: new Date().toISOString(),
    };

    alerts.push(newAlert);

    return NextResponse.json(newAlert, { status: 201 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to create alert: ${message}` },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get("id");

    if (!id) {
      return NextResponse.json(
        { error: "id query parameter is required" },
        { status: 400 }
      );
    }

    const index = alerts.findIndex((alert) => alert.id === id);

    if (index === -1) {
      return NextResponse.json(
        { error: `Alert with id "${id}" not found` },
        { status: 404 }
      );
    }

    const [removed] = alerts.splice(index, 1);

    return NextResponse.json({
      message: "Alert deleted successfully",
      alert: removed,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Failed to delete alert: ${message}` },
      { status: 500 }
    );
  }
}
