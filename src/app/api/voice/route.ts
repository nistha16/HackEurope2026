import { NextRequest, NextResponse } from "next/server";
import { textToSpeech } from "@/lib/elevenlabs";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { text } = body as { text: string };

    if (!text || typeof text !== "string" || text.trim().length === 0) {
      return NextResponse.json(
        { error: "text is required and must be a non-empty string" },
        { status: 400 }
      );
    }

    const audioBuffer = await textToSpeech(text);

    return new Response(audioBuffer, {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Content-Length": audioBuffer.byteLength.toString(),
      },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json(
      { error: `Voice synthesis failed: ${message}` },
      { status: 500 }
    );
  }
}
