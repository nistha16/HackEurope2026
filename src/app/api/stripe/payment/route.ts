import { NextRequest, NextResponse } from "next/server";
import {
  createPaymentIntent,
  createCheckoutSession,
} from "@/lib/stripe-client";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { type, amount, currency, price_id } = body as {
      type: "rate_lock" | "subscription";
      amount?: number;
      currency?: string;
      price_id?: string;
    };

    if (!type) {
      return NextResponse.json(
        { error: "type is required (rate_lock or subscription)" },
        { status: 400 }
      );
    }

    if (type === "rate_lock") {
      if (!amount || !currency) {
        return NextResponse.json(
          {
            error:
              "amount (in cents) and currency are required for rate_lock payments",
          },
          { status: 400 }
        );
      }

      const paymentIntent = await createPaymentIntent(amount, currency, {
        type: "rate_lock",
      });

      return NextResponse.json({
        clientSecret: paymentIntent.client_secret,
      });
    }

    if (type === "subscription") {
      if (!price_id) {
        return NextResponse.json(
          { error: "price_id is required for subscription payments" },
          { status: 400 }
        );
      }

      const session = await createCheckoutSession(price_id);

      return NextResponse.json({
        url: session.url,
      });
    }

    return NextResponse.json(
      { error: "Invalid type. Must be rate_lock or subscription" },
      { status: 400 }
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Payment processing failed: ${message}` },
      { status: 500 }
    );
  }
}
