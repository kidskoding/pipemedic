"""Publisher: validated Fix + proof -> GitHub PR."""

from github import GithubException

from pipemedic.config import Settings
from pipemedic.models import Fix, ValidationResult


def _github(settings: Settings):
    from github import Github

    return Github(settings.github_token)


def _pr_body(fix: Fix, proof: ValidationResult) -> str:
    validated_on = f"Iceberg branch `{proof.branch_name}`" if proof.branch_name else "dev schema"
    return f"""## Root cause

{fix.root_cause}

## Fix

{fix.explanation}

## Validation proof

Validated on {validated_on} — `dbt build` passed:

```
{proof.logs}
```

---
*Opened automatically by [pipemedic](https://github.com/kidskoding/pipemedic). A human must review and merge.*
"""


def open_pr(fix: Fix, proof: ValidationResult, model_name: str, settings: Settings) -> str:
    """Open a PR with the diff, root-cause writeup, and test proof. Returns PR URL."""
    repo = _github(settings).get_repo(settings.github_repo)
    base = repo.default_branch
    head = f"pipemedic/fix-{model_name}"
    sha = repo.get_branch(base).commit.sha
    try:
        repo.create_git_ref(ref=f"refs/heads/{head}", sha=sha)
    except GithubException:
        # stale ref from a prior failed/aborted run — clear it and retry once
        repo.get_git_ref(f"heads/{head}").delete()
        repo.create_git_ref(ref=f"refs/heads/{head}", sha=sha)

    for edit in fix.edits:
        message = f"pipemedic: fix {model_name} ({edit.path})"
        try:
            existing = repo.get_contents(edit.path, ref=head)
            repo.update_file(edit.path, message, edit.new_content, existing.sha, branch=head)
        except GithubException:
            repo.create_file(edit.path, message, edit.new_content, branch=head)

    pr = repo.create_pull(
        title=f"pipemedic: fix {model_name}",
        body=_pr_body(fix, proof),
        head=head,
        base=base,
    )
    return pr.html_url
