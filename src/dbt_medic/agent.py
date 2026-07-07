"""Agent: Claude loop. FailureContext -> Fix, consuming validator errors on retry."""

from dbt_medic.models import FailureContext, Fix


def propose_fix(context: FailureContext) -> Fix:
    """Ask Claude to root-cause the failure and propose file edits."""
    raise NotImplementedError
