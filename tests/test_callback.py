from pipemedic.airflow import callback


def test_no_params_does_not_run_fix(monkeypatch):
    called = []
    monkeypatch.setattr(callback, "run_fix", lambda pd, mn, s: called.append(1))
    callback.on_failure_callback({"params": {}})
    assert called == []


def test_missing_model_does_not_run_fix(monkeypatch):
    called = []
    monkeypatch.setattr(callback, "run_fix", lambda pd, mn, s: called.append(1))
    callback.on_failure_callback({"params": {"pipemedic": {"project_dir": "/opt/dbt"}}})
    assert called == []


def test_missing_project_dir_does_not_run_fix(monkeypatch):
    called = []
    monkeypatch.setattr(callback, "run_fix", lambda pd, mn, s: called.append(1))
    callback.on_failure_callback({"params": {"pipemedic": {"model": "stg_orders"}}})
    assert called == []


def test_complete_params_runs_fix(monkeypatch):
    calls = []
    monkeypatch.setattr(callback, "run_fix", lambda pd, mn, s: calls.append((pd, mn)))
    monkeypatch.setattr(callback.Settings, "from_env", classmethod(lambda cls: "settings"))
    callback.on_failure_callback(
        {"params": {"pipemedic": {"model": "stg_orders", "project_dir": "/opt/dbt"}}}
    )
    assert calls == [("/opt/dbt", "stg_orders")]
