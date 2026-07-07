# dbt-medic

An autonomous "AI data engineer" that fixes broken dbt pipelines.

When a dbt model fails in Airflow, dbt-medic root-causes the error, writes the
fix, proves it on an isolated Iceberg branch against real data, and opens a PR
with the diff, a root-cause writeup, and passing tests. The human reviews and
merges — the agent never touches prod.

## How it works

dbt-medic is a full AI agent, built as a **LangGraph state machine** around a
tool-using Claude core. It doesn't run one prompt — it investigates, acts,
observes results, and self-corrects until the pipeline is green or it decides
a human is needed.

```mermaid
flowchart TD
    A[/"🔥 Airflow: dbt model fails"/] --> B["📦 collect<br/><i>error, compiled SQL, lineage,<br/>manifest, source schema</i>"]
    B --> C["🧠 agent — Claude tool-use loop"]

    subgraph TOOLS ["agent tools"]
        direction LR
        T1(["read_file"])
        T2(["get_schema"])
        T3(["run_sql"])
        T4(["edit_file"])
    end

    C <-.-> TOOLS
    C -- "proposed fix" --> D{"🧪 validate<br/><i>dbt build + tests on isolated<br/>Iceberg branch — never prod</i>"}

    D -- "✅ tests pass" --> E["🚀 publish<br/><i>GitHub PR: diff + root cause<br/>+ test proof</i>"]
    D -- "❌ fail (attempt < 3)" --> R["feed error back"]
    R --> C
    D -- "❌ fail (retries exhausted)" --> F["🙋 escalate to human<br/><i>no guessing</i>"]

    E --> G[/"👤 human reviews & merges"/]

    style A fill:#7c2d12,stroke:#ea580c,color:#fff
    style B fill:#1e3a8a,stroke:#3b82f6,color:#fff
    style C fill:#4c1d95,stroke:#8b5cf6,color:#fff
    style TOOLS fill:#2e1065,stroke:#8b5cf6,color:#ddd
    style T1 fill:#4c1d95,stroke:#a78bfa,color:#fff
    style T2 fill:#4c1d95,stroke:#a78bfa,color:#fff
    style T3 fill:#4c1d95,stroke:#a78bfa,color:#fff
    style T4 fill:#4c1d95,stroke:#a78bfa,color:#fff
    style D fill:#713f12,stroke:#eab308,color:#fff
    style E fill:#14532d,stroke:#22c55e,color:#fff
    style F fill:#7f1d1d,stroke:#ef4444,color:#fff
    style G fill:#14532d,stroke:#22c55e,color:#fff
    style R fill:#450a0a,stroke:#f87171,color:#fff
```

- **collect** — gathers the failing model, compiled SQL, error text, dbt
  artifacts, and upstream lineage into a structured failure context.
- **agent** — Claude with tools (`read_file`, `get_schema`, `run_sql`,
  `edit_file`) runs an inner tool-use loop: inspect the project, query the
  warehouse, root-cause the failure, stage a fix.
- **validate** — applies the fix on an isolated Iceberg branch (dev-schema
  fallback) and runs `dbt build` + tests there against real data. Failures
  route back to the agent with the error in state; after N attempts it
  escalates to a human instead of guessing.
- **publish** — opens a GitHub PR with the diff, a root-cause writeup, and
  the branch test proof. The agent never touches prod; the human merges.

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
