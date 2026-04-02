"""
Workflow Executor — runs a workflow step-by-step, building context
and producing a final result with layout directives.
"""

import json
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflows import Workflow, WorkflowStep, StepType, find_workflow
from app.agents.registry import AGENTS
from app.agents.executor import run as run_agent
from app.tools.executor import execute_tool_call


async def execute_workflow(
    workflow: Workflow,
    user_message: str,
    conversation_history: list[dict],
    db: AsyncSession,
) -> dict:
    """
    Execute a workflow end-to-end, returning the final result
    with content, layout directive, and all intermediate data.
    """
    context: dict[str, Any] = {
        "user_message": user_message,
    }
    all_tool_calls = []
    final_content = ""
    final_layout = {"layout": workflow.output_layout, "title": workflow.name, "data": {}}

    step = workflow.first_step
    max_steps = 20  # safety limit

    for _ in range(max_steps):
        if step is None:
            break

        result = await _execute_step(step, context, conversation_history, db)

        # Store result in context
        if step.output_key and result.get("output"):
            context[step.output_key] = result["output"]

        # Collect tool calls
        if result.get("tool_calls"):
            all_tool_calls.extend(result["tool_calls"])

        # Track content from agent steps
        if result.get("content"):
            final_content = result["content"]

        # Handle layout steps
        if step.type == StepType.LAYOUT:
            final_layout = {
                "layout": step.layout_type or workflow.output_layout,
                "title": step.layout_title or workflow.name,
                "data": _build_layout_data(step.layout_type, context),
            }

        # Determine next step
        next_step_id = result.get("next_step", step.next_step)
        step = workflow.get_step(next_step_id) if next_step_id else None

    return {
        "content": final_content,
        "agent": f"workflow:{workflow.id}",
        "model": "multi-agent",
        "tool_calls": all_tool_calls or None,
        "layout": final_layout,
        "workflow_context": {k: _summarize(v) for k, v in context.items()},
    }


async def _execute_step(
    step: WorkflowStep,
    context: dict,
    conversation_history: list[dict],
    db: AsyncSession,
) -> dict:
    """Execute a single workflow step."""

    if step.type == StepType.AGENT:
        return await _execute_agent_step(step, context, conversation_history, db)
    elif step.type == StepType.TOOL:
        return await _execute_tool_step(step, context, db)
    elif step.type == StepType.CONDITION:
        return _execute_condition_step(step, context)
    elif step.type == StepType.LAYOUT:
        return {"output": None, "next_step": step.next_step}
    elif step.type == StepType.TRANSFORM:
        return await _execute_transform_step(step, context)
    else:
        return {"output": None, "next_step": step.next_step}


async def _execute_agent_step(
    step: WorkflowStep,
    context: dict,
    conversation_history: list[dict],
    db: AsyncSession,
) -> dict:
    """Run an agent with a templated prompt."""
    agent_name = step.agent_name or "general"
    agent = AGENTS.get(agent_name, AGENTS["general"])

    # Build the prompt from template
    prompt = step.prompt_template or "{user_message}"
    try:
        prompt = prompt.format(**{k: _summarize(v) for k, v in context.items()})
    except KeyError:
        prompt = prompt.format_map(SafeDict(context))

    result = await run_agent(agent, prompt, conversation_history, db)

    return {
        "content": result.get("content", ""),
        "output": result.get("content", ""),
        "tool_calls": result.get("tool_calls"),
        "next_step": step.next_step,
    }


async def _execute_tool_step(
    step: WorkflowStep,
    context: dict,
    db: AsyncSession,
) -> dict:
    """Execute a tool directly."""
    tool_name = step.tool_name
    args = dict(step.tool_args or {})

    # Template args from context
    for k, v in args.items():
        if isinstance(v, str) and '{' in v:
            try:
                args[k] = v.format(**context)
            except KeyError:
                pass

    result = await execute_tool_call(tool_name, args, db)

    return {
        "output": result,
        "tool_calls": [{"tool": tool_name, "args": args, "result": result}],
        "next_step": step.next_step,
    }


def _execute_condition_step(
    step: WorkflowStep,
    context: dict,
) -> dict:
    """Evaluate a condition and branch."""
    try:
        # Only allow safe attribute access, no builtins
        result = bool(eval(step.condition or "False", {"__builtins__": {}}, context))  # noqa: S307
    except Exception:
        result = False

    next_step = step.if_true if result else step.if_false
    return {"output": result, "next_step": next_step}


async def _execute_transform_step(
    step: WorkflowStep,
    context: dict,
) -> dict:
    """Apply a transform function to context data."""
    if not step.transform_fn:
        return {"output": None, "next_step": step.next_step}

    try:
        module_path, fn_name = step.transform_fn.rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_path)
        fn = getattr(mod, fn_name)
        result = fn(context) if not callable(getattr(fn, '__await__', None)) else await fn(context)
    except Exception:
        result = None

    return {"output": result, "next_step": step.next_step}


def _build_layout_data(layout_type: str | None, context: dict) -> dict:
    """Build layout-specific data from the workflow context."""
    if not layout_type:
        return {}

    # Pass through relevant context keys as layout data
    data = {}
    for key, value in context.items():
        if key != "user_message" and isinstance(value, (str, dict, list)):
            data[key] = _summarize(value) if isinstance(value, str) else value
    return data


def _summarize(value: Any) -> str:
    """Truncate long values for use in prompt templates."""
    if isinstance(value, str):
        return value[:3000] if len(value) > 3000 else value
    if isinstance(value, dict):
        return json.dumps(value, indent=2)[:3000]
    if isinstance(value, list):
        return json.dumps(value, indent=2)[:3000]
    return str(value)[:3000]


class SafeDict(dict):
    """Dict that returns the key name for missing format keys."""
    def __missing__(self, key):
        return f"{{{key}}}"
