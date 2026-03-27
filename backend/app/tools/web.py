"""
Web search and scraping tools.
Uses SearXNG (local, private) for search, httpx + readability for scraping.
Falls back to DuckDuckGo if SearXNG is unavailable.
"""

import httpx
import re
from typing import Optional
from app.config import settings


async def search(query: str, num_results: int = 5) -> dict:
    """Search the web. Tries SearXNG first, falls back to DuckDuckGo HTML."""
    num_results = int(num_results)
    try:
        return await _searxng_search(query, num_results)
    except Exception:
        return await _duckduckgo_fallback(query, num_results)


async def _searxng_search(query: str, num_results: int) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.SEARXNG_URL}/search",
            params={"q": query, "format": "json", "categories": "general", "pageno": 1},
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("results", [])[:num_results]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            })
        return {"results": results, "source": "searxng"}


async def _duckduckgo_fallback(query: str, num_results: int) -> dict:
    """DuckDuckGo search fallback using the ddgs/duckduckgo-search library."""
    import asyncio
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        from ddgs import DDGS  # renamed package

    def _sync_search():
        with DDGS() as ddgs:
            # Try news search first for news-like queries
            news_keywords = ("news", "affairs", "latest", "today", "breaking", "headlines")
            if any(kw in query.lower() for kw in news_keywords):
                results = list(ddgs.news(query, max_results=num_results))
                if results:
                    return [
                        {"title": r.get("title", ""), "url": r.get("url", ""),
                         "snippet": r.get("body", r.get("date", ""))}
                        for r in results
                    ]
            # General web search
            results = list(ddgs.text(query, max_results=num_results))
            return [
                {"title": r.get("title", ""), "url": r.get("href", ""),
                 "snippet": r.get("body", "")}
                for r in results
            ]

    results = await asyncio.to_thread(_sync_search)
    return {"results": results, "source": "duckduckgo"}


async def scrape(url: str) -> dict:
    """Fetch a web page and extract main text content."""
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Aria/1.0)"})
        resp.raise_for_status()
        html = resp.text

    # Simple text extraction — strip HTML tags, collapse whitespace
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Limit to ~8000 chars to avoid overwhelming the model
    if len(text) > 8000:
        text = text[:8000] + "... [truncated]"

    return {"url": url, "content": text, "length": len(text)}
