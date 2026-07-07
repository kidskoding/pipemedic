from pipemedic import graph
from pipemedic.config import Settings
from pipemedic.models import FailureContext, FileEdit, Fix, ValidationResult

FIX = Fix(edits=[FileEdit(path="m.sql", new_content="x")], root_cause="rc", explanation="ex")
CTX = FailureContext(model_name="stg_orders", error_message="boom")


def _patch(monkeypatch, validations):
    """validations: list of ValidationResult returned in order."""
    monkeypatch.setattr(graph, "_collect", lambda pd, mn: CTX)
    monkeypatch.setattr(graph, "_propose_fix", lambda ctx, pd, s: FIX)
    results = iter(validations)
    monkeypatch.setattr(graph, "_validate", lambda fix, pd, mn, s: next(results))
    monkeypatch.setattr(graph, "_open_pr", lambda fix, proof, mn, s: "https://x/pull/1")


def test_happy_path_publishes(monkeypatch):
    _patch(monkeypatch, [ValidationResult(passed=True, logs="ok")])
    final = graph.run_fix("/proj", "stg_orders", Settings())
    assert final.pr_url == "https://x/pull/1"
    assert final.attempts == 1


def test_retry_then_publish(monkeypatch):
    _patch(
        monkeypatch,
        [ValidationResult(passed=False, logs="err1"), ValidationResult(passed=True, logs="ok")],
    )
    final = graph.run_fix("/proj", "stg_orders", Settings())
    assert final.pr_url == "https://x/pull/1"
    assert final.attempts == 2
    # validator error was fed back into the context for the retry
    assert "err1" in final.context.prior_attempts[0]


def test_escalates_after_max_retries(monkeypatch):
    _patch(monkeypatch, [ValidationResult(passed=False, logs=f"err{i}") for i in range(3)])
    final = graph.run_fix("/proj", "stg_orders", Settings(max_retries=3))
    assert final.pr_url is None
    assert final.attempts == 3
