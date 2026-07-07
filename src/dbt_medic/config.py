"""Config: env/yaml settings, iceberg-vs-devschema validation mode."""

from pydantic import BaseModel


class Settings(BaseModel):
    anthropic_api_key: str = ""
    github_token: str = ""
    github_repo: str = ""
    databricks_host: str = ""
    databricks_token: str = ""
    use_iceberg_branch: bool = True  # False -> dev-schema fallback
    max_retries: int = 3
