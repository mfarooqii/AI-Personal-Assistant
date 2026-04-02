"""
Browser intent detection — quickly determines if a user query needs the
in-app browser agent rather than the normal chat/tool agent pipeline.

This runs BEFORE the regular router, as a fast heuristic + optional
small-model check.  If it fires, the chat route returns a special
"browser" layout directive that triggers the BrowserPanel on the frontend.
"""

import re
from app.config import settings

# ── Keyword patterns that strongly signal browser usage ───

_EMAIL_PATTERN = re.compile(
    r"\b(show|check|open|read|get|summarize|skim|browse|look at|see|manage)\b"
    r".*\b(email|emails|inbox|gmail|hotmail|yahoo mail|outlook|mail)\b",
    re.IGNORECASE,
)

_SHOPPING_PATTERN = re.compile(
    r"\b(find|search|look for|browse|shop|buy|compare|show me)\b"
    r".*\b(on amazon|on ebay|on walmart|on etsy|product|shopping|deal|toolkit|gadget)\b",
    re.IGNORECASE,
)

_LOGIN_PATTERN = re.compile(
    r"\b(sign in|log ?in|login|connect|sign into|log into)\b"
    r".*\b(gmail|google|amazon|outlook|yahoo|facebook|twitter|linkedin|hotmail)\b",
    re.IGNORECASE,
)

_BROWSE_PATTERN = re.compile(
    r"\b(open|go to|visit|browse|navigate)\b"
    r".*\b(website|site|page|\.com|\.org|\.net|http)\b",
    re.IGNORECASE,
)

_GOVERNMENT_PATTERN = re.compile(
    r"\b(check|look up|find|search|apply|renew|schedule)\b"
    r".*\b(dmv|irs|passport|visa|government|social security|medicare|ssa\.gov|irs\.gov)\b",
    re.IGNORECASE,
)


def detect_browser_intent(message: str) -> dict | None:
    """
    Check if a message requires the browser agent.

    Returns None if regular agents should handle it, or a dict like::

        {
            "needs_browser": True,
            "category": "email",        # email | shopping | login | browse | government
            "provider_hint": "gmail",    # optional
        }
    """
    msg = message.strip()

    if _EMAIL_PATTERN.search(msg):
        provider = _guess_provider(msg, ["gmail", "hotmail", "yahoo", "outlook"])
        return {
            "needs_browser": True,
            "category": "email",
            "provider_hint": provider,
        }

    if _SHOPPING_PATTERN.search(msg):
        provider = _guess_provider(msg, ["amazon", "ebay", "walmart", "etsy"])
        return {
            "needs_browser": True,
            "category": "shopping",
            "provider_hint": provider,
        }

    if _LOGIN_PATTERN.search(msg):
        provider = _guess_provider(msg, [
            "gmail", "google", "amazon", "outlook", "yahoo",
            "facebook", "twitter", "linkedin", "hotmail",
        ])
        return {
            "needs_browser": True,
            "category": "login",
            "provider_hint": provider,
        }

    if _GOVERNMENT_PATTERN.search(msg):
        return {"needs_browser": True, "category": "government", "provider_hint": ""}

    if _BROWSE_PATTERN.search(msg):
        return {"needs_browser": True, "category": "browse", "provider_hint": ""}

    return None


def _guess_provider(msg: str, candidates: list[str]) -> str:
    """Return the first matching provider keyword found in the message."""
    lower = msg.lower()
    for p in candidates:
        if p in lower:
            return p
    return ""
