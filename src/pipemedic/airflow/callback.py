"""Airflow on_failure_callback — the drop-in hook users copy into their DAG.

Usage in a DAG:
    default_args = {"on_failure_callback": on_failure_callback}
    # task params must include: {"pipemedic": {"model": "stg_orders", "project_dir": "/opt/dbt"}}
"""

from pipemedic.config import Settings
from pipemedic.graph import run_fix


def on_failure_callback(context: dict) -> None:
    params = (context.get("params") or {}).get("pipemedic")
    if not params:
        return  # task not opted in; do nothing
    run_fix(params["project_dir"], params["model"], Settings.from_env())
