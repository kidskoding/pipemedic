# Eval harness

~30–50 seeded broken-pipeline scenarios: a known-good dbt project under
`project/`, broken in documented ways under `scenarios/` (one directory per
scenario: `breakage.patch` + `expected.yml`).

`run_evals.py` runs the agent across all scenarios and reports:

- **% auto-fixed** — fix validated and would-merge
- **mean retries to green**
- **failure taxonomy** — which classes it nails, which it escalates

Results are published here as the credibility artifact for the project.
