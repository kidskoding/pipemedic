"""Collector: dbt artifacts + lineage -> FailureContext."""

import json
from pathlib import Path

from pipemedic.models import FailureContext


class CollectorError(Exception):
    pass


def collect(project_dir: str, model_name: str) -> FailureContext:
    """Gather failure context from manifest.json, run_results.json, and compiled SQL."""
    target = Path(project_dir) / "target"
    try:
        manifest = json.loads((target / "manifest.json").read_text())
        run_results = json.loads((target / "run_results.json").read_text())
    except FileNotFoundError as e:
        raise CollectorError(f"missing dbt artifact: {e.filename}") from e

    node_id = next(
        (
            uid
            for uid, n in manifest["nodes"].items()
            if n.get("resource_type") == "model" and n.get("name") == model_name
        ),
        None,
    )
    if node_id is None:
        raise CollectorError(f"model {model_name!r} not in manifest")
    node = manifest["nodes"][node_id]

    result = next((r for r in run_results["results"] if r["unique_id"] == node_id), None)
    if result is None or result.get("status") not in ("error", "fail"):
        raise CollectorError(f"model {model_name!r} has no failed run result")

    compiled_path = (
        target / "compiled" / manifest["metadata"]["project_name"] / node["original_file_path"]
    )
    compiled_sql = compiled_path.read_text() if compiled_path.exists() else None

    upstream = node.get("depends_on", {}).get("nodes", [])
    source_schema: dict[str, str] = {}
    for uid in upstream:
        src = manifest.get("sources", {}).get(uid)
        if src:
            for col, meta in src.get("columns", {}).items():
                source_schema[col] = meta.get("data_type", "")

    return FailureContext(
        model_name=model_name,
        error_message=result.get("message") or "",
        compiled_sql=compiled_sql,
        raw_sql=node.get("raw_code"),
        upstream_models=upstream,
        source_schema=source_schema,
    )
