"""Run the complete dependency-free local verification gate."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], env: dict[str, str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/demo"),
        help="artifact output directory relative to the project root",
    )
    args = parser.parse_args()

    output = args.output
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    evidence = output / "evidence.json"

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")

    run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        env,
    )
    run(
        [
            sys.executable,
            "-m",
            "gameready",
            "demo",
            "--output",
            str(output),
        ],
        env,
    )
    run(
        [sys.executable, "-m", "gameready", "replay", str(evidence)],
        env,
    )
    run(["git", "diff", "--check"], env)

    print("GameReady local verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
