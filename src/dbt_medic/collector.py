"""Collector: dbt artifacts + lineage -> FailureContext."""

from dbt_medic.models import FailureContext


def collect(project_dir: str, model_name: str) -> FailureContext:
    """Gather failure context from manifest.json, run_results.json, and compiled SQL."""
    raise NotImplementedError
