import pytest
from langchain_core.messages import AIMessage

from pipemedic import agent, tools
from pipemedic.config import Settings
from pipemedic.models import FailureContext


class FakeLLM:
    """Yields scripted AIMessages; ignores input."""

    def __init__(self, messages):
        self._messages = list(messages)

    def invoke(self, _msgs):
        return self._messages.pop(0)


def _ctx():
    return FailureContext(model_name="stg_orders", error_message="COLUMN_NOT_FOUND: amount")


def test_agent_stages_edit_then_submits(tmp_path, monkeypatch):
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "stg_orders.sql").write_text("select amount from t")
    script = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "read_file", "args": {"path": "models/stg_orders.sql"}, "id": "1"},
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "edit_file",
                    "args": {"path": "models/stg_orders.sql", "new_content": "select amount_usd as amount from t"},
                    "id": "2",
                },
                {
                    "name": "submit_fix",
                    "args": {"root_cause": "column renamed to amount_usd", "explanation": "aliased it"},
                    "id": "3",
                },
            ],
        ),
    ]
    monkeypatch.setattr(agent, "_make_llm", lambda settings: FakeLLM(script))
    fix = agent.propose_fix(_ctx(), str(tmp_path), Settings())
    assert fix.root_cause == "column renamed to amount_usd"
    assert fix.edits[0].new_content == "select amount_usd as amount from t"


def test_agent_recovers_from_tool_exception(tmp_path, monkeypatch):
    def _boom(_query):
        raise RuntimeError("warehouse down")

    monkeypatch.setattr(tools, "_execute_sql", _boom)
    script = [
        AIMessage(
            content="",
            tool_calls=[
                {"name": "run_sql", "args": {"query": "select 1"}, "id": "1"},
            ],
        ),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "submit_fix",
                    "args": {"root_cause": "ESCALATE: could not query warehouse", "explanation": ""},
                    "id": "2",
                },
            ],
        ),
    ]
    monkeypatch.setattr(agent, "_make_llm", lambda settings: FakeLLM(script))
    fix = agent.propose_fix(_ctx(), str(tmp_path), Settings())
    assert fix.root_cause.startswith("ESCALATE:")


def test_agent_gives_up_after_max_turns(tmp_path, monkeypatch):
    forever = [AIMessage(content="hmm", tool_calls=[])] * 31
    monkeypatch.setattr(agent, "_make_llm", lambda settings: FakeLLM(forever))
    with pytest.raises(agent.AgentError):
        agent.propose_fix(_ctx(), str(tmp_path), Settings())
