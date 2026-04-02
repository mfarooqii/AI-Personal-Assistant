"""
Agent executor — takes a routed agent spec and runs the conversation
with the appropriate model, tools, and system prompt.

Supports two execution modes automatically:
  1. Native tool calling  — for models that support it (llama3.2, qwen2.5-coder, phi4-mini …)
  2. ReAct text parsing   — fallback for models that don't (deepseek-r1, …)
     The model is instructed to emit <tool_call>{…}</tool_call> tags in its text;
     we parse them, execute the tools, and feed results back.
"""

import re
import json
from datetime import datetime
from typing import AsyncIterator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.agents.ollama_client import chat_completion, chat_stream, ModelUnavailableError
from app.agents.registry import AgentSpec
from app.tools.executor import execute_tool_call
from app.memory.manager import MemoryManager
from app.config import settings

# Agents that benefit from pre-retrieval (search BEFORE model generates)
_RETRIEVAL_AGENTS = {"researcher", "general", "planner"}

# Models that don't support Ollama native function/tool calling — ReAct fallback used.
# Add model name prefixes here if you hit 400 errors with a new model.
MODELS_WITHOUT_NATIVE_TOOLS: set[str] = {
    "qwen3.5",
    "qwen3.5:latest",
    "qwen3.5-max",
    "qwen3.5-max:latest",
}

# ReAct tag pattern: <tool_call>{"name": "...", "arguments": {...}}</tool_call>
_TC_RE = re.compile(r"<tool_call>\s*(\{.*?\})\s*</tool_call>", re.DOTALL)

REACT_TOOL_INSTRUCTIONS = """
You have access to tools. To use a tool, output EXACTLY this format on its own line:
<tool_call>{{"name": "<tool_name>", "arguments": {{<args as JSON>}}}}</tool_call>

After receiving the tool result, continue reasoning. Call more tools if needed.
When you have enough information, provide your final answer in plain text WITHOUT any tool_call tags.

Available tools:
{tool_list}
"""


def _resolve_model(model_key: str) -> str:
    return getattr(settings, model_key, settings.MODEL_CHAT)


def _uses_native_tools(model: str) -> bool:
    """Return False if we know this model can't do native tool calling."""
    normalized = model.lower().strip()
    return not any(normalized.startswith(blocked.lower()) for blocked in MODELS_WITHOUT_NATIVE_TOOLS)


def _build_tool_list_text(agent: AgentSpec) -> str:
    from app.tools.registry import TOOLS
    lines = []
    for name in agent.tools:
        if name in TOOLS:
            spec = TOOLS[name]
            params = spec.parameters.get("properties", {})
            required = spec.parameters.get("required", [])
            param_names = [f"{k}{'*' if k in required else ''}" for k in params]
            lines.append(f"- {name}({', '.join(param_names)}): {spec.description}")
    return "\n".join(lines)


def _parse_react_tool_calls(text: str) -> list[dict]:
    """Extract <tool_call>…</tool_call> JSON blocks from model text."""
    calls = []
    for match in _TC_RE.finditer(text):
        try:
            data = json.loads(match.group(1))
            name = data.get("name", "")
            args = data.get("arguments", {})
            if name:
                calls.append({"name": name, "arguments": args})
        except json.JSONDecodeError:
            pass
    return calls


def _strip_react_tags(text: str) -> str:
    """Remove leftover tool_call tags from final response text."""
    return _TC_RE.sub("", text).strip()


async def _build_context(
    agent: AgentSpec,
    user_message: str,
    conversation_history: list[dict],
    db: AsyncSession,
    react_mode: bool = False,
    grounding_prompt: str = "",
) -> list[dict]:
    """Build the full message list with system prompt, memory context, and history."""
    memories = await MemoryManager.search(db, user_message, limit=5)
    memory_text = ""
    if memories:
        memory_text = "\n\nRelevant things you remember about the user:\n"
        for m in memories:
            memory_text += f"- [{m['category']}] {m['content']}\n"

    system_prompt = agent.system_prompt.format(name=settings.APP_NAME) + memory_text
    system_prompt += f"\n\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M %Z')}"

    # Inject pre-retrieved web content so the model synthesizes from real data
    if grounding_prompt:
        system_prompt += grounding_prompt

    if react_mode and agent.tools:
        tool_list = _build_tool_list_text(agent)
        system_prompt += REACT_TOOL_INSTRUCTIONS.format(tool_list=tool_list)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history[-20:])
    messages.append({"role": "user", "content": user_message})
    return messages


def _build_tools_schema(agent: AgentSpec) -> Optional[list[dict]]:
    """Convert agent's tool list into Ollama native tool-calling format."""
    from app.tools.registry import TOOLS
    if not agent.tools:
        return None
    return [TOOLS[n].to_ollama_schema() for n in agent.tools if n in TOOLS] or None


# ── Native tool-calling execution ────────────────────────

async def _run_native(
    model: str,
    agent: AgentSpec,
    messages: list[dict],
    tools_schema: list[dict],
    db: AsyncSession,
) -> dict:
    max_rounds = 5
    tool_calls_made = []

    for _ in range(max_rounds):
        resp = await chat_completion(model, messages, tools=tools_schema)
        msg = resp.get("message", {})

        if msg.get("tool_calls"):
            messages.append(msg)
            for tc in msg["tool_calls"]:
                fn_name = tc["function"]["name"]
                fn_args = tc["function"]["arguments"]
                tool_result = await execute_tool_call(fn_name, fn_args, db)
                tool_calls_made.append({"tool": fn_name, "args": fn_args, "result": tool_result})
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result),
                })
            continue

        return {
            "content": msg.get("content", ""),
            "model": model,
            "agent": agent.name,
            "tool_calls": tool_calls_made or None,
        }

    return {
        "content": msg.get("content", ""),
        "model": model,
        "agent": agent.name,
        "tool_calls": tool_calls_made or None,
    }


# ── ReAct fallback execution ─────────────────────────────

async def _run_react(
    model: str,
    agent: AgentSpec,
    messages: list[dict],
    db: AsyncSession,
) -> dict:
    """ReAct (Reasoning + Acting) loop — works with any model, including deepseek-r1."""
    max_rounds = 6
    tool_calls_made = []

    for _ in range(max_rounds):
        resp = await chat_completion(model, messages, tools=None)
        msg = resp.get("message", {})
        text = msg.get("content", "")

        calls = _parse_react_tool_calls(text)

        if not calls:
            # No tool calls in this turn — final answer
            return {
                "content": _strip_react_tags(text),
                "model": model,
                "agent": agent.name,
                "tool_calls": tool_calls_made or None,
            }

        # Keep the assistant turn with its tool_call tags
        messages.append({"role": "assistant", "content": text})

        # Execute each tool and inject result as a user message
        for call in calls:
            fn_name = call["name"]
            fn_args = call["arguments"]
            tool_result = await execute_tool_call(fn_name, fn_args, db)
            tool_calls_made.append({"tool": fn_name, "args": fn_args, "result": tool_result})
            result_text = (
                json.dumps(tool_result, indent=2)
                if isinstance(tool_result, dict)
                else str(tool_result)
            )
            messages.append({
                "role": "user",
                "content": f"Tool result for `{fn_name}`:\n{result_text}\n\nNow continue."
            })

    return {
        "content": _strip_react_tags(messages[-1].get("content", "")),
        "model": model,
        "agent": agent.name,
        "tool_calls": tool_calls_made or None,
    }


# ── Public API ───────────────────────────────────────────

async def run(
    agent: AgentSpec,
    user_message: str,
    conversation_history: list[dict],
    db: AsyncSession,
) -> dict:
    """Execute agent — auto-selects native or ReAct mode based on model capability."""
    model = _resolve_model(agent.model_key)
    tools_schema = _build_tools_schema(agent)

    # ── Pre-Retrieval (Perplexity-style RAG) ─────────────────────────────────
    # For research/news agents, fetch real web content BEFORE the model responds.
    # This guarantees fresh data even if the model would skip tool calls.
    retrieval_ctx = None
    extra_tool_calls: list[dict] = []
    grounding_prompt = ""

    if agent.name in _RETRIEVAL_AGENTS:
        try:
            from app.agents.retrieval import pre_retrieve
            retrieval_ctx = await pre_retrieve(user_message, db)
        except Exception:
            retrieval_ctx = None

    if retrieval_ctx:
        grounding_prompt = retrieval_ctx.get("grounding_prompt", "")
        # Surface search results as virtual tool_calls so the layout engine sees them
        if retrieval_ctx.get("search_results"):
            extra_tool_calls.append({
                "tool": "news_search" if retrieval_ctx.get("query_type") == "news" else "web_search",
                "args": {"query": retrieval_ctx.get("query", "")},
                "result": {"results": retrieval_ctx["search_results"]},
            })
        for article in retrieval_ctx.get("articles", []):
            extra_tool_calls.append({
                "tool": "web_scrape",
                "args": {"url": article.get("url", "")},
                "result": article,
            })

    # No tools needed — plain chat
    if not tools_schema:
        messages = await _build_context(
            agent, user_message, conversation_history, db,
            grounding_prompt=grounding_prompt,
        )
        try:
            resp = await chat_completion(model, messages)
        except ModelUnavailableError:
            model = settings.MODEL_CHAT
            messages = await _build_context(
                agent, user_message, conversation_history, db,
                grounding_prompt=grounding_prompt,
            )
            resp = await chat_completion(model, messages)
        return {
            "content": resp.get("message", {}).get("content", ""),
            "model": model,
            "agent": agent.name,
            "tool_calls": extra_tool_calls or None,
        }

    if _uses_native_tools(model):
        messages = await _build_context(
            agent, user_message, conversation_history, db,
            react_mode=False, grounding_prompt=grounding_prompt,
        )
        try:
            result = await _run_native(model, agent, messages, tools_schema, db)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                MODELS_WITHOUT_NATIVE_TOOLS.add(model)
            else:
                raise
        except ModelUnavailableError:
            model = settings.MODEL_CHAT
            messages = await _build_context(
                agent, user_message, conversation_history, db,
                react_mode=False, grounding_prompt=grounding_prompt,
            )
            result = await _run_native(model, agent, messages, tools_schema, db)
        else:
            # Merge pre-fetch results with any tool calls the model made
            existing = result.get("tool_calls") or []
            result["tool_calls"] = (extra_tool_calls + existing) or None
            return result

    # ReAct mode
    messages = await _build_context(
        agent, user_message, conversation_history, db,
        react_mode=True, grounding_prompt=grounding_prompt,
    )
    try:
        result = await _run_react(model, agent, messages, db)
    except ModelUnavailableError:
        model = settings.MODEL_CHAT
        messages = await _build_context(
            agent, user_message, conversation_history, db,
            react_mode=False, grounding_prompt=grounding_prompt,
        )
        result = await _run_native(model, agent, messages, tools_schema, db)

    existing = result.get("tool_calls") or []
    result["tool_calls"] = (extra_tool_calls + existing) or None
    return result


async def run_stream(
    agent: AgentSpec,
    user_message: str,
    conversation_history: list[dict],
    db: AsyncSession,
) -> AsyncIterator[str]:
    """Streaming version — yields tokens. No tool calling (used for voice/quick chat)."""
    model = _resolve_model(agent.model_key)
    messages = await _build_context(agent, user_message, conversation_history, db)
    async for token in chat_stream(model, messages):
        yield token
