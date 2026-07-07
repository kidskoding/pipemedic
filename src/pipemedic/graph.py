"""LangGraph StateGraph wiring: collect -> agent -> validate -> publish/retry/escalate."""

from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from pipemedic.agent import propose_fix as _propose_fix
from pipemedic.collector import collect as _collect
from pipemedic.config import Settings
from pipemedic.models import FailureContext, Fix, ValidationResult
from pipemedic.publisher import open_pr as _open_pr
from pipemedic.validator import validate as _validate


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


def _route_after_agent(state: MedicState) -> str:
    if state.fix and state.fix.root_cause.startswith("ESCALATE:"):
        return "escalate"
    return "validate"


def _route_after_validate(state: MedicState) -> str:
    if state.validation and state.validation.passed:
        return "publish"
    if state.attempts < state.max_retries:
        return "agent"
    return "escalate"


def build_graph(settings: Settings):
    def collect_node(state: MedicState) -> dict:
        return {"context": _collect(state.project_dir, state.model_name)}

    def agent_node(state: MedicState) -> dict:
        return {"fix": _propose_fix(state.context, state.project_dir, settings)}

    def validate_node(state: MedicState) -> dict:
        result = _validate(state.fix, state.project_dir, state.model_name, settings)
        update: dict = {"validation": result, "attempts": state.attempts + 1}
        if not result.passed:
            ctx = state.context.model_copy()
            ctx.prior_attempts = ctx.prior_attempts + [result.logs]
            update["context"] = ctx
        return update

    def publish_node(state: MedicState) -> dict:
        url = _open_pr(state.fix, state.validation, state.model_name, settings)
        return {"pr_url": url}

    def escalate_node(state: MedicState) -> dict:
        # ponytail: escalation = log + no PR; notification hook is v2
        reason = f" — {state.fix.root_cause}" if state.fix and state.fix.root_cause else ""
        print(f"pipemedic: escalating {state.model_name} after {state.attempts} attempts{reason}")
        return {}

    g = StateGraph(MedicState)
    g.add_node("collect", collect_node)
    g.add_node("agent", agent_node)
    g.add_node("validate", validate_node)
    g.add_node("publish", publish_node)
    g.add_node("escalate", escalate_node)
    g.set_entry_point("collect")
    g.add_edge("collect", "agent")
    g.add_conditional_edges("agent", _route_after_agent)
    g.add_conditional_edges("validate", _route_after_validate)
    g.add_edge("publish", END)
    g.add_edge("escalate", END)
    return g.compile()


def run_fix(project_dir: str, model_name: str, settings: Settings) -> MedicState:
    app = build_graph(settings)
    final = app.invoke(
        MedicState(project_dir=project_dir, model_name=model_name, max_retries=settings.max_retries),
        {"recursion_limit": 50},
    )
    return MedicState(**final)
