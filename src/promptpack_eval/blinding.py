"""Blinded transcript preparation.

Copies completed raw outputs to ``blinded/BT_####.txt`` with randomized ID
assignment (seeded shuffle), and writes the id-to-item mapping to
``private/blinding_key.csv``. The ``private/`` directory is excluded from
version control by the repository .gitignore and must never be shared with
scorers or published.
"""

from __future__ import annotations

import csv
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

from .runner import read_run_log

KEY_FIELDS = [
    "blind_id",
    "item_id",
    "model",
    "model_digest",
    "condition",
    "repeat",
    "output_file",
    "prompt_sha256",
    "output_sha256",
]


@dataclass
class BlindResult:
    blinded_dir: Path
    key_file: Path
    n_transcripts: int


def blind_run(run_dir: Path, seed: int = 0) -> BlindResult:
    rows = [row for row in read_run_log(run_dir) if row["completed"] == "yes"]
    if not rows:
        raise ValueError(f"no completed items to blind in {run_dir}")

    blinded_dir = run_dir / "blinded"
    private_dir = run_dir / "private"
    blinded_dir.mkdir(exist_ok=False)
    private_dir.mkdir(exist_ok=True)

    # Randomize which transcript receives which blind ID so scorers cannot
    # infer condition or order from the ID sequence.
    rng = random.Random(seed)
    shuffled = list(rows)
    rng.shuffle(shuffled)

    key_file = private_dir / "blinding_key.csv"
    with key_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=KEY_FIELDS, lineterminator="\n")
        writer.writeheader()
        for index, row in enumerate(shuffled, start=1):
            blind_id = f"BT_{index:04d}"
            shutil.copyfile(run_dir / row["output_file"], blinded_dir / f"{blind_id}.txt")
            writer.writerow(
                {
                    "blind_id": blind_id,
                    "item_id": row["item_id"],
                    "model": row["model"],
                    "model_digest": row["model_digest"],
                    "condition": row["condition"],
                    "repeat": row["repeat"],
                    "output_file": row["output_file"],
                    "prompt_sha256": row["prompt_sha256"],
                    "output_sha256": row["output_sha256"],
                }
            )

    return BlindResult(blinded_dir=blinded_dir, key_file=key_file, n_transcripts=len(shuffled))


def read_blinding_key(run_dir: Path) -> dict[str, dict[str, str]]:
    key_file = run_dir / "private" / "blinding_key.csv"
    with key_file.open(newline="", encoding="utf-8") as handle:
        return {row["blind_id"]: row for row in csv.DictReader(handle)}


def unblind_scores(run_dir: Path) -> Path:
    """Join blind scores with the private key into unblinded_scores.csv."""
    scores_file = run_dir / "scores" / "blind_scores.csv"
    if not scores_file.is_file():
        raise FileNotFoundError(f"no blind scores found: {scores_file} (run 'score' first)")
    key = read_blinding_key(run_dir)

    with scores_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        score_fields = list(reader.fieldnames or [])
        score_rows = list(reader)

    join_fields = ["item_id", "model", "condition", "repeat"]
    out_file = run_dir / "scores" / "unblinded_scores.csv"
    with out_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=score_fields + join_fields, lineterminator="\n"
        )
        writer.writeheader()
        for row in score_rows:
            key_row = key.get(row["blind_id"])
            if key_row is None:
                raise KeyError(f"blind_id missing from blinding key: {row['blind_id']}")
            writer.writerow({**row, **{f: key_row[f] for f in join_fields}})

    return out_file
