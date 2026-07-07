import pytest

from pipemedic import branch
from pipemedic.config import Settings


def test_create_and_drop_branch(monkeypatch):
    ran = []
    monkeypatch.setattr(branch, "_execute", lambda sql, settings: ran.append(sql) or "SUCCEEDED")
    s = Settings()
    name = branch.create_branch("main.shop.orders", s)
    branch.drop_branch("main.shop.orders", name, s)
    assert ran == [
        "ALTER TABLE main.shop.orders CREATE BRANCH pipemedic_fix",
        "ALTER TABLE main.shop.orders DROP BRANCH pipemedic_fix",
    ]


def test_create_branch_raises_on_non_succeeded_state(monkeypatch):
    monkeypatch.setattr(branch, "_execute", lambda sql, settings: "FAILED")
    with pytest.raises(RuntimeError):
        branch.create_branch("main.shop.orders", Settings())


def test_drop_branch_raises_on_non_succeeded_state(monkeypatch):
    monkeypatch.setattr(branch, "_execute", lambda sql, settings: "CANCELED")
    with pytest.raises(RuntimeError):
        branch.drop_branch("main.shop.orders", "pipemedic_fix", Settings())
