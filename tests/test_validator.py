import os

from pipemedic import validator
from pipemedic.config import Settings
from pipemedic.models import FileEdit, Fix, ValidationResult


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
        seen["schema"] = os.environ.get("PIPEMEDIC_SCHEMA")
        seen["select"] = args[args.index("--select") + 1]
        return True, "ok"

    monkeypatch.setattr(validator, "_run_dbt", fake_run_dbt)
    result = validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=False))
    assert isinstance(result, ValidationResult)
    assert result.passed is True
    assert seen["edited"] == "select 2"
    assert seen["select"] == "stg_orders"
    assert seen["schema"] == "pipemedic_dev"
    # original untouched
    assert (project / "models" / "stg_orders.sql").read_text() == "select 1"


def test_validate_failure_returns_logs(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.setattr(validator, "_run_dbt", lambda args: (False, "Database Error: boom"))
    result = validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=False))
    assert result.passed is False
    assert "boom" in result.logs


def test_validate_iceberg_branch_wraps_build(tmp_path, monkeypatch):
    project = _project(tmp_path)
    calls = []

    monkeypatch.setattr(validator, "_run_dbt", lambda args: (True, "ok"))
    monkeypatch.setattr(
        "pipemedic.branch.create_branch",
        lambda table, settings: calls.append(("create", table)) or "pipemedic_fix",
    )
    monkeypatch.setattr(
        "pipemedic.branch.drop_branch",
        lambda table, branch, settings: calls.append(("drop", table, branch)),
    )

    result = validator.validate(
        _fix(), str(project), "stg_orders", Settings(use_iceberg_branch=True, dev_schema="dev")
    )
    assert result.passed is True
    assert result.branch_name == "pipemedic_fix"
    assert calls == [
        ("create", "dev.stg_orders"),
        ("drop", "dev.stg_orders", "pipemedic_fix"),
    ]


def test_validate_drops_branch_on_build_failure(tmp_path, monkeypatch):
    project = _project(tmp_path)
    calls = []

    monkeypatch.setattr(validator, "_run_dbt", lambda args: (False, "boom"))
    monkeypatch.setattr(
        "pipemedic.branch.create_branch",
        lambda table, settings: calls.append("create") or "pipemedic_fix",
    )
    monkeypatch.setattr(
        "pipemedic.branch.drop_branch",
        lambda table, branch, settings: calls.append("drop"),
    )

    result = validator.validate(
        _fix(), str(project), "stg_orders", Settings(use_iceberg_branch=True, dev_schema="dev")
    )
    assert result.passed is False
    assert calls == ["create", "drop"]


def test_validate_restores_prior_env_var(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.setattr(validator, "_run_dbt", lambda args: (True, "ok"))
    monkeypatch.setenv("PIPEMEDIC_SCHEMA", "previous_value")

    validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=False))

    assert os.environ.get("PIPEMEDIC_SCHEMA") == "previous_value"


def test_validate_removes_env_var_if_previously_unset(tmp_path, monkeypatch):
    project = _project(tmp_path)
    monkeypatch.setattr(validator, "_run_dbt", lambda args: (True, "ok"))
    monkeypatch.delenv("PIPEMEDIC_SCHEMA", raising=False)

    validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=False))

    assert "PIPEMEDIC_SCHEMA" not in os.environ


def test_validate_restores_prior_branch_env_var(tmp_path, monkeypatch):
    project = _project(tmp_path)
    calls = []
    monkeypatch.setattr(validator, "_run_dbt", lambda args: (True, "ok"))
    monkeypatch.setattr(
        "pipemedic.branch.create_branch",
        lambda table, settings: calls.append("create") or "pipemedic_fix",
    )
    monkeypatch.setattr(
        "pipemedic.branch.drop_branch",
        lambda table, branch, settings: calls.append("drop"),
    )
    monkeypatch.setenv("PIPEMEDIC_BRANCH", "previous_branch")

    validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=True, dev_schema="dev"))

    assert os.environ.get("PIPEMEDIC_BRANCH") == "previous_branch"


def test_validate_removes_branch_env_var_if_previously_unset(tmp_path, monkeypatch):
    project = _project(tmp_path)
    calls = []
    monkeypatch.setattr(validator, "_run_dbt", lambda args: (True, "ok"))
    monkeypatch.setattr(
        "pipemedic.branch.create_branch",
        lambda table, settings: calls.append("create") or "pipemedic_fix",
    )
    monkeypatch.setattr(
        "pipemedic.branch.drop_branch",
        lambda table, branch, settings: calls.append("drop"),
    )
    monkeypatch.delenv("PIPEMEDIC_BRANCH", raising=False)

    validator.validate(_fix(), str(project), "stg_orders", Settings(use_iceberg_branch=True, dev_schema="dev"))

    assert "PIPEMEDIC_BRANCH" not in os.environ
