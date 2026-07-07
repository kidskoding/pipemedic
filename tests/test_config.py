from pipemedic.config import Settings


def test_from_env(monkeypatch):
    monkeypatch.setenv("PIPEMEDIC_ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setenv("PIPEMEDIC_GITHUB_TOKEN", "gh-test")
    monkeypatch.setenv("PIPEMEDIC_GITHUB_REPO", "acme/warehouse")
    monkeypatch.setenv("PIPEMEDIC_USE_ICEBERG_BRANCH", "false")
    s = Settings.from_env()
    assert s.anthropic_api_key == "sk-test"
    assert s.github_repo == "acme/warehouse"
    assert s.use_iceberg_branch is False
    assert s.max_retries == 3  # default
