"""CLI entrypoint: `pipemedic fix --model X --project-dir .`"""

import argparse
import sys

from pipemedic.config import Settings
from pipemedic.graph import run_fix


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="pipemedic")
    sub = parser.add_subparsers(dest="command", required=True)
    fix = sub.add_parser("fix", help="diagnose and fix a failed dbt model")
    fix.add_argument("--model", required=True)
    fix.add_argument("--project-dir", default=".")
    args = parser.parse_args(argv)

    final = run_fix(args.project_dir, args.model, Settings.from_env())
    if final.pr_url:
        print(f"PR opened: {final.pr_url}")
        sys.exit(0)
    print(f"escalated after {final.attempts} attempts — see logs", file=sys.stderr)
    sys.exit(2)
