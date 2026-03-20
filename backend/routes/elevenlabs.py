import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.responses import StreamingResponse

router = APIRouter()

class TTSRequest(BaseModel):
    text: str

@router.post("/api/elevenlabs/tts")
def text_to_speech(payload: TTSRequest):
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    if not ELEVENLABS_API_KEY:
        raise HTTPException(status_code=500, detail="ELEVENLABS_API_KEY environment variable not set.")

    VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
    TTS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }

    data = {
        "text": payload.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        response = requests.post(TTS_URL, json=data, headers=headers, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return StreamingResponse(response.iter_content(chunk_size=1024), media_type="audio/mpeg")

    except requests.exceptions.RequestException as e:
        # Log the error and return a more informative error message
        print(f"Error calling ElevenLabs API: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to get audio from ElevenLabs: {e}")
