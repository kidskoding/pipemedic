"""Iceberg branch ops via Databricks SQL. Isolated here: if the UC branch DDL
surface differs from the Iceberg spec, this is the only file that changes."""

from pipemedic.config import Settings

BRANCH_NAME = "pipemedic_fix"


def _execute(sql: str, settings: Settings) -> str:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(host=settings.databricks_host, token=settings.databricks_token)
    resp = w.statement_execution.execute_statement(
        statement=sql, warehouse_id=settings.databricks_warehouse_id, wait_timeout="30s"
    )
    return str(resp.status.state) if resp.status else "unknown"


def create_branch(table: str, settings: Settings) -> str:
    state = _execute(f"ALTER TABLE {table} CREATE BRANCH {BRANCH_NAME}", settings)
    if "SUCCEEDED" not in state:
        raise RuntimeError(f"CREATE BRANCH on {table} did not succeed: {state}")
    return BRANCH_NAME


def drop_branch(table: str, branch: str, settings: Settings) -> None:
    state = _execute(f"ALTER TABLE {table} DROP BRANCH {branch}", settings)
    if "SUCCEEDED" not in state:
        raise RuntimeError(f"DROP BRANCH on {table} did not succeed: {state}")
