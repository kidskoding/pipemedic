# Eval harness

## Prerequisites

`run_evals.py` runs real `dbt build`s against Databricks, so it needs live
credentials and cannot be run in CI/offline:

- `PIPEMEDIC_DATABRICKS_HOST`, `PIPEMEDIC_DATABRICKS_TOKEN`,
  `PIPEMEDIC_DATABRICKS_WAREHOUSE_ID` (or `..._HTTP_PATH` for `profiles.yml`)
  set in the environment.
- `PIPEMEDIC_ANTHROPIC_API_KEY` and `PIPEMEDIC_GITHUB_TOKEN` for the agent
  and (disabled-in-eval) publisher.
- `evals/project/profiles.yml` templates its schema from `PIPEMEDIC_SCHEMA`,
  same requirement the validator enforces for real runs.

Each scenario's `_prepare()` step runs `dbt build` against the seeded,
broken project once — that build is *expected to fail*; its only job is to
populate `target/` with the manifest/run_results artifacts the collector
reads, before `run_fix` (and its own internal `dbt build`s) take over.

~30–50 seeded broken-pipeline scenarios: a known-good dbt project under
`project/`, broken in documented ways under `scenarios/` (one directory per
scenario: `breakage.patch` + `expected.yml`).

`run_evals.py` runs the agent across all scenarios and reports:

- **% auto-fixed** — fix validated and would-merge
- **mean retries to green**
- **failure taxonomy** — which classes it nails, which it escalates

Results are published here as the credibility artifact for the project.
