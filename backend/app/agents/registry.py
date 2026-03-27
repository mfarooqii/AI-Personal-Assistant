"""
Agent definitions — each agent specializes in a domain and knows which
model + tools to use. The Router picks the best agent for each task.
"""

from dataclasses import dataclass, field


@dataclass
class AgentSpec:
    name: str
    description: str
    model_key: str                      # key in settings (MODEL_CHAT, MODEL_REASONING, etc.)
    tools: list[str] = field(default_factory=list)
    system_prompt: str = ""


# ── Agent Registry ───────────────────────────────────────

AGENTS: dict[str, AgentSpec] = {}


def register(agent: AgentSpec):
    AGENTS[agent.name] = agent
    return agent


# ── Built-in Agents ─────────────────────────────────────

register(AgentSpec(
    name="general",
    description="Friendly conversation, general Q&A, small talk, daily chitchat.",
    model_key="MODEL_CHAT",
    tools=["memory_search", "memory_store"],
    system_prompt=(
        "You are {name}, a warm and helpful personal AI assistant. "
        "You remember important things about the user and bring them up naturally. "
        "Be concise but personable — like a smart friend who is always there to help."
    ),
))

register(AgentSpec(
    name="researcher",
    description="Web search, news lookup, product comparison, deal finding, flight/hotel search.",
    model_key="MODEL_REASONING",
    tools=["web_search", "web_scrape", "memory_search", "memory_store"],
    system_prompt=(
        "You are {name}'s research agent. Your job is to search the web, "
        "compare options, and present clear, structured findings. "
        "Always cite sources. Present data in tables when comparing items."
    ),
))

register(AgentSpec(
    name="planner",
    description="Complex multi-step planning, trip planning, scheduling, task decomposition.",
    model_key="MODEL_REASONING",
    tools=["web_search", "memory_search", "memory_store", "create_reminder", "file_write"],
    system_prompt=(
        "You are {name}'s planning agent. Break complex requests into clear steps. "
        "Create actionable plans, timelines, and checklists. Think step by step."
    ),
))

register(AgentSpec(
    name="finance",
    description="Budget tracking, expense analysis, financial advice, deal comparison.",
    model_key="MODEL_REASONING",
    tools=["memory_search", "memory_store", "calculator", "web_search"],
    system_prompt=(
        "You are {name}'s finance assistant. Help track budgets, analyze spending, "
        "and give practical financial advice. Be precise with numbers. "
        "Always consider the user's monthly budget context."
    ),
))

register(AgentSpec(
    name="health",
    description="Recipes, diet plans, exercise schedules, nutrition info, meal planning.",
    model_key="MODEL_CHAT",
    tools=["web_search", "memory_search", "memory_store"],
    system_prompt=(
        "You are {name}'s health & wellness assistant. Provide recipes, diet plans, "
        "and exercise routines. Always respect dietary restrictions and preferences. "
        "Be encouraging and practical."
    ),
))

register(AgentSpec(
    name="coder",
    description="Code generation, debugging, technical questions, command execution.",
    model_key="MODEL_CODE",
    tools=["file_read", "file_write", "run_command", "web_search"],
    system_prompt=(
        "You are {name}'s coding assistant. Write clean, well-structured code. "
        "Explain your approach when asked. Default to Python unless specified."
    ),
))

register(AgentSpec(
    name="writer",
    description="Summarization, writing, editing, formatting, content creation.",
    model_key="MODEL_CHAT",
    tools=["web_search", "memory_search", "file_write"],
    system_prompt=(
        "You are {name}'s writing assistant. Help draft, edit, and format text. "
        "Match the requested tone and style. Be creative when appropriate."
    ),
))
