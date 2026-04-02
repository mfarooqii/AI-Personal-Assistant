"""
Workflow transform functions — convert data between workflow steps.
"""

from typing import Any


def plan_to_kanban(context: dict) -> dict:
    """Convert a planner agent's output into kanban board structure."""
    plan_text = context.get("project_plan", "")
    columns = {
        "todo": [],
        "in_progress": [],
        "done": [],
    }

    current_col = "todo"
    for line in plan_text.split('\n'):
        stripped = line.strip()
        lower = stripped.lower()

        if any(w in lower for w in ['to do', 'todo', 'pending', 'backlog', 'upcoming']):
            current_col = "todo"
        elif any(w in lower for w in ['in progress', 'ongoing', 'current', 'active']):
            current_col = "in_progress"
        elif any(w in lower for w in ['done', 'complete', 'finished', 'delivered']):
            current_col = "done"
        elif stripped.startswith(('-', '•', '*', '✓', '☐', '☑')) or (stripped and stripped[0].isdigit() and '.' in stripped[:4]):
            task_text = stripped.lstrip('-•*✓☐☑0123456789. ').strip()
            if task_text:
                columns[current_col].append({
                    "title": task_text,
                    "priority": _guess_priority(task_text),
                })

    return columns


def _guess_priority(text: str) -> str:
    """Guess task priority from text keywords."""
    lower = text.lower()
    if any(w in lower for w in ['urgent', 'critical', 'asap', 'blocker']):
        return "high"
    if any(w in lower for w in ['important', 'key', 'major']):
        return "medium"
    return "normal"
