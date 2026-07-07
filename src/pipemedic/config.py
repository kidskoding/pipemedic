"""Config: env settings, iceberg-vs-devschema validation mode."""

import os

from pydantic import BaseModel

_PREFIX = "PIPEMEDIC_"


class Settings(BaseModel):
    anthropic_api_key: str = ""
    github_token: str = ""
    github_repo: str = ""  # "owner/name" of the dbt project repo
    databricks_host: str = ""
    databricks_token: str = ""
    databricks_warehouse_id: str = ""
    dev_schema: str = "pipemedic_dev"
    use_iceberg_branch: bool = True  # False -> dev-schema fallback
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> "Settings":
        values = {}
        for field in cls.model_fields:
            raw = os.environ.get(_PREFIX + field.upper())
            if raw is not None:
                values[field] = raw
        return cls(**values)  # pydantic coerces "false" -> False, "3" -> 3
