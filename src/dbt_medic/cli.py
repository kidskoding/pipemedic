"""CLI entrypoint: `dbt-medic fix --model X --project-dir .`"""

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(prog="dbt-medic")
    sub = parser.add_subparsers(dest="command", required=True)
    fix = sub.add_parser("fix", help="diagnose and fix a failed dbt model")
    fix.add_argument("--model", required=True)
    fix.add_argument("--project-dir", default=".")
    args = parser.parse_args()
    raise NotImplementedError(f"command {args.command} not implemented yet")
