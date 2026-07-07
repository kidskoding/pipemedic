"""Smallest check that the shared types hold their contract."""

from pipemedic.models import FailureContext, FileEdit, Fix, ValidationResult


def test_types_roundtrip():
    ctx = FailureContext(model_name="stg_orders", error_message="column not found")
    fix = Fix(
        edits=[FileEdit(path="models/stg_orders.sql", new_content="select 1")],
        root_cause="upstream rename",
        explanation="renamed col",
    )
    result = ValidationResult(passed=True, logs="ok")
    assert ctx.prior_attempts == []
    assert fix.edits[0].path.endswith(".sql")
    assert result.branch_name is None
