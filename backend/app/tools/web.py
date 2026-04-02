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


async def news_search(query: str, num_results: int = 5) -> dict:
    """Search specifically for recent news articles. Returns title, url, snippet, source, published_date."""
    num_results = int(num_results)
    # Try SearXNG news category first
    try:
        return await _searxng_news_search(query, num_results)
    except Exception:
        pass
    # Fallback to DDG news
    try:
        return await _duckduckgo_news_fallback(query, num_results)
    except Exception as e:
        return {"results": [], "source": "none", "error": str(e)}


async def _searxng_news_search(query: str, num_results: int) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{settings.SEARXNG_URL}/search",
            params={"q": query, "format": "json", "categories": "news", "pageno": 1},
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for r in data.get("results", [])[:num_results]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
                "source": r.get("source", ""),
                "published_date": r.get("publishedDate", ""),
            })
        return {"results": results, "source": "searxng_news"}


async def _duckduckgo_news_fallback(query: str, num_results: int) -> dict:
    """DuckDuckGo news search fallback."""
    import asyncio
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        from ddgs import DDGS

    def _sync_news():
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=num_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", ""),
                    "source": r.get("source", ""),
                    "published_date": r.get("date", ""),
                }
                for r in results
            ]

    results = await asyncio.to_thread(_sync_news)
    return {"results": results, "source": "duckduckgo_news"}


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
    """Fetch a web page and extract main text content with article metadata."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text

    return _extract_article(html, url)


def _extract_article(html: str, url: str) -> dict:
    """Extract structured article data from HTML."""
    # Try trafilatura first (best-in-class content extractor)
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html,
            include_images=True,
            include_links=False,
            output_format='json',
            with_metadata=True,
        )
        if extracted:
            import json as _json
            data = _json.loads(extracted)
            text = data.get("text", "")
            if len(text) > 300:  # meaningful content
                return {
                    "url": url,
                    "title": data.get("title", ""),
                    "author": data.get("author", ""),
                    "published_date": data.get("date", ""),
                    "content": text[:8000] + ("..." if len(text) > 8000 else ""),
                    "image": data.get("image", ""),
                    "description": data.get("description", ""),
                    "hostname": data.get("hostname", ""),
                    "length": len(text),
                    "extractor": "trafilatura",
                }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: manual HTML extraction with metadata
    return _manual_extract(html, url)


def _manual_extract(html: str, url: str) -> dict:
    """Manual extractor: pulls og/meta tags + strips HTML."""
    # Extract Open Graph / meta tags
    def _meta(pattern: str) -> str:
        m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else ""

    title = (
        _meta(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']')
        or _meta(r'<title[^>]*>(.*?)</title>')
        or ""
    )
    description = (
        _meta(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']')
        or _meta(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']')
        or ""
    )
    image = (
        _meta(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']')
        or ""
    )
    author = (
        _meta(r'<meta[^>]+name=["\']author["\'][^>]+content=["\'](.*?)["\']')
        or _meta(r'"author"[^"]*"[^"]*"[^"]*"(.*?)"')
        or ""
    )
    published_date = (
        _meta(r'<meta[^>]+(?:property=["\']article:published_time["\']|name=["\']pubdate["\'])[^>]+content=["\'](.*?)["\']')
        or ""
    )

    # Strip scripts, styles, nav, footer
    text = re.sub(r"<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) > 8000:
        text = text[:8000] + "..."

    return {
        "url": url,
        "title": title,
        "author": author,
        "published_date": published_date,
        "content": text,
        "image": image,
        "description": description,
        "hostname": re.sub(r"^www\.", "", re.search(r"https?://([^/]+)", url).group(1) if re.search(r"https?://([^/]+)", url) else ""),
        "length": len(text),
        "extractor": "manual",
    }
