"""
Voice routes — speech-to-text and text-to-speech endpoints.
"""

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional

from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize

router = APIRouter()


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    """Transcribe uploaded audio to text."""
    audio_bytes = await audio.read()
    result = await transcribe_audio(audio_bytes)
    return result


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Convert text to speech audio."""
    audio_bytes = await synthesize(req.text, req.voice)
    return Response(content=audio_bytes, media_type="audio/wav")
