const VOICE_ID = "CwhRBWXzGAHq8TQ4Fs17";

export async function textToSpeech(text) {
  const apiKey = import.meta.env.VITE_ELEVENLABS_API_KEY;

  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`, {
    method: "POST",
    headers: {
      "xi-api-key": apiKey,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      text,
      model_id: "eleven_turbo_v2" 
    })
  });

  if (!res.ok) throw new Error(await res.text());
  return res.blob();
}
