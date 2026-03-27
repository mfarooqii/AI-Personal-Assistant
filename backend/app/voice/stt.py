"""
Speech-to-Text using faster-whisper (runs locally, no API needed).
Supports real-time and file-based transcription.
"""

import tempfile
from pathlib import Path
from typing import Optional

_model = None


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        from app.config import settings
        # Use tiny/base for speed on normal laptops, medium/large for better hardware
        model_size = settings.STT_MODEL.replace("whisper-", "")
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model


async def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None) -> dict:
    """Transcribe audio bytes to text."""
    import asyncio

    def _transcribe():
        model = _get_model()
        # Write to temp file (faster-whisper needs a file path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            temp_path = f.name

        try:
            segments, info = model.transcribe(
                temp_path,
                language=language,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text.strip() for seg in segments)
            return {
                "text": text,
                "language": info.language,
                "language_probability": round(info.language_probability, 2),
                "duration": round(info.duration, 1),
            }
        finally:
            Path(temp_path).unlink(missing_ok=True)

    # Run in thread pool to avoid blocking the event loop
    return await asyncio.get_event_loop().run_in_executor(None, _transcribe)
