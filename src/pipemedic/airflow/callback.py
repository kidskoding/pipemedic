"""Airflow on_failure_callback — the drop-in hook users copy into their DAG."""


def on_failure_callback(context: dict) -> None:
    """Airflow task-failure hook: extract the failed dbt model and run pipemedic."""
    raise NotImplementedError
