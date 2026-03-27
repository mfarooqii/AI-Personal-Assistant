"""
Async client for Ollama — the local model server.
Provides chat completion, streaming, embeddings, and model management.
"""

import httpx
import json
from typing import AsyncIterator, Optional

from app.config import settings

_client: Optional[httpx.AsyncClient] = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(base_url=settings.OLLAMA_BASE_URL, timeout=300)
    return _client


class ModelUnavailableError(Exception):
    """Raised when an Ollama model can't be loaded (OOM, missing, etc.)."""
    pass


async def chat_completion(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
    tools: Optional[list[dict]] = None,
) -> dict:
    """Non-streaming chat completion. Returns full response dict."""
    client = _get_client()
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    if tools:
        payload["tools"] = tools
    resp = await client.post("/api/chat", json=payload)

    # Detect model-load failures (OOM, missing model, etc.)
    if resp.status_code == 500:
        body = resp.text
        if any(kw in body for kw in ("memory", "not found", "pull model", "no such")):
            raise ModelUnavailableError(f"Model '{model}' unavailable: {body[:200]}")

    resp.raise_for_status()
    return resp.json()


async def chat_stream(
    model: str,
    messages: list[dict],
    temperature: float = 0.7,
) -> AsyncIterator[str]:
    """Streaming chat — yields content tokens as they arrive."""
    client = _get_client()
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature},
    }
    async with client.stream("POST", "/api/chat", json=payload) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line:
                continue
            data = json.loads(line)
            token = data.get("message", {}).get("content", "")
            if token:
                yield token


async def get_embedding(text: str) -> Optional[list[float]]:
    """Get embedding vector for a piece of text."""
    try:
        client = _get_client()
        resp = await client.post(
            "/api/embed",
            json={"model": settings.MODEL_EMBEDDING, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("embeddings", [None])[0]
    except Exception:
        return None


async def list_models() -> list[dict]:
    """List locally available Ollama models."""
    try:
        client = _get_client()
        resp = await client.get("/api/tags")
        resp.raise_for_status()
        return resp.json().get("models", [])
    except Exception:
        return []


async def pull_model(model_name: str) -> AsyncIterator[str]:
    """Pull a model — yields progress lines."""
    client = _get_client()
    async with client.stream(
        "POST", "/api/pull", json={"name": model_name, "stream": True}
    ) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if line:
                yield line


async def is_ollama_available() -> bool:
    try:
        client = _get_client()
        resp = await client.get("/api/tags")
        return resp.status_code == 200
    except Exception:
        return False
