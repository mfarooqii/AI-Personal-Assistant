"""
Browser intent detection — quickly determines if a user query needs the
in-app browser agent rather than the normal chat/tool agent pipeline.

This runs BEFORE the regular router, as a fast heuristic.  If it fires,
the chat route streams a browser task via browser-use + CDP into the
live visible Electron BrowserView.
"""

import re
from app.config import settings

# ── Patterns that signal browser usage ───────────────────────────────────────

_EMAIL_PATTERN = re.compile(
    r"\b(show|check|open|read|get|summarize|skim|browse|look at|see|manage)\b"
    r".*\b(email|emails|inbox|gmail|hotmail|yahoo mail|outlook|mail)\b",
    re.IGNORECASE,
)

_SHOPPING_PATTERN = re.compile(
    r"\b(find|search|look for|browse|shop|buy|compare|show me|order|purchase)\b"
    r".*\b(on amazon|on ebay|on walmart|on etsy|product|shopping|deal|toolkit|gadget)\b",
    re.IGNORECASE,
)

# "search for X" or "find X" without requiring a site — product-intent heuristic
_SEARCH_PRODUCT_PATTERN = re.compile(
    r"\b(search for|find me|look for|show me)\b"
    r"\s+(?:a |an |some |the )?"
    r"([\w\s]{3,50})"
    r"(?:\s+(?:shoes?|shirt|clothes|dress|laptop|phone|bag|watch|camera|"
    r"electronics|clothing|apparel|product|item|gadget|headphone|keyboard|"
    r"monitor|desk|chair|jacket|pants|sneaker|boot|hat|glass)s?)?",
    re.IGNORECASE,
)

_LOGIN_PATTERN = re.compile(
    r"\b(sign in|log ?in|login|connect|sign into|log into)\b"
    r".*\b(gmail|google|amazon|outlook|yahoo|facebook|twitter|linkedin|hotmail|github|notion|slack)\b",
    re.IGNORECASE,
)

# Sign up / register / create account on any site
_SIGNUP_PATTERN = re.compile(
    r"\b(sign up|signup|register|create (an? )?account|join)\b"
    r".*\b(on|for|at|with)\b",
    re.IGNORECASE,
)

# Generic URL navigation — "go to X", "open X", "navigate to X"
_BROWSE_PATTERN = re.compile(
    r"\b(open|go to|visit|browse|navigate|head to|take me to|launch)\b"
    r".{1,60}?\b(website|site|page|\.com|\.org|\.net|\.io|\.app|\.dev|http|https|www\.|"
    r"google|youtube|reddit|github|twitter|instagram|facebook|linkedin|amazon|"
    r"netflix|spotify|notion|slack|discord|twitch|tiktok|wikipedia)\b",
    re.IGNORECASE,
)

# Bare URL pasted by user (e.g. "github.com/myrepo give it a star")
_URL_PASTE_PATTERN = re.compile(
    r"(https?://|www\.)\S+|[a-zA-Z0-9-]+\.(com|org|net|io|app|dev|co)\b",
    re.IGNORECASE,
)

# Government / official sites
_GOVERNMENT_PATTERN = re.compile(
    r"\b(check|look up|find|search|apply|renew|schedule|file)\b"
    r".*\b(dmv|irs|passport|visa|government|social security|medicare|ssa\.gov|irs\.gov)\b",
    re.IGNORECASE,
)

# General "do something on a website" tasks
_WEB_TASK_PATTERN = re.compile(
    r"\b(fill out|fill in|submit|complete|book|reserve|schedule|search for|look up|find me|"
    r"download from|upload to|post on|comment on|like|follow|unsubscribe|cancel)\b"
    r".{1,80}?\b(website|site|page|online|web|portal|form|\.com|\.org|\.net|\.io)\b",
    re.IGNORECASE,
)

# Browser continuation — "search for X", "click X", "scroll down" etc. when already in browser session
_BROWSER_ACTION_PATTERN = re.compile(
    r"^(search\s+for|click\s+on|click\s+the|type\s+in|scroll\s+(up|down)|go\s+back|"
    r"fill\s+in|press\s+(enter|tab)|hit\s+enter|next\s+page|previous\s+page)\b",
    re.IGNORECASE,
)


def detect_browser_intent(message: str, recent_history: list[dict] | None = None) -> dict | None:
    """
    Check if a message requires the browser agent.

    Args:
        message: the user's message
        recent_history: last few messages from the conversation
                        Each dict has {"role": "user"|"assistant", "agent": str|None}

    Returns None if regular agents should handle it, or a dict::

        {
            "needs_browser": True,
            "category": "email",        # email | shopping | login | signup |
                                        # browse | government | web_task | continuation
            "provider_hint": "gmail",   # optional — extracted site name
        }
    """
    msg = message.strip()

    if _EMAIL_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "email",
            "provider_hint": _guess_provider(msg, ["gmail", "hotmail", "yahoo", "outlook"]),
        }

    if _SHOPPING_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "shopping",
            "provider_hint": _guess_provider(msg, ["amazon", "ebay", "walmart", "etsy"]),
        }

    if _LOGIN_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "login",
            "provider_hint": _guess_provider(msg, [
                "gmail", "google", "amazon", "outlook", "yahoo",
                "facebook", "twitter", "linkedin", "hotmail",
                "github", "notion", "slack",
            ]),
        }

    if _SIGNUP_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "signup",
            "provider_hint": _extract_domain(msg),
        }

    if _GOVERNMENT_PATTERN.search(msg):
        return {"needs_browser": True, "category": "government", "provider_hint": ""}

    if _WEB_TASK_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "web_task",
            "provider_hint": _extract_domain(msg),
        }

    if _BROWSE_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "browse",
            "provider_hint": _extract_domain(msg),
        }

    if _URL_PASTE_PATTERN.search(msg):
        return {
            "needs_browser": True,
            "category": "browse",
            "provider_hint": _extract_domain(msg),
        }

    # ── Context-aware continuation ────────────────────────────────────────────
    # If there was a recent browser task in conversation history, treat
    # follow-up browser-action messages as browser continuations.
    if recent_history and _is_browser_continuation(msg, recent_history):
        return {
            "needs_browser": True,
            "category": "continuation",
            "provider_hint": "",
        }

    return None


def _is_browser_continuation(msg: str, recent_history: list[dict]) -> bool:
    """
    Return True if:
    - There was a browser task recently in the conversation AND
    - The current message looks like a browser action (search, click, type, scroll, etc.)
    """
    # Check if the last assistant message was a browser task
    recent_browser = any(
        h.get("role") == "assistant" and h.get("agent") == "browser"
        for h in recent_history[-4:]  # look at last 4 messages
    )
    if not recent_browser:
        return False

    # Check if the message looks like a browser action
    return bool(_BROWSER_ACTION_PATTERN.search(msg) or _SEARCH_PRODUCT_PATTERN.search(msg))


def _guess_provider(msg: str, candidates: list[str]) -> str:
    """Return the first matching provider keyword found in the message."""
    lower = msg.lower()
    for p in candidates:
        if p in lower:
            return p
    return ""


def _extract_domain(msg: str) -> str:
    """Extract a domain/site name from the message if present."""
    url_match = re.search(r"(https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})", msg)
    if url_match:
        return url_match.group(2)
    return ""

