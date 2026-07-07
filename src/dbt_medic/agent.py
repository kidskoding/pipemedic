"""Agent node: ChatAnthropic + tools loop. FailureContext -> Fix."""

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from dbt_medic import tools
from dbt_medic.config import Settings
from dbt_medic.models import FailureContext, FileEdit, Fix

MAX_TURNS = 30

SYSTEM = """You are dbt-medic, an autonomous data engineer fixing a failed dbt model.

Investigate with your tools (read_file, get_schema, run_sql), then stage the
minimal fix with edit_file and finish by calling submit_fix with your
root-cause analysis. Rules:
- Fix the root cause, not the symptom. Prefer the smallest correct edit.
- Only edit files in the dbt project (model SQL, schema.yml, sources.yml).
- If the failure needs business-logic judgment you cannot verify, do NOT guess:
  call submit_fix with root_cause starting with "ESCALATE:" and no edits.
"""


class AgentError(Exception):
    pass


def _make_llm(settings: Settings):
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-sonnet-5", api_key=settings.anthropic_api_key)
    return llm.bind_tools(tools.ALL_TOOLS)


def _render(context: FailureContext) -> str:
    parts = [
        f"Failed model: {context.model_name}",
        f"Error:\n{context.error_message}",
    ]
    if context.raw_sql:
        parts.append(f"Model SQL (raw):\n{context.raw_sql}")
    if context.compiled_sql:
        parts.append(f"Compiled SQL:\n{context.compiled_sql}")
    if context.upstream_models:
        parts.append("Upstream: " + ", ".join(context.upstream_models))
    if context.source_schema:
        cols = "\n".join(f"  {c}: {t}" for c, t in context.source_schema.items())
        parts.append(f"Documented source schema:\n{cols}")
    if context.prior_attempts:
        attempts = "\n---\n".join(context.prior_attempts)
        parts.append(f"PRIOR FIX ATTEMPTS FAILED VALIDATION with:\n{attempts}")
    return "\n\n".join(parts)


_EXECUTABLE = {"read_file", "get_schema", "run_sql", "edit_file"}


def propose_fix(context: FailureContext, project_dir: str, settings: Settings) -> Fix:
    tools.configure(project_dir, settings)
    llm = _make_llm(settings)
    messages = [SystemMessage(SYSTEM), HumanMessage(_render(context))]

    for _ in range(MAX_TURNS):
        response = llm.invoke(messages)
        messages.append(response)
        if not response.tool_calls:
            messages.append(HumanMessage("Continue. Finish by calling submit_fix."))
            continue
        for call in response.tool_calls:
            if call["name"] == "submit_fix":
                staged = tools.staged_edits()
                return Fix(
                    edits=[FileEdit(path=p, new_content=c) for p, c in staged.items()],
                    root_cause=call["args"].get("root_cause", ""),
                    explanation=call["args"].get("explanation", ""),
                )
            if call["name"] in _EXECUTABLE:
                result = tools.__dict__[call["name"]].invoke(call["args"])
            else:
                result = f"ERROR: unknown tool {call['name']}"
            messages.append(ToolMessage(content=str(result), tool_call_id=call["id"]))
    raise AgentError(f"no submit_fix after {MAX_TURNS} turns")
