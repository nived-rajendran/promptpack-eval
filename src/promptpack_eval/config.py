"""TOML config loading and validation for runs."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass
class ModelConfig:
    adapter: str
    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunConfig:
    name: str
    pack: Path
    repeats: int
    shuffle_seed: int
    output_dir: Path
    model: ModelConfig
    conditions: list[str] | None = None
    source_path: Path | None = None


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_run_config(path: Path) -> RunConfig:
    """Load and validate a run config. Relative paths resolve against CWD."""
    data = load_toml(path)

    run = data.get("run")
    model = data.get("model")
    if not isinstance(run, dict):
        raise ConfigError(f"{path}: missing [run] table")
    if not isinstance(model, dict):
        raise ConfigError(f"{path}: missing [model] table")

    for key in ("name", "pack"):
        if not run.get(key):
            raise ConfigError(f"{path}: [run] requires '{key}'")
    for key in ("adapter", "name"):
        if not model.get(key):
            raise ConfigError(f"{path}: [model] requires '{key}'")

    repeats = int(run.get("repeats", 1))
    if repeats < 1:
        raise ConfigError(f"{path}: repeats must be >= 1")

    conditions = run.get("conditions")
    if conditions is not None and not (
        isinstance(conditions, list) and all(isinstance(c, str) for c in conditions)
    ):
        raise ConfigError(f"{path}: conditions must be a list of strings")

    return RunConfig(
        name=str(run["name"]),
        pack=Path(run["pack"]),
        repeats=repeats,
        shuffle_seed=int(run.get("shuffle_seed", 0)),
        output_dir=Path(run.get("output_dir", "runs")),
        conditions=conditions,
        model=ModelConfig(
            adapter=str(model["adapter"]),
            name=str(model["name"]),
            params=dict(model.get("params", {})),
        ),
        source_path=path,
    )
