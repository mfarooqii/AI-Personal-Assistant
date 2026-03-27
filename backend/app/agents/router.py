"""
Agent Router — analyzes each user message and routes it to the best agent.
Uses the small/fast model for classification to keep latency low.
"""

import json
from app.agents.ollama_client import chat_completion
from app.agents.registry import AGENTS, AgentSpec
from app.config import settings

ROUTER_PROMPT = """You are a task router. Given the user's message, decide which specialist agent should handle it.

Available agents:
{agent_list}

Respond with ONLY a JSON object:
{{"agent": "<agent_name>", "reasoning": "<one sentence why>"}}

Rules:
- Pick the MOST specific agent that fits.
- If unsure, pick "general".
- For multi-step tasks involving web lookup, prefer "researcher" or "planner".
- For budget/money questions, prefer "finance".
- For recipes/diet/exercise, prefer "health".
"""


def _build_agent_list() -> str:
    lines = []
    for name, spec in AGENTS.items():
        lines.append(f"- {name}: {spec.description}")
    return "\n".join(lines)


async def route(user_message: str, conversation_history: list[dict] | None = None) -> AgentSpec:
    """Determine which agent should handle this message."""
    agent_list = _build_agent_list()
    system_msg = ROUTER_PROMPT.format(agent_list=agent_list)

    messages = [
        {"role": "system", "content": system_msg},
    ]

    # Include last few messages for context
    if conversation_history:
        for msg in conversation_history[-4:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_message})

    try:
        resp = await chat_completion(
            model=settings.MODEL_SMALL,
            messages=messages,
            temperature=0.1,
        )
        content = resp.get("message", {}).get("content", "")
        # Parse JSON from response
        # Handle potential markdown wrapping
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1].rsplit("```", 1)[0]
        data = json.loads(content)
        agent_name = data.get("agent", "general")
        if agent_name in AGENTS:
            return AGENTS[agent_name]
    except Exception:
        pass

    return AGENTS["general"]
