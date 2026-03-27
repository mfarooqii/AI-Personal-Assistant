"""
Tool executor — dynamically imports and calls the tool handler by dotted path.
"""

import importlib
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.registry import TOOLS


async def execute_tool_call(tool_name: str, arguments: dict, db: AsyncSession) -> Any:
    """Execute a tool by name with given arguments."""
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    spec = TOOLS[tool_name]

    try:
        # Import the handler dynamically
        module_path, func_name = spec.handler.rsplit(".", 1)
        module = importlib.import_module(module_path)
        handler = getattr(module, func_name)

        # Memory tools need db session
        if tool_name.startswith("memory_") or tool_name == "create_reminder":
            return await handler(db=db, **arguments)
        else:
            return await handler(**arguments)

    except Exception as e:
        return {"error": f"Tool '{tool_name}' failed: {str(e)}"}
