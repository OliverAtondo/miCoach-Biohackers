import os
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse
from elevenlabs.client import ElevenLabs

router = APIRouter()

class TTSRequest(BaseModel):
    text: str

@router.post("/api/elevenlabs/tts")
def text_to_speech(payload: TTSRequest):
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY environment variable not set.")

    try:
        # Create a custom httpx client that disables SSL verification for the hackathon.
        # WARNING: This is insecure and should not be used in production.
        custom_httpx_client = httpx.Client(verify=False)

        client = ElevenLabs(
            api_key=ELEVENLABS_API_KEY,
            httpx_client=custom_httpx_client  # Pass the custom client
        )

        # Generate audio stream from text
        audio_stream = client.generate(
            text=payload.text,
            voice="CwhRBWXzGAHq8TQ4Fs17",
            model="eleven_flash_v2_5"
        )
        
        # Return the stream as a response
        return StreamingResponse(audio_stream, media_type="audio/mpeg")

    except Exception as e:
        # Catch potential exceptions from the SDK
        print(f"Error calling ElevenLabs API via SDK: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to get audio from ElevenLabs: {str(e)}")
