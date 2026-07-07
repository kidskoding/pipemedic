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

## Architecture

```mermaid
flowchart TB
    subgraph SYS ["dbt-medic — autonomous dbt pipeline repair"]
        direction TB

        subgraph ORCH ["⏱️ Apache Airflow — orchestration"]
            AF["🔥 dbt DAG task fails<br/><i>on_failure_callback → dbt-medic</i>"]
        end

        subgraph RUNTIME ["🧠 Agent runtime — LangGraph state machine"]
            direction TB
            COLLECT["📦 collect<br/><i>error, compiled SQL, manifest,<br/>lineage, source schemas</i>"]

            subgraph LLM ["Claude (Anthropic API) — tool-use loop"]
                direction TB
                CORE["reasoning core<br/><i>root-cause → stage fix</i>"]
                subgraph TOOLS ["tools"]
                    direction LR
                    T1(["read_file"])
                    T2(["get_schema"])
                    T3(["run_sql"])
                    T4(["edit_file"])
                end
                CORE <-.-> TOOLS
            end

            COLLECT --> LLM
        end

        subgraph DBX ["🗄️ Databricks — warehouse"]
            direction TB
            subgraph ICE ["Apache Iceberg catalog"]
                direction LR
                BR["🧪 isolated branch<br/><i>dbt build + dbt test<br/>on real data</i>"]
                PROD["🔒 prod tables<br/><i>never touched</i>"]
            end
        end

        subgraph GH ["🚀 GitHub — delivery"]
            direction TB
            PR["PR: diff + root-cause<br/>writeup + test proof"]
            HUMAN["👤 human reviews & merges"]
            PR --> HUMAN
        end

        ESC["🙋 escalate to human<br/><i>no guessing</i>"]

        AF --> COLLECT
        LLM -- "proposed fix" --> BR
        BR -- "❌ fail (attempt < 3)<br/>error fed back" --> LLM
        BR -- "✅ tests pass" --> PR
        BR -- "❌ retries exhausted" --> ESC
    end

    style SYS fill:#0b1120,stroke:#475569,color:#e2e8f0
    style ORCH fill:#431407,stroke:#ea580c,color:#fed7aa
    style AF fill:#7c2d12,stroke:#fb923c,color:#fff
    style RUNTIME fill:#1e1b4b,stroke:#6366f1,color:#c7d2fe
    style COLLECT fill:#312e81,stroke:#818cf8,color:#fff
    style LLM fill:#2e1065,stroke:#8b5cf6,color:#ddd6fe
    style CORE fill:#4c1d95,stroke:#a78bfa,color:#fff
    style TOOLS fill:#3b0764,stroke:#a78bfa,color:#e9d5ff
    style T1 fill:#4c1d95,stroke:#c4b5fd,color:#fff
    style T2 fill:#4c1d95,stroke:#c4b5fd,color:#fff
    style T3 fill:#4c1d95,stroke:#c4b5fd,color:#fff
    style T4 fill:#4c1d95,stroke:#c4b5fd,color:#fff
    style DBX fill:#422006,stroke:#eab308,color:#fef08a
    style ICE fill:#713f12,stroke:#facc15,color:#fef9c3
    style BR fill:#854d0e,stroke:#fde047,color:#fff
    style PROD fill:#450a0a,stroke:#f87171,color:#fecaca
    style GH fill:#052e16,stroke:#22c55e,color:#bbf7d0
    style PR fill:#14532d,stroke:#4ade80,color:#fff
    style HUMAN fill:#166534,stroke:#86efac,color:#fff
    style ESC fill:#7f1d1d,stroke:#ef4444,color:#fff
```

**Key tech:** Apache Airflow (failure trigger) · dbt (models, build, tests) ·
LangGraph (agent state machine, retry routing) · Claude / Anthropic API
(tool-using reasoning core) · Databricks + Apache Iceberg (isolated
write-audit-publish branches) · GitHub (PR delivery).

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
