"""Validator: apply a Fix on an Iceberg branch (or dev schema), dbt build there."""

from dbt_medic.models import Fix, ValidationResult


def validate(fix: Fix, project_dir: str) -> ValidationResult:
    """Apply edits, run dbt build + tests on an isolated branch, tear down."""
    raise NotImplementedError
