"""
Layout Engine — analyzes the AI's response and user intent to determine
what dashboard view the frontend should display.

The engine returns a layout directive that tells the frontend:
  - which view component to render (calendar, finance, search, kanban, etc.)
  - structured data to populate that view
  - optional metadata (title, filters, actions)

This runs AFTER the agent produces a response, enriching it with display hints.
"""

import json
import re
from datetime import datetime
from typing import Optional

from app.agents.ollama_client import chat_completion
from app.config import settings

# ── Layout Types ──────────────────────────────────────────

LAYOUT_TYPES = {
    "chat": "Default conversational view — just show the message",
    "news_article": "News/article view — Perplexity-style layout with AI summary, hero image, full article, and citations",
    "calendar": "Calendar/schedule view — display events, reminders, appointments",
    "finance": "Financial dashboard — charts, budgets, expenses, summaries",
    "search_results": "Web search results — product cards, links, images, comparisons",
    "kanban": "Task board — columns with cards (todo/in-progress/done)",
    "data_table": "Structured data table — rows and columns of information",
    "document": "Document/article view — long-form content, reports, summaries",
    "map": "Map/location view — addresses, directions, nearby places",
    "code": "Code editor view — syntax-highlighted code with file tabs",
    "media_gallery": "Image/video gallery — grid of media items",
    "comparison": "Side-by-side comparison — products, plans, options",
    "timeline": "Timeline view — chronological events or project milestones",
    "form": "Input form — collect structured data from user",
    "email_inbox": "Email inbox view — list of emails with sender, subject, snippet, date, unread status",
    "dashboard": "Multi-widget dashboard — mixed cards, stats, charts",
}

LAYOUT_CLASSIFIER_PROMPT = """You are a UI layout classifier. Given a user's message and the AI assistant's response, determine the best visual layout to display the information.

Available layouts:
{layout_list}

Analyze the content and output ONLY a JSON object:
{{
  "layout": "<layout_type>",
  "title": "<short title for the view panel>",
  "reasoning": "<one sentence why>"
}}

Rules:
- Default to "chat" if the response is just conversational text with no structured data.
- Use "calendar" for ANY schedule, event, reminder, appointment, or time-based content.
- Use "finance" for budgets, expenses, income, financial summaries, or monetary data.
- Use "search_results" for web search results, product recommendations, or comparison shopping.
- Use "kanban" for task lists, project boards, or workflow tracking.
- Use "data_table" for tabular data, lists of items with properties, or structured records.
- Use "comparison" for side-by-side feature/price/option comparisons.
- Use "code" for code snippets, scripts, or technical output.
- Use "document" for long articles, reports, or multi-section content.
- Use "dashboard" for overview summaries mixing stats + lists + charts.
- Use "timeline" for chronological events or project milestones.
- ONLY choose a non-chat layout if there's actual structured data to display.
"""


def _build_layout_list() -> str:
    return "\n".join(f"- {k}: {v}" for k, v in LAYOUT_TYPES.items())


async def classify_layout(
    user_message: str,
    assistant_response: str,
    agent_name: str,
    tool_calls: list[dict] | None = None,
) -> dict:
    """
    Classify what layout the frontend should use to display this response.
    Returns: {"layout": "...", "title": "...", "data": {...}}
    """
    # Fast-path: short conversational responses → always chat
    if len(assistant_response) < 150 and not tool_calls:
        return {"layout": "chat", "title": "", "data": None}

    # Fast-path heuristics before calling the model
    layout = _heuristic_classify(user_message, assistant_response, agent_name, tool_calls)
    if layout:
        return layout

    # Use the small model for fast classification
    system_msg = LAYOUT_CLASSIFIER_PROMPT.format(layout_list=_build_layout_list())

    context = f"User: {user_message}\n\nAgent ({agent_name}) response:\n{assistant_response[:2000]}"
    if tool_calls:
        tools_used = ", ".join(tc.get("tool", "") for tc in tool_calls)
        context += f"\n\nTools used: {tools_used}"

    try:
        resp = await chat_completion(
            model=settings.MODEL_SMALL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": context},
            ],
            temperature=0.1,
        )
        content = resp.get("message", {}).get("content", "")
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]

        data = json.loads(content)
        layout_type = data.get("layout", "chat")
        if layout_type not in LAYOUT_TYPES:
            layout_type = "chat"

        return {
            "layout": layout_type,
            "title": data.get("title", ""),
            "data": _extract_structured_data(layout_type, assistant_response, tool_calls),
        }
    except Exception:
        return {"layout": "chat", "title": "", "data": None}


def _heuristic_classify(
    user_message: str,
    response: str,
    agent_name: str,
    tool_calls: list[dict] | None,
) -> Optional[dict]:
    """Quick keyword-based classification to avoid model calls for obvious cases."""
    msg_lower = user_message.lower()
    tools_used = {tc.get("tool", "") for tc in (tool_calls or [])}

    # News / Article — highest priority for researcher agent with news_search tool
    news_words = ["news", "article", "headline", "today", "latest", "breaking", "what happened",
                  "recent", "current events", "politics", "election", "sports score", "weather"]
    if (
        "news_search" in tools_used
        or (agent_name == "researcher" and any(w in msg_lower for w in news_words))
        or ("web_scrape" in tools_used and any(w in msg_lower for w in news_words))
    ):
        return {
            "layout": "news_article",
            "title": "News",
            "data": _extract_structured_data("news_article", response, tool_calls),
        }

    # Email / Gmail
    email_words = ["email", "emails", "inbox", "gmail", "unread", "mail", "messages from", "send email"]
    if (
        any(w in msg_lower for w in email_words)
        or any(t in tools_used for t in ("gmail_list", "gmail_read", "gmail_search"))
    ):
        return {
            "layout": "email_inbox",
            "title": "Email",
            "data": _extract_structured_data("email_inbox", response, tool_calls),
        }

    # Schedule / Calendar
    schedule_words = ["schedule", "calendar", "appointment", "meeting", "event", "reminder", "agenda", "plan my day", "plan my week"]
    if any(w in msg_lower for w in schedule_words) or "create_reminder" in tools_used:
        return {
            "layout": "calendar",
            "title": "Schedule",
            "data": _extract_structured_data("calendar", response, tool_calls),
        }

    # Finance
    finance_words = ["budget", "expense", "spending", "financial", "income", "money", "cost", "price", "investment", "savings"]
    if any(w in msg_lower for w in finance_words) or agent_name == "finance":
        return {
            "layout": "finance",
            "title": "Finances",
            "data": _extract_structured_data("finance", response, tool_calls),
        }

    # Web search / product search
    search_words = ["search for", "find me", "look up", "compare", "best deals", "buy", "shop", "product", "recommend"]
    if any(w in msg_lower for w in search_words) and "web_search" in tools_used:
        return {
            "layout": "search_results",
            "title": "Search Results",
            "data": _extract_structured_data("search_results", response, tool_calls),
        }

    # Code
    if agent_name == "coder" and ("```" in response):
        return {
            "layout": "code",
            "title": "Code",
            "data": _extract_structured_data("code", response, tool_calls),
        }

    # Task management
    task_words = ["task", "todo", "to-do", "project board", "kanban", "checklist", "track progress"]
    if any(w in msg_lower for w in task_words):
        return {
            "layout": "kanban",
            "title": "Tasks",
            "data": _extract_structured_data("kanban", response, tool_calls),
        }

    return None


def _extract_structured_data(
    layout_type: str,
    response: str,
    tool_calls: list[dict] | None,
) -> dict:
    """
    Extract structured data from the response text and tool results
    to populate the view component.
    """
    tool_results = {}
    for tc in (tool_calls or []):
        tool_name = tc.get("tool", "")
        result = tc.get("result", {})
        if tool_name not in tool_results:
            tool_results[tool_name] = []
        tool_results[tool_name].append(result)

    if layout_type == "news_article":
        return _extract_news_article_data(response, tool_results)
    elif layout_type == "calendar":
        return _extract_calendar_data(response, tool_results)
    elif layout_type == "finance":
        return _extract_finance_data(response, tool_results)
    elif layout_type == "search_results":
        return _extract_search_data(response, tool_results)
    elif layout_type == "code":
        return _extract_code_data(response)
    elif layout_type == "kanban":
        return _extract_kanban_data(response)
    elif layout_type == "comparison":
        return _extract_comparison_data(response)
    elif layout_type == "data_table":
        return _extract_table_data(response)
    elif layout_type == "dashboard":
        return _extract_dashboard_data(response, tool_results)
    elif layout_type == "timeline":
        return _extract_timeline_data(response)
    elif layout_type == "email_inbox":
        return _extract_email_data(response, tool_results)

    return {"raw_content": response}


# ── Data Extractors ───────────────────────────────────────

def _extract_calendar_data(response: str, tool_results: dict) -> dict:
    """Parse events/reminders from response text."""
    events = []

    # From reminder tool results
    for result in tool_results.get("create_reminder", []):
        if isinstance(result, dict) and result.get("status") == "created":
            events.append({
                "title": result.get("message", "Reminder"),
                "time": result.get("scheduled_for", ""),
                "type": "reminder",
                "recurring": result.get("recurring", False),
            })

    # Try to parse events from response text
    time_pattern = re.compile(
        r'(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*[-–:]\s*(.+?)(?:\n|$)'
    )
    for match in time_pattern.finditer(response):
        events.append({
            "title": match.group(2).strip(),
            "time": match.group(1).strip(),
            "type": "event",
        })

    return {
        "events": events,
        "view_mode": "week",  # day | week | month
        "today": datetime.now().strftime("%Y-%m-%d"),
    }


def _extract_finance_data(response: str, tool_results: dict) -> dict:
    """Parse financial data from response."""
    # Extract numbers/amounts from response
    amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', response)
    categories = []
    lines = response.split('\n')
    for line in lines:
        if ':' in line and '$' in line:
            parts = line.split(':')
            cat = parts[0].strip().strip('-•* ')
            amt_match = re.search(r'\$([\d,]+(?:\.\d{2})?)', parts[1])
            if amt_match and cat:
                categories.append({
                    "name": cat,
                    "amount": float(amt_match.group(1).replace(',', '')),
                })

    return {
        "categories": categories,
        "total_amounts": amounts,
        "summary": response[:300],
    }


def _extract_search_data(response: str, tool_results: dict) -> dict:
    """Parse search results from web_search tool output."""
    results = []
    for search_results in tool_results.get("web_search", []):
        if isinstance(search_results, dict):
            for item in search_results.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("snippet", item.get("content", "")),
                    "source": item.get("source", ""),
                })

    return {
        "results": results,
        "query": "",
    }


def _extract_code_data(response: str) -> dict:
    """Parse code blocks from response."""
    blocks = []
    pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    for match in pattern.finditer(response):
        blocks.append({
            "language": match.group(1) or "text",
            "code": match.group(2).strip(),
        })
    return {"blocks": blocks}


def _extract_kanban_data(response: str) -> dict:
    """Parse tasks into kanban columns."""
    columns = {
        "todo": [],
        "in_progress": [],
        "done": [],
    }
    current_col = "todo"
    for line in response.split('\n'):
        line_stripped = line.strip()
        lower = line_stripped.lower()
        if 'to do' in lower or 'todo' in lower or 'pending' in lower:
            current_col = "todo"
        elif 'in progress' in lower or 'ongoing' in lower or 'current' in lower:
            current_col = "in_progress"
        elif 'done' in lower or 'complete' in lower or 'finished' in lower:
            current_col = "done"
        elif line_stripped.startswith(('-', '•', '*', '✓', '☐', '☑')):
            task_text = line_stripped.lstrip('-•*✓☐☑ ').strip()
            if task_text:
                columns[current_col].append({"title": task_text})

    return {"columns": columns}


def _extract_comparison_data(response: str) -> dict:
    """Parse comparison tables from response."""
    return {"raw_content": response}


def _extract_table_data(response: str) -> dict:
    """Parse markdown tables from response."""
    headers = []
    rows = []
    in_table = False
    for line in response.split('\n'):
        stripped = line.strip()
        if '|' in stripped:
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if not in_table:
                headers = cells
                in_table = True
            elif all(set(c) <= {'-', ':', ' '} for c in cells):
                continue  # separator row
            else:
                rows.append(cells)
        else:
            if in_table and stripped == '':
                break
    return {"headers": headers, "rows": rows}


def _extract_dashboard_data(response: str, tool_results: dict) -> dict:
    """Extract mixed dashboard widgets."""
    return {
        "widgets": [
            {"type": "text", "content": response[:500]},
        ]
    }


def _extract_timeline_data(response: str) -> dict:
    """Parse timeline/milestone events."""
    events = []
    date_pattern = re.compile(
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\w+ \d{1,2},?\s*\d{4}?)\s*[-–:]\s*(.+?)(?:\n|$)'
    )
    for match in date_pattern.finditer(response):
        events.append({
            "date": match.group(1).strip(),
            "title": match.group(2).strip(),
        })
    return {"events": events}


def _extract_news_article_data(response: str, tool_results: dict) -> dict:
    """
    Extracts Perplexity-style article data from web_scrape + news_search tool results.

    Returns:
      {
        "ai_summary": str,          # Model's synthesized text
        "article": {...},           # Top scraped article metadata
        "citations": [...],         # All sources referenced
        "related": [...],           # Additional search results
      }
    """
    # Pull the primary scraped article
    article = None
    for scraped in tool_results.get("web_scrape", []):
        if isinstance(scraped, dict) and scraped.get("content"):
            article = scraped
            break

    # Compile citations from all search result tools
    citations = []
    for tool_name in ("news_search", "web_search"):
        for result_batch in tool_results.get(tool_name, []):
            if isinstance(result_batch, dict):
                for r in result_batch.get("results", []):
                    citations.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "source": r.get("source", r.get("hostname", "")),
                        "published_date": r.get("published_date", ""),
                        "snippet": r.get("snippet", ""),
                    })

    # Related results = remaining citations (after the first one)
    related = citations[1:6] if len(citations) > 1 else []

    return {
        "ai_summary": response,
        "article": article,
        "citations": citations[:8],
        "related": related,
    }


def _extract_email_data(response: str, tool_results: dict) -> dict:
    """Extract email data from gmail tool results."""
    emails = []
    for result_batch in tool_results.get("gmail_list", []) + tool_results.get("gmail_search", []):
        if isinstance(result_batch, dict):
            for e in result_batch.get("emails", []):
                emails.append(e)

    # Deduplicate by email id
    seen = set()
    unique = []
    for e in emails:
        eid = e.get("id", "")
        if eid and eid not in seen:
            seen.add(eid)
            unique.append(e)

    return {
        "ai_summary": response,
        "emails": unique,
        "total": len(unique),
    }
