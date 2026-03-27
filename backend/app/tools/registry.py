"""
Tool registry — defines the schema for each tool so models can call them.
"""

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict          # JSON Schema for parameters
    handler: str              # dotted path to async handler function

    def to_ollama_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


TOOLS: dict[str, ToolSpec] = {}


def register_tool(spec: ToolSpec):
    TOOLS[spec.name] = spec


# ══════════════════════════════════════════════════════════
# Tool Definitions
# ══════════════════════════════════════════════════════════

register_tool(ToolSpec(
    name="web_search",
    description="Search the web for current information. Returns a list of results with titles, URLs, and snippets.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
        },
        "required": ["query"],
    },
    handler="app.tools.web.search",
))

register_tool(ToolSpec(
    name="web_scrape",
    description="Fetch and extract the main text content from a web page URL.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to scrape"},
        },
        "required": ["url"],
    },
    handler="app.tools.web.scrape",
))

register_tool(ToolSpec(
    name="memory_search",
    description="Search your memory for information you previously learned about the user.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for"},
            "category": {"type": "string", "description": "Optional category filter: preference, fact, event, person, finance"},
        },
        "required": ["query"],
    },
    handler="app.tools.memory_tools.search",
))

register_tool(ToolSpec(
    name="memory_store",
    description="Store an important fact, preference, or context about the user for future reference.",
    parameters={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "What to remember"},
            "category": {"type": "string", "description": "Category: preference, fact, event, person, finance"},
            "importance": {"type": "number", "description": "Importance 0.0-1.0 (default 0.5)"},
        },
        "required": ["content", "category"],
    },
    handler="app.tools.memory_tools.store",
))

register_tool(ToolSpec(
    name="calculator",
    description="Evaluate a mathematical expression safely. Supports basic arithmetic, percentages, and common math functions.",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Math expression to evaluate (e.g., '1500 * 0.3')"},
        },
        "required": ["expression"],
    },
    handler="app.tools.calculator.evaluate",
))

register_tool(ToolSpec(
    name="create_reminder",
    description="Set a reminder for the user at a specific date/time.",
    parameters={
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "Reminder message"},
            "trigger_at": {"type": "string", "description": "ISO datetime string (e.g., '2026-03-27T15:00:00')"},
            "recurring": {"type": "string", "description": "Optional: daily, weekly, monthly"},
        },
        "required": ["message", "trigger_at"],
    },
    handler="app.tools.reminder_tools.create",
))

register_tool(ToolSpec(
    name="file_read",
    description="Read the contents of a local file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to read"},
        },
        "required": ["path"],
    },
    handler="app.tools.filesystem.read_file",
))

register_tool(ToolSpec(
    name="file_write",
    description="Write content to a local file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path to write"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
    handler="app.tools.filesystem.write_file",
))

register_tool(ToolSpec(
    name="run_command",
    description="Execute a shell command and return its output. Use carefully.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to run"},
            "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
        },
        "required": ["command"],
    },
    handler="app.tools.shell.run_command",
))
