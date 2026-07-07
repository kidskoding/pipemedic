import os

from dbt_medic import validator
from dbt_medic.config import Settings
from dbt_medic.models import FileEdit, Fix, ValidationResult


def _fix():
    return Fix(
        edits=[FileEdit(path="models/stg_orders.sql", new_content="select 2")],
        root_cause="rc",
        explanation="ex",
    )


def _project(tmp_path):
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "stg_orders.sql").write_text("select 1")
    (tmp_path / "dbt_project.yml").write_text("name: warehouse")
    return tmp_path


def test_validate_applies_edits_and_builds(tmp_path, monkeypatch):
    project = _project(tmp_path)
    seen = {}

    def fake_run_dbt(args):
        # the edited file must be present in the temp copy dbt builds
        pdir = args[args.index("--project-dir") + 1]
        seen["edited"] = open(os.path.join(pdir, "models/stg_orders.sql")).read()
        seen["schema"] = os.environ.get("DBT_MEDIC_SCHEMA")
        seen["select"] = args[args.index("--select") + 1]
        return True, "ok"

    monkeypatch.setattr(validator, "_run_dbt", fake_run_dbt)
    result = validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=False))
    assert isinstance(result, ValidationResult)
    assert result.passed is True
    assert seen["edited"] == "select 2"
    assert seen["select"] == "stg_orders"
    assert seen["schema"] == "dbt_medic_dev"
    # original untouched
    assert (project / "models" / "stg_orders.sql").read_text() == "select 1"


def test_validate_failure_returns_logs(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.setattr(validator, "_run_dbt", lambda args: (False, "Database Error: boom"))
    result = validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=False))
    assert result.passed is False
    assert "boom" in result.logs
