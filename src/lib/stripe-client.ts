import Stripe from "stripe";

let _stripe: Stripe | null = null;

export function getStripe(): Stripe {
  if (!_stripe) {
    const key = process.env.STRIPE_SECRET_KEY;
    if (!key) {
      throw new Error("STRIPE_SECRET_KEY is not set");
    }
    _stripe = new Stripe(key, {
      apiVersion: "2026-01-28.clover",
      typescript: true,
    });
  }
  return _stripe;
}

export async function createPaymentIntent(
  amount: number,
  currency: string,
  metadata: Record<string, string>
): Promise<Stripe.PaymentIntent> {
  try {
    const paymentIntent = await getStripe().paymentIntents.create({
      amount,
      currency: currency.toLowerCase(),
      metadata,
      automatic_payment_methods: {
        enabled: true,
      },
    });

    return paymentIntent;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Stripe PaymentIntent error: ${error.message}`);
    }
    throw new Error("Stripe PaymentIntent error: Unknown error");
  }
}

export async function createReportCheckoutSession(): Promise<Stripe.Checkout.Session> {
  try {
    const session = await getStripe().checkout.sessions.create({
      mode: "payment",
      payment_method_types: ["card"],
      line_items: [
        {
          price_data: {
            currency: "eur",
            unit_amount: 99, // €0.99
            product_data: {
              name: "Detailed Transfer Report",
              description:
                "Full provider breakdown with Claude AI analysis and personalized recommendation.",
            },
          },
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"}/report?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"}/compare`,
      metadata: { type: "report" },
    });
    return session;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Stripe Report Checkout error: ${error.message}`);
    }
    throw new Error("Stripe Report Checkout error: Unknown error");
  }
}

export async function createCheckoutSession(
  priceId: string,
  customerId?: string
): Promise<Stripe.Checkout.Session> {
  try {
    const sessionParams: Stripe.Checkout.SessionCreateParams = {
      mode: "subscription",
      payment_method_types: ["card"],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      success_url: `${process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"}/subscription/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000"}/subscription/cancel`,
    };

    if (customerId) {
      sessionParams.customer = customerId;
    }

    const session = await getStripe().checkout.sessions.create(sessionParams);
    return session;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Stripe Checkout error: ${error.message}`);
    }
    throw new Error("Stripe Checkout error: Unknown error");
  }
}
