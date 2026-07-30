"""Command-line interface for the GameReady reference kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .evidence import EvidenceBundle
from .loop import run_demo
from .replay import replay_evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gameready",
        description="GameReady deterministic self-healing reference kernel",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser(
        "demo",
        help="run the duplicate-delivery incident through the local closure loop",
    )
    demo.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/demo"),
        help="artifact output directory (default: artifacts/demo)",
    )

    replay = subparsers.add_parser(
        "replay",
        help="replay a previously captured evidence bundle",
    )
    replay.add_argument("evidence", type=Path, help="path to evidence.json")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "demo":
        report = run_demo(args.output.resolve())
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if report.local_closed else 1

    if args.command == "replay":
        bundle = EvidenceBundle.load(args.evidence.resolve())
        result = replay_evidence(bundle)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result.exact else 1

    raise AssertionError(f"unhandled command: {args.command}")
