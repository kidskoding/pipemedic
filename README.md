# pipemedic

An autonomous data engineering agent that fixes broken dbt pipelines

When a dbt model fails in Apache Airflow, pipemedic root-causes the error, writes the
fix, proves it on an isolated Iceberg branch against real data, and opens a PR
with the diff, a root-cause writeup, and passing tests. The human reviews and
merges, andthe agent never touches prod: a win-win situation.

## How it works

pipemedic is a full on AI agent, built as a **LangGraph state machine** around a
tool, using Claude core. It doesn't just run one prompt, it investigates, acts,
observes results, and self-corrects until the pipeline is green or it decides
a human is needed.

## Architecture Diagram

```mermaid
flowchart TB
    subgraph ORCH ["Orchestration: Apache Airflow"]
        AF["dbt DAG task fails<br/>on_failure_callback triggers pipemedic"]
    end

    subgraph RUNTIME ["Agent runtime: LangGraph state machine"]
        direction LR
        COLLECT["collect<br/>error, compiled SQL, manifest,<br/>lineage, source schemas"]
        AGENT["Claude (Anthropic API)<br/>tool-use loop"]
        TOOLS(["read_file &middot; get_schema<br/>run_sql &middot; edit_file"])
        COLLECT --> AGENT
        AGENT -.- TOOLS
    end

    subgraph DBX ["Warehouse: Databricks / Apache Iceberg"]
        direction LR
        BR["validate<br/>dbt build + dbt test on<br/>isolated Iceberg branch"]
        PROD["prod tables<br/>never touched by the agent"]
        BR ~~~ PROD
    end

    subgraph GH ["Delivery: GitHub"]
        direction LR
        PR["pull request<br/>diff, root-cause writeup, test proof"]
        HUMAN["human reviews and merges"]
        PR --> HUMAN
    end

    ESC["escalate to human"]

    AF --> COLLECT
    AGENT <-- "proposed fix /<br/>on failure, error fed back<br/>(max 3 attempts)" --> BR
    BR -- "tests pass" --> PR
    BR -- "retries exhausted" --> ESC

    classDef zone fill:#f8fafc,stroke:#94a3b8,color:#334155
    classDef node fill:#ffffff,stroke:#64748b,color:#1e293b
    classDef tool fill:#f1f5f9,stroke:#94a3b8,color:#334155
    classDef guard fill:#fff7ed,stroke:#fb923c,color:#7c2d12

    class ORCH,RUNTIME,DBX,GH zone
    class AF,COLLECT,AGENT,BR,PR,HUMAN node
    class TOOLS tool
    class PROD,ESC guard
```

**Key tech:** Apache Airflow (failure trigger) · dbt (models, build, tests) ·
LangGraph (agent state machine, retry routing) · Anthropic API
(tool-using reasoning core) · Databricks + Apache Iceberg (isolated
write-audit-publish branches) · GitHub (PR delivery)

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
uv tool install pipemedic
```

Then add the Airflow hook:

```python
from pipemedic.airflow import on_failure_callback
```

## Status

Early development — Databricks Fellowship project
