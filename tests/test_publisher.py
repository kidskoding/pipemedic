from unittest.mock import MagicMock

from pipemedic import publisher
from pipemedic.config import Settings
from pipemedic.models import FileEdit, Fix, ValidationResult


def test_open_pr(monkeypatch):
    repo = MagicMock()
    repo.default_branch = "main"
    repo.get_branch.return_value.commit.sha = "abc123"
    existing = MagicMock()
    existing.sha = "filesha"
    repo.get_contents.return_value = existing
    repo.create_pull.return_value.html_url = "https://github.com/acme/warehouse/pull/7"
    gh = MagicMock()
    gh.get_repo.return_value = repo
    monkeypatch.setattr(publisher, "_github", lambda settings: gh)

    fix = Fix(
        edits=[FileEdit(path="models/stg_orders.sql", new_content="select 2")],
        root_cause="upstream renamed amount -> amount_usd",
        explanation="aliased the column",
    )
    proof = ValidationResult(passed=True, logs="stg_orders: success", branch_name="dbt_medic_fix")
    url = publisher.open_pr(fix, proof, "stg_orders", Settings(github_repo="acme/warehouse"))

    assert url.endswith("/pull/7")
    repo.create_git_ref.assert_called_once_with(ref="refs/heads/pipemedic/fix-stg_orders", sha="abc123")
    repo.update_file.assert_called_once()
    body = repo.create_pull.call_args.kwargs["body"]
    assert "upstream renamed" in body and "stg_orders: success" in body
