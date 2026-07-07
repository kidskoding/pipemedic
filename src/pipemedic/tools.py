"""LangChain tools the agent node can call while diagnosing a failure.

ponytail: module-level context — one agent run per process. Make it a class
if we ever run concurrent fixes in one process.
"""

from pathlib import Path

from langchain_core.tools import tool

from pipemedic.config import Settings

_ctx: dict = {"project_dir": None, "settings": None, "staged": {}}


def configure(project_dir: str, settings: Settings) -> None:
    _ctx.update(project_dir=project_dir, settings=settings, staged={})


def staged_edits() -> dict[str, str]:
    return dict(_ctx["staged"])


def _resolve(path: str) -> Path | None:
    root = Path(_ctx["project_dir"]).resolve()
    candidate = (root / path).resolve()
    return candidate if candidate.is_relative_to(root) else None


def _execute_sql(statement: str) -> str:
    """Run a statement via Databricks SQL warehouse; returns TSV-ish text."""
    from databricks.sdk import WorkspaceClient

    s: Settings = _ctx["settings"]
    w = WorkspaceClient(host=s.databricks_host, token=s.databricks_token)
    resp = w.statement_execution.execute_statement(
        statement=statement, warehouse_id=s.databricks_warehouse_id, wait_timeout="30s"
    )
    if resp.result is None or resp.result.data_array is None:
        return f"(no rows) status={resp.status.state if resp.status else 'unknown'}"
    cols = [c.name for c in resp.manifest.schema.columns] if resp.manifest else []
    lines = ["\t".join(cols)] if cols else []
    lines += ["\t".join("" if v is None else str(v) for v in row) for row in resp.result.data_array]
    return "\n".join(lines)


@tool
def read_file(path: str) -> str:
    """Read a file from the dbt project (model SQL, schema.yml, sources)."""
    p = _resolve(path)
    if p is None:
        return "ERROR: path escapes the project directory"
    if not p.exists():
        return f"ERROR: {path} does not exist"
    return p.read_text()


@tool
def get_schema(table: str) -> str:
    """Return the current column names/types of a warehouse table (e.g. 'shop.orders')."""
    return _execute_sql(f"DESCRIBE TABLE {table}")


_READ_ONLY_PREFIXES = ("SELECT", "WITH", "DESCRIBE", "SHOW", "EXPLAIN")


def _strip_leading_comments(sql: str) -> str:
    """Drop leading whitespace/`--`/`/* */` comments to find the real first statement."""
    s = sql.lstrip()
    while True:
        if s.startswith("--"):
            s = s.split("\n", 1)[1].lstrip() if "\n" in s else ""
        elif s.startswith("/*"):
            s = s.split("*/", 1)[1].lstrip() if "*/" in s else ""
        else:
            return s


@tool
def run_sql(query: str) -> str:
    """Run a read-only diagnostic query against the warehouse (row samples, counts)."""
    if not _strip_leading_comments(query).upper().startswith(_READ_ONLY_PREFIXES):
        return "ERROR: run_sql is read-only"
    return _execute_sql(query)


@tool
def edit_file(path: str, new_content: str) -> str:
    """Stage an edit to a dbt project file as part of the proposed fix. Does not touch disk."""
    if _resolve(path) is None:
        return "ERROR: path escapes the project directory"
    _ctx["staged"][path] = new_content
    return f"staged edit to {path} ({len(new_content)} chars)"


@tool
def submit_fix(root_cause: str, explanation: str) -> str:
    """Finish: submit the staged edits as the fix, with your root-cause analysis."""
    return "fix submitted"


ALL_TOOLS = [read_file, get_schema, run_sql, edit_file, submit_fix]
