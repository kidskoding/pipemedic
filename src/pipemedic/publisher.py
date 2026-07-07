"""Publisher: validated Fix + proof -> GitHub PR."""

from pipemedic.models import Fix, ValidationResult


def open_pr(fix: Fix, proof: ValidationResult, repo: str) -> str:
    """Open a PR with the diff, root-cause writeup, and test proof. Returns PR URL."""
    raise NotImplementedError
