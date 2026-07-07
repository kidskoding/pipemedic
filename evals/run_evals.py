"""Run pipemedic across all seeded scenarios; emit results.json + a taxonomy table."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

from pipemedic.config import Settings
from pipemedic.graph import run_fix

EVALS = Path(__file__).parent


def _prepare(project: Path) -> None:
    """Run `dbt build` once against the (broken) seeded project so it fails and
    produces the target/ artifacts (manifest, run_results) the collector reads.
    A real dbt failure is expected here — we ignore the result and only care
    that the artifacts exist on disk before run_fix's collect step runs.
    """
    from pipemedic.validator import _run_dbt

    _run_dbt(["build", "--project-dir", str(project), "--profiles-dir", str(project)])


def score_scenario(scenario_dir: Path, settings) -> dict:
    expected = yaml.safe_load((scenario_dir / "expected.yml").read_text())
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        shutil.copytree(EVALS / "project", project)
        patch = scenario_dir / "breakage.patch"
        if patch.read_text().strip():
            subprocess.run(["git", "apply", str(patch.resolve())], cwd=project, check=True)
        _prepare(project)
        final = run_fix(str(project), "stg_orders", settings)
    return {
        "id": scenario_dir.name,
        "class": expected["class"],
        "fixed": final.pr_url is not None,
        "attempts": final.attempts,
    }


def summarize(rows: list[dict]) -> dict:
    fixed = [r for r in rows if r["fixed"]]
    return {
        "scenarios": rows,
        "auto_fix_rate": len(fixed) / len(rows) if rows else 0.0,
        "mean_retries": sum(r["attempts"] for r in rows) / len(rows) if rows else 0.0,
    }


def main() -> None:
    import pipemedic.graph as graph_mod

    # never open real PRs during evals
    graph_mod._open_pr = lambda fix, proof, mn, s: "eval://pr"
    settings = Settings.from_env()
    rows = [
        score_scenario(d, settings)
        for d in sorted((EVALS / "scenarios").iterdir())
        if d.is_dir()
    ]
    summary = summarize(rows)
    (EVALS / "results.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
