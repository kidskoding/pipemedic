import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))
import run_evals  # noqa: E402

from pipemedic.graph import MedicState  # noqa: E402


def test_score_scenario_counts_fix(monkeypatch):
    monkeypatch.setattr(
        run_evals,
        "run_fix",
        lambda pd, mn, s: MedicState(project_dir=pd, model_name=mn, pr_url="https://x/1", attempts=2),
    )
    row = run_evals.score_scenario(Path("evals/scenarios/001-column-rename"), settings=None)
    assert row == {"id": "001-column-rename", "class": "schema_drift", "fixed": True, "attempts": 2}


def test_summarize():
    rows = [
        {"id": "a", "class": "schema_drift", "fixed": True, "attempts": 1},
        {"id": "b", "class": "cast_error", "fixed": False, "attempts": 3},
    ]
    summary = run_evals.summarize(rows)
    assert summary["auto_fix_rate"] == 0.5
    assert summary["mean_retries"] == 2.0
