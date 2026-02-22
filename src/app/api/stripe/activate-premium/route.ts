import { NextRequest, NextResponse } from "next/server";
import { getStripe } from "@/lib/stripe-client";
import { getSupabaseServerClient } from "@/lib/supabase";

export async function POST(request: NextRequest) {
  try {
    const { session_id, access_token } = await request.json();

    if (!session_id || !access_token) {
      return NextResponse.json(
        { error: "session_id and access_token are required" },
        { status: 400 }
      );
    }

    // 1. Verify Stripe session is actually paid
    const stripe = getStripe();
    const session = await stripe.checkout.sessions.retrieve(session_id);

    if (session.payment_status !== "paid") {
      return NextResponse.json({ error: "Payment not completed" }, { status: 400 });
    }

    // 2. Get the Supabase user from their access token
    const supabase = getSupabaseServerClient();
    const { data: { user }, error } = await supabase.auth.getUser(access_token);

    if (error || !user) {
      return NextResponse.json({ error: "Invalid session" }, { status: 401 });
    }

    // 3. Grant Premium via service role (bypasses RLS)
    await supabase.auth.admin.updateUserById(user.id, {
      user_metadata: { ...user.user_metadata, isPremium: true },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
