"""Run manifest construction.

Privacy note: only generic platform facts are recorded (OS name, architecture,
Python version). Hostnames, usernames, and filesystem paths outside the run
directory are deliberately excluded so manifests are safe to publish.
"""

from __future__ import annotations

import platform
import sys
from datetime import datetime, timezone
from typing import Any

from . import __version__


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_manifest(
    *,
    run_id: str,
    run_name: str,
    adapter: str,
    model: str,
    model_digest: str,
    backend_version: str,
    params: dict[str, Any],
    pack_name: str,
    pack_version: str,
    prompts_sha256: str,
    conditions: list[str],
    repeats: int,
    shuffle_seed: int,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "run_name": run_name,
        "created_utc": utc_now_iso(),
        "framework": {"name": "promptpack-eval", "version": __version__},
        "environment": {
            "python": sys.version.split()[0],
            "os": platform.system(),
            "arch": platform.machine(),
        },
        "model": {
            "adapter": adapter,
            "name": model,
            "digest": model_digest,
            "backend_version": backend_version,
            "params": params,
        },
        "pack": {
            "name": pack_name,
            "version": pack_version,
            "prompts_sha256": prompts_sha256,
        },
        "design": {
            "conditions": conditions,
            "repeats": repeats,
            "shuffle_seed": shuffle_seed,
            "n_items": len(conditions) * repeats,
        },
    }
