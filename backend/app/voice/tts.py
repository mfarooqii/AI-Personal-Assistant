"""
Text-to-Speech using Piper TTS (fast, local, high quality).
Falls back to edge-tts (Microsoft) if Piper is not installed.
"""

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Optional


async def synthesize(text: str, voice: Optional[str] = None) -> bytes:
    """Convert text to speech audio (WAV bytes)."""
    if shutil.which("piper"):
        return await _piper_tts(text, voice)
    else:
        return await _edge_tts_fallback(text, voice)


async def _piper_tts(text: str, voice: Optional[str] = None) -> bytes:
    """Use Piper TTS (local, fast, works offline)."""
    voice = voice or "en_US-lessac-medium"
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as out_file:
        out_path = out_file.name

    proc = await asyncio.create_subprocess_exec(
        "piper",
        "--model", voice,
        "--output_file", out_path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate(input=text.encode())

    try:
        return Path(out_path).read_bytes()
    finally:
        Path(out_path).unlink(missing_ok=True)


async def _edge_tts_fallback(text: str, voice: Optional[str] = None) -> bytes:
    """Fallback: edge-tts (Microsoft, requires internet)."""
    import edge_tts

    voice = voice or "en-US-AriaNeural"
    communicate = edge_tts.Communicate(text, voice)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as out_file:
        out_path = out_file.name

    await communicate.save(out_path)

    try:
        return Path(out_path).read_bytes()
    finally:
        Path(out_path).unlink(missing_ok=True)
