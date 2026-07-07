import pytest

from pipemedic import cli
from pipemedic.graph import MedicState


def _final(pr_url):
    return MedicState(project_dir="/p", model_name="m", pr_url=pr_url)


def test_fix_exits_zero_on_pr(monkeypatch, capsys):
    monkeypatch.setattr(cli, "run_fix", lambda pd, mn, s: _final("https://x/pull/1"))
    with pytest.raises(SystemExit) as e:
        cli.main(["fix", "--model", "stg_orders"])
    assert e.value.code == 0
    assert "https://x/pull/1" in capsys.readouterr().out


def test_fix_exits_two_on_escalation(monkeypatch):
    monkeypatch.setattr(cli, "run_fix", lambda pd, mn, s: _final(None))
    with pytest.raises(SystemExit) as e:
        cli.main(["fix", "--model", "stg_orders"])
    assert e.value.code == 2
