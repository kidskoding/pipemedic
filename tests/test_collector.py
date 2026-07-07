import json

import pytest

from pipemedic.collector import CollectorError, collect

MANIFEST = {
    "metadata": {"project_name": "warehouse"},
    "nodes": {
        "model.warehouse.stg_orders": {
            "resource_type": "model",
            "name": "stg_orders",
            "raw_code": "select order_id, amount from {{ source('shop', 'orders') }}",
            "original_file_path": "models/stg_orders.sql",
            "depends_on": {"nodes": ["source.warehouse.shop.orders"]},
        }
    },
    "sources": {
        "source.warehouse.shop.orders": {
            "name": "orders",
            "columns": {"order_id": {"data_type": "bigint"}, "amount_usd": {"data_type": "double"}},
        }
    },
}

RUN_RESULTS = {
    "results": [
        {
            "unique_id": "model.warehouse.stg_orders",
            "status": "error",
            "message": "COLUMN_NOT_FOUND: amount",
        }
    ]
}


def _write_artifacts(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "manifest.json").write_text(json.dumps(MANIFEST))
    (target / "run_results.json").write_text(json.dumps(RUN_RESULTS))
    compiled = target / "compiled" / "warehouse" / "models"
    compiled.mkdir(parents=True)
    (compiled / "stg_orders.sql").write_text("select order_id, amount from shop.orders")
    return tmp_path


def test_collect_builds_failure_context(tmp_path):
    project = _write_artifacts(tmp_path)
    ctx = collect(str(project), "stg_orders")
    assert ctx.model_name == "stg_orders"
    assert "COLUMN_NOT_FOUND" in ctx.error_message
    assert "{{ source(" in ctx.raw_sql
    assert ctx.compiled_sql == "select order_id, amount from shop.orders"
    assert ctx.upstream_models == ["source.warehouse.shop.orders"]
    assert ctx.source_schema == {"order_id": "bigint", "amount_usd": "double"}


def test_collect_unknown_model_raises(tmp_path):
    project = _write_artifacts(tmp_path)
    with pytest.raises(CollectorError):
        collect(str(project), "nope")
