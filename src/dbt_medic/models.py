"""Shared types — the unit boundaries between collector, agent, validator, publisher."""

from pydantic import BaseModel


class FailureContext(BaseModel):
    """Everything the agent needs to root-cause a failed dbt model."""

    model_name: str
    error_message: str
    compiled_sql: str | None = None
    raw_sql: str | None = None
    upstream_models: list[str] = []
    source_schema: dict[str, str] = {}  # column -> type
    prior_attempts: list[str] = []  # validator errors from earlier retries


class FileEdit(BaseModel):
    path: str
    new_content: str


class Fix(BaseModel):
    """A proposed fix: file edits plus the agent's root-cause explanation."""

    edits: list[FileEdit]
    root_cause: str
    explanation: str


class ValidationResult(BaseModel):
    passed: bool
    logs: str
    branch_name: str | None = None  # Iceberg branch used, if any
