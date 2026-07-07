import pytest

from dbt_medic import tools
from dbt_medic.config import Settings


@pytest.fixture()
def project(tmp_path):
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "stg_orders.sql").write_text("select 1")
    tools.configure(str(tmp_path), Settings())
    return tmp_path


def test_read_file(project):
    assert tools.read_file.invoke({"path": "models/stg_orders.sql"}) == "select 1"


def test_read_file_blocks_traversal(project):
    out = tools.read_file.invoke({"path": "../../etc/passwd"})
    assert out.startswith("ERROR")


def test_edit_file_stages(project):
    tools.edit_file.invoke({"path": "models/stg_orders.sql", "new_content": "select 2"})
    assert tools.staged_edits() == {"models/stg_orders.sql": "select 2"}
    # disk untouched — edits are staged, not applied
    assert (project / "models" / "stg_orders.sql").read_text() == "select 1"


def test_configure_resets_staging(project):
    tools.edit_file.invoke({"path": "a.sql", "new_content": "x"})
    tools.configure(str(project), Settings())
    assert tools.staged_edits() == {}


def test_run_sql_uses_databricks(project, monkeypatch):
    calls = {}

    def fake_execute(statement: str) -> str:
        calls["sql"] = statement
        return "col1\tcol2\n1\t2"

    monkeypatch.setattr(tools, "_execute_sql", fake_execute)
    out = tools.run_sql.invoke({"query": "select * from shop.orders limit 5"})
    assert calls["sql"].startswith("select")
    assert "col1" in out


def test_get_schema_describes_table(project, monkeypatch):
    monkeypatch.setattr(tools, "_execute_sql", lambda s: f"RAN: {s}")
    out = tools.get_schema.invoke({"table": "shop.orders"})
    assert out == "RAN: DESCRIBE TABLE shop.orders"
