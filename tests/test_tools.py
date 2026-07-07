import pytest

from pipemedic import tools
from pipemedic.config import Settings


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


def test_edit_file_blocks_traversal(project):
    out = tools.edit_file.invoke({"path": "../../evil", "new_content": "x"})
    assert out.startswith("ERROR")
    assert tools.staged_edits() == {}


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


def test_run_sql_rejects_write_statement(project, monkeypatch):
    called = []
    monkeypatch.setattr(tools, "_execute_sql", lambda s: called.append(s) or "ignored")
    out = tools.run_sql.invoke({"query": "DROP TABLE shop.orders"})
    assert out.startswith("ERROR")
    assert called == []


def test_run_sql_allows_select(project, monkeypatch):
    monkeypatch.setattr(tools, "_execute_sql", lambda s: f"RAN: {s}")
    out = tools.run_sql.invoke({"query": "  -- comment\nselect 1"})
    assert out.startswith("RAN:")
