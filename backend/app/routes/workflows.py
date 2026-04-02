"""
Workflow routes — list, create, and manage custom workflows.
"""

from fastapi import APIRouter

from app.workflows import WORKFLOWS

router = APIRouter()


@router.get("")
async def list_workflows():
    """List all registered workflows with their metadata."""
    return [
        {
            "id": wf.id,
            "name": wf.name,
            "description": wf.description,
            "category": wf.category,
            "trigger_keywords": wf.trigger_keywords,
            "output_layout": wf.output_layout,
            "steps": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.type.value,
                    "description": s.description,
                }
                for s in wf.steps
            ],
        }
        for wf in WORKFLOWS.values()
    ]


@router.get("/layouts")
async def list_layouts():
    """List all available layout types."""
    from app.agents.layout_engine import LAYOUT_TYPES
    return LAYOUT_TYPES
