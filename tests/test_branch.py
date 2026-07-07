from pipemedic import branch
from pipemedic.config import Settings


def test_create_and_drop_branch(monkeypatch):
    ran = []
    monkeypatch.setattr(branch, "_execute", lambda sql, settings: ran.append(sql) or "ok")
    s = Settings()
    name = branch.create_branch("main.shop.orders", s)
    branch.drop_branch("main.shop.orders", name, s)
    assert ran == [
        "ALTER TABLE main.shop.orders CREATE BRANCH pipemedic_fix",
        "ALTER TABLE main.shop.orders DROP BRANCH pipemedic_fix",
    ]
