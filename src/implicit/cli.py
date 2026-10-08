from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import sys
from importlib.metadata import version

from .sdk import Implicit
from .serialization import json_value
from .storage import SQLiteEventStore


def _main() -> None:
    parser = argparse.ArgumentParser(prog="implicit")
    parser.add_argument("--version", action="version", version=version("implicit-ai"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("demo", help="show one addressed experience and selective state materialization")
    sub.add_parser("benchmark", help="compare eager and lazy state on an offline deterministic workload")
    run = sub.add_parser("run")
    run.add_argument("--episodes", type=int, default=8)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--database", default="implicit.db")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("session_id")
    inspect.add_argument("--database", default="implicit.db")
    args = parser.parse_args()
    if args.command in {"demo", "benchmark"}:
        from .demo import benchmark

        result = benchmark()
    elif args.command == "doctor":
        result = {
            "python": platform.python_version(),
            "local_core": True,
            "runtime_dependencies": 0,
            "paid_api_required_for_toy": False,
        }
    elif args.command == "run":
        from .adapters.toy import components

        agent, environment, evaluator = components()
        session = Implicit(database=args.database).connect(
            agent=agent, environment=environment, evaluator=evaluator
        )
        explored = session.explore(episodes=args.episodes, seed=args.seed)
        result = {
            "session_id": explored.session_id,
            "episodes": len(explored.episodes),
            "rewards": [ep.verification.reward for ep in explored.episodes],
            "metrics": explored.metrics,
        }
    else:
        store = SQLiteEventStore(args.database)
        result = {"manifest": store.manifest(args.session_id), "events": store.events(args.session_id)}
    print(json.dumps(json_value(result), indent=2, ensure_ascii=False))


def main() -> None:
    try:
        _main()
    except (ValueError, KeyError, OSError, sqlite3.Error) as exc:
        print(
            f"implicit: {type(exc).__name__}: invalid configuration or unavailable/corrupt local state",
            file=sys.stderr,
        )
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
