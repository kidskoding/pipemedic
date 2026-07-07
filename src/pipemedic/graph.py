"""LangGraph StateGraph wiring: collect -> agent -> validate -> publish/retry/escalate."""

from langgraph.graph import StateGraph
from pydantic import BaseModel

from pipemedic.models import FailureContext, Fix, ValidationResult


class MedicState(BaseModel):
    """Graph state threaded through every node."""

    project_dir: str
    model_name: str
    context: FailureContext | None = None
    fix: Fix | None = None
    validation: ValidationResult | None = None
    attempts: int = 0
    max_retries: int = 3
    pr_url: str | None = None


def _route_after_validate(state: MedicState) -> str:
    if state.validation and state.validation.passed:
        return "publish"
    if state.attempts < state.max_retries:
        return "agent"
    return "escalate"


def build_graph() -> StateGraph:
    """Wire the nodes; node implementations live in their own modules."""
    from pipemedic import agent, collector, publisher, validator  # noqa: F401

    # ponytail: node fns not implemented yet — wired when modules land (Task 8)
    raise NotImplementedError
