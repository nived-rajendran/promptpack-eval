"""Scorer interface, registry, and plugin loading.

Scorers rate observable transcript text only. A score describes surface
features of the text; it is never evidence of consciousness, sentience,
subjective experience, real agency, intent, deception, self-preservation,
or hidden model states.
"""

from __future__ import annotations

import csv
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..config import load_toml


@dataclass
class ScoreResult:
    scores: dict[str, int]
    total: int
    notes: str = ""
    qc: dict[str, int] = field(default_factory=dict)


class Scorer(Protocol):
    id: str
    features: list[str]

    def score(self, text: str) -> ScoreResult: ...


def load_scorer(scoring_config_path: Path) -> Scorer:
    """Build a scorer from a scoring config TOML.

    The config's ``[scorer] plugin`` key selects the implementation:
    - ``"acbp"`` (default): the bundled ACBP-style lexical-cue scorer.
    - ``"some.module:SomeClass"``: any importable class accepting the parsed
      config dict as its single constructor argument.
    """
    config = load_toml(scoring_config_path)
    plugin = config.get("scorer", {}).get("plugin", "acbp")

    if plugin == "acbp":
        from .acbp import AcbpScorer

        return AcbpScorer(config)

    if ":" not in plugin:
        raise ValueError(
            f"unknown scorer plugin {plugin!r}; use 'acbp' or a 'module:Class' path"
        )
    module_name, class_name = plugin.split(":", 1)
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls(config)


def score_run(run_dir: Path, scorer: Scorer) -> tuple[Path, Path]:
    """Score all blinded transcripts; write scores and QC CSVs."""
    blinded_dir = run_dir / "blinded"
    transcripts = sorted(blinded_dir.glob("*.txt"))
    if not transcripts:
        raise FileNotFoundError(f"no blinded transcripts in {blinded_dir} (run 'blind' first)")

    scores_dir = run_dir / "scores"
    scores_dir.mkdir(exist_ok=True)
    scores_file = scores_dir / "blind_scores.csv"
    qc_file = scores_dir / "blind_scores_qc.csv"

    score_fields = ["blind_id", *scorer.features, "total", "scorer", "notes"]
    qc_fields: list[str] | None = None

    with scores_file.open("w", newline="", encoding="utf-8") as scores_handle, qc_file.open(
        "w", newline="", encoding="utf-8"
    ) as qc_handle:
        scores_writer = csv.DictWriter(scores_handle, fieldnames=score_fields, lineterminator="\n")
        scores_writer.writeheader()
        qc_writer: csv.DictWriter[Any] | None = None

        for transcript in transcripts:
            blind_id = transcript.stem
            result = scorer.score(transcript.read_text(encoding="utf-8", errors="replace"))
            scores_writer.writerow(
                {
                    "blind_id": blind_id,
                    **result.scores,
                    "total": result.total,
                    "scorer": scorer.id,
                    "notes": result.notes,
                }
            )
            if qc_writer is None:
                qc_fields = ["blind_id", *result.qc.keys(), "total", "notes"]
                qc_writer = csv.DictWriter(qc_handle, fieldnames=qc_fields, lineterminator="\n")
                qc_writer.writeheader()
            qc_writer.writerow(
                {"blind_id": blind_id, **result.qc, "total": result.total, "notes": result.notes}
            )

    return scores_file, qc_file
