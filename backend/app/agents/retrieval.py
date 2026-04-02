"""
Pre-Retrieval Pipeline — Perplexity-style "search first, then generate" approach.

The core problem this solves: LLMs sometimes skip tool calls and answer from
training data. For news and research queries we MUST have real data.

Solution:
  1. Detect "retrieval-first" intent from the user message
  2. Run web_search / news_search automatically BEFORE the model
  3. Inject real results into the system prompt as grounding context
  4. Model then synthesizes/summarizes — never hallucinates a "no results" answer

This is how Perplexity.ai, ChatGPT Search, and Claude Search work internally.
"""

import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.web import search as web_search_fn, news_search as news_search_fn, scrape


# ── Intent Detection ──────────────────────────────────────

NEWS_KEYWORDS = [
    "news", "article", "today", "latest", "recent", "current", "breaking",
    "headlines", "what happened", "what's happening", "politics", "election",
    "government", "economy", "war", "conflict", "sports", "weather",
    "show me", "tell me about", "what are", "find articles", "top stories",
]

RESEARCH_KEYWORDS = [
    "search", "find", "look up", "research", "what is", "how does", "explain",
    "compare", "best", "review", "recommend", "product", "price", "buy",
    "where can", "help me find", "show results",
]

SHOPPING_KEYWORDS = [
    "buy", "purchase", "shop", "deal", "price", "compare", "product",
    "laptop", "phone", "tv", "camera", "headphones", "specs",
]


def is_retrieval_query(message: str) -> tuple[bool, str]:
    """
    Returns (should_retrieve, query_type).
    query_type: "news" | "research" | "shopping" | None
    """
    msg = message.lower()

    if any(kw in msg for kw in NEWS_KEYWORDS):
        return True, "news"
    if any(kw in msg for kw in SHOPPING_KEYWORDS):
        return True, "shopping"
    if any(kw in msg for kw in RESEARCH_KEYWORDS):
        return True, "research"
    return False, "none"


def _clean_query(message: str) -> str:
    """Remove conversational filler to make a clean search query."""
    remove_phrases = [
        "can you", "could you", "please", "i want to", "i need to",
        "show me", "tell me", "find me", "help me", "would you",
        "do you know", "what are", "search for",
    ]
    q = message.lower()
    for phrase in remove_phrases:
        q = q.replace(phrase, "")
    q = re.sub(r"\s+", " ", q).strip()
    # Limit query length
    return q[:150]


# ── Pre-Retrieval Engine ──────────────────────────────────

async def pre_retrieve(
    user_message: str,
    db: AsyncSession,
    num_results: int = 5,
    scrape_top: int = 1,
) -> dict | None:
    """
    Run web search BEFORE the model responds.

    Returns a retrieval context dict, or None if not applicable.
    {
        "query_type": "news" | "research" | "shopping",
        "search_results": [...],
        "articles": [...],   # scraped full content for top results
        "grounding_prompt": str,  # ready-to-inject context for the model
    }
    """
    should_retrieve, query_type = is_retrieval_query(user_message)
    if not should_retrieve:
        return None

    query = _clean_query(user_message)
    # Add today's date context for news queries
    if query_type == "news":
        today = datetime.now().strftime("%B %d, %Y")
        query_with_date = f"{query} {today}"
    else:
        query_with_date = query

    # Run appropriate search
    try:
        if query_type == "news":
            search_data = await news_search_fn(query_with_date, num_results=num_results)
        else:
            search_data = await web_search_fn(query_with_date, num_results=num_results)
    except Exception as e:
        return None

    results = search_data.get("results", [])
    if not results:
        return None

    # Scrape the top article(s) for rich content
    articles = []
    for result in results[:scrape_top]:
        url = result.get("url", "")
        if not url:
            continue
        try:
            article = await scrape(url)
            if article.get("content") and len(article["content"]) > 200:
                articles.append(article)
        except Exception:
            pass  # Don't fail the whole pipeline if scraping fails

    # Build grounding prompt to inject into system context
    grounding_prompt = _build_grounding_prompt(query_type, results, articles, user_message)

    return {
        "query_type": query_type,
        "query": query,
        "search_results": results,
        "articles": articles,
        "grounding_prompt": grounding_prompt,
        "source": search_data.get("source", ""),
    }


def _build_grounding_prompt(
    query_type: str,
    results: list[dict],
    articles: list[dict],
    original_query: str,
) -> str:
    """Build the context string to inject into the model's system prompt."""
    today = datetime.now().strftime("%B %d, %Y")
    lines = [
        f"\n\n--- RETRIEVED WEB RESULTS (fetched {today}) ---",
        f"Query: {original_query}",
        "",
    ]

    # Full article content first (most valuable)
    for article in articles:
        lines.append(f"## ARTICLE: {article.get('title', 'Untitled')}")
        if article.get("author"):
            lines.append(f"Author: {article['author']}")
        if article.get("published_date"):
            lines.append(f"Published: {article['published_date']}")
        if article.get("hostname"):
            lines.append(f"Source: {article['hostname']}")
        lines.append(f"URL: {article.get('url', '')}")
        if article.get("description"):
            lines.append(f"Summary: {article['description']}")
        lines.append("")
        content = article.get("content", "")
        # Include first 4000 chars of article body
        lines.append(content[:4000] + ("..." if len(content) > 4000 else ""))
        lines.append("")

    # Search result snippets for additional context
    lines.append("## ADDITIONAL SEARCH RESULTS:")
    for i, r in enumerate(results):
        lines.append(
            f"{i+1}. [{r.get('title', '')}]({r.get('url', '')}) — "
            f"{r.get('source', '')} {r.get('published_date', '')}"
        )
        if r.get("snippet"):
            lines.append(f"   {r['snippet'][:300]}")
        lines.append("")

    lines.extend([
        "--- END OF WEB RESULTS ---",
        "",
        "IMPORTANT INSTRUCTIONS:",
        "- Base your response ENTIRELY on the retrieved content above.",
        "- DO NOT use your training data for facts — only use what is in the results.",
        "- Cite sources inline using [Source Name](URL) format.",
        "- If the results are from today's date, mention that explicitly.",
        "- Format your response as a well-structured article with headings.",
        "- Include key facts, quotes, and important details from the sources.",
    ])

    return "\n".join(lines)
