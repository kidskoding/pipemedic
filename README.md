# dbt-medic

An autonomous "AI data engineer" that fixes broken dbt pipelines.

When a dbt model fails in Airflow, dbt-medic root-causes the error, writes the
fix, proves it on an isolated Iceberg branch against real data, and opens a PR
with the diff, a root-cause writeup, and passing tests. The human reviews and
merges — the agent never touches prod.

## How it works

```
Airflow failure → Collector → Agent (Claude) → Validator (Iceberg branch) → PR
```

1. **Collector** — gathers the failing model, compiled SQL, error text, dbt
   artifacts, and upstream lineage into a structured failure context.
2. **Agent** — Claude root-causes the failure and proposes a code fix.
3. **Validator** — applies the fix on an isolated Iceberg branch (or dev-schema
   fallback) and runs `dbt build` + tests there. Failures feed back to the
   agent for retry.
4. **Publisher** — opens a GitHub PR with the diff, root-cause writeup, and
   test proof.

## Install

```sh
uv tool install dbt-medic
```

Then add the Airflow hook:

```python
from dbt_medic.airflow import on_failure_callback
```

## Status

Early development — Databricks Fellowship project.
