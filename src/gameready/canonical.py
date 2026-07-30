"""Canonical serialization helpers used by every evidence-producing stage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize a JSON-compatible value in a stable, whitespace-free form."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_hash(value: Any) -> str:
    """Return a SHA-256 digest of the canonical JSON representation."""

    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def write_pretty_json(path: Path, value: Any) -> None:
    """Write a human-readable artifact while preserving deterministic keys."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    """Read one UTF-8 JSON artifact."""

    return json.loads(path.read_text(encoding="utf-8"))
