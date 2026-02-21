const ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech";
const VOICE_ID = "21m00Tcm4TlvDq8ikWAM"; // Rachel

export async function textToSpeech(text: string): Promise<ArrayBuffer> {
  const apiKey = process.env.ELEVENLABS_API_KEY;

  if (!apiKey) {
    throw new Error("ELEVENLABS_API_KEY environment variable is not set");
  }

  try {
    const response = await fetch(`${ELEVENLABS_API_URL}/${VOICE_ID}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "xi-api-key": apiKey,
      },
      body: JSON.stringify({
        text,
        model_id: "eleven_monolingual_v1",
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
        },
      }),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(
        `ElevenLabs API error: ${response.status} ${response.statusText} - ${errorBody}`
      );
    }

    const audioBuffer = await response.arrayBuffer();
    return audioBuffer;
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`ElevenLabs TTS error: ${error.message}`);
    }
    throw new Error("ElevenLabs TTS error: Unknown error");
  }
}
