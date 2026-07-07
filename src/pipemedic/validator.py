"""Validator: apply a Fix in an isolated copy, dbt build on a dev schema (or Iceberg branch)."""

import os
import shutil
import tempfile
from pathlib import Path

from pipemedic.config import Settings
from pipemedic.models import Fix, ValidationResult


def _run_dbt(args: list[str]) -> tuple[bool, str]:
    """Invoke dbt programmatically; returns (success, logs)."""
    from dbt.cli.main import dbtRunner

    res = dbtRunner().invoke(args)
    logs = ""
    if res.result is not None and hasattr(res.result, "results"):
        logs = "\n".join(
            f"{r.node.name}: {r.status} {r.message or ''}" for r in res.result.results
        )
    if res.exception:
        logs += f"\n{res.exception}"
    return bool(res.success), logs


def validate(fix: Fix, project_dir: str, model_name: str, settings: Settings) -> ValidationResult:
    """Apply edits to a temp copy of the project, dbt build the model + tests there."""
    with tempfile.TemporaryDirectory(prefix="pipemedic-") as tmp:
        work = Path(tmp) / "project"
        shutil.copytree(project_dir, work, ignore=shutil.ignore_patterns("target", ".git"))
        for edit in fix.edits:
            dest = work / edit.path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(edit.new_content)

        # profiles.yml should template schema from this env var; see README snippet
        os.environ["DBT_MEDIC_SCHEMA"] = settings.dev_schema
        passed, logs = _run_dbt(
            [
                "build",
                "--select",
                model_name,
                "--project-dir",
                str(work),
                "--profiles-dir",
                str(work),
            ]
        )
        return ValidationResult(passed=passed, logs=logs)
