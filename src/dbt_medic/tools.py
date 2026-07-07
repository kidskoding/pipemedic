"""LangChain tools the agent node can call while diagnosing a failure."""

from langchain_core.tools import tool


@tool
def read_file(path: str) -> str:
    """Read a file from the dbt project (model SQL, schema.yml, sources)."""
    raise NotImplementedError


@tool
def get_schema(table: str) -> str:
    """Return the current column names/types of an upstream table."""
    raise NotImplementedError


@tool
def run_sql(query: str) -> str:
    """Run a read-only diagnostic query against the warehouse (row samples, counts)."""
    raise NotImplementedError


@tool
def edit_file(path: str, new_content: str) -> str:
    """Stage an edit to a dbt project file as part of the proposed fix."""
    raise NotImplementedError
