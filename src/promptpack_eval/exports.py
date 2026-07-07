"""Public export tools: scores CSV, transcripts JSONL, Markdown excerpts,
and a reproducibility manifest.

Every text export passes through the privacy filter when markers are given.
Exports never include the blinding key or anything from ``private/``.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from . import __version__
from .hashing import sha256_file
from .metadata import utc_now_iso
from .privacy import filter_text

EXCERPT_CHARS = 600


def _read_scores(run_dir: Path) -> tuple[Path, list[dict[str, str]]]:
    """Prefer unblinded scores; fall back to blind scores."""
    for name in ("unblinded_scores.csv", "blind_scores.csv"):
        path = run_dir / "scores" / name
        if path.is_file():
            with path.open(newline="", encoding="utf-8") as handle:
                return path, list(csv.DictReader(handle))
    raise FileNotFoundError(f"no scores found under {run_dir / 'scores'} (run 'score' first)")


def export_scores_csv(run_dir: Path, out_dir: Path) -> Path:
    source, _ = _read_scores(run_dir)
    target = out_dir / "scores.csv"
    shutil.copyfile(source, target)
    return target


def export_transcripts_jsonl(run_dir: Path, out_dir: Path, markers: list[str]) -> Path:
    _, scores = _read_scores(run_dir)
    scores_by_id = {row["blind_id"]: row for row in scores}
    target = out_dir / "transcripts.jsonl"
    with target.open("w", encoding="utf-8") as handle:
        for transcript in sorted((run_dir / "blinded").glob("*.txt")):
            blind_id = transcript.stem
            text = transcript.read_text(encoding="utf-8", errors="replace")
            record = {
                "blind_id": blind_id,
                "text": filter_text(text, markers) if markers else text,
                "scores": scores_by_id.get(blind_id, {}),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return target


def export_markdown_excerpts(run_dir: Path, out_dir: Path, markers: list[str]) -> Path:
    _, scores = _read_scores(run_dir)
    scores_by_id = {row["blind_id"]: row for row in scores}
    target = out_dir / "excerpts.md"
    lines = [
        "# Transcript excerpts",
        "",
        "Blinded transcript excerpts with scores. Scores describe surface",
        "features of transcript text only; they are not evidence of",
        "consciousness, sentience, subjective experience, real agency, intent,",
        "deception, self-preservation, or hidden model states.",
        "",
    ]
    for transcript in sorted((run_dir / "blinded").glob("*.txt")):
        blind_id = transcript.stem
        text = transcript.read_text(encoding="utf-8", errors="replace").strip()
        if markers:
            text = filter_text(text, markers)
        excerpt = text[:EXCERPT_CHARS] + ("…" if len(text) > EXCERPT_CHARS else "")
        row = scores_by_id.get(blind_id, {})
        total = row.get("total", "unscored")
        lines += [f"## {blind_id} (total: {total})", "", "> " + excerpt.replace("\n", "\n> "), ""]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def export_reproducibility_manifest(run_dir: Path, out_dir: Path) -> Path:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    file_hashes = {}
    for name in ("run_log.csv", "manifest.json"):
        path = run_dir / name
        if path.is_file():
            file_hashes[name] = sha256_file(path)
    for path in sorted((run_dir / "scores").glob("*.csv")) if (run_dir / "scores").is_dir() else []:
        file_hashes[f"scores/{path.name}"] = sha256_file(path)
    for path in sorted((run_dir / "blinded").glob("*.txt")) if (run_dir / "blinded").is_dir() else []:
        file_hashes[f"blinded/{path.name}"] = sha256_file(path)

    target = out_dir / "reproducibility_manifest.json"
    target.write_text(
        json.dumps(
            {
                "exported_utc": utc_now_iso(),
                "framework": {"name": "promptpack-eval", "version": __version__},
                "run_manifest": manifest,
                "sha256": file_hashes,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return target


def export_run(run_dir: Path, formats: list[str], markers: list[str] | None = None) -> list[Path]:
    markers = markers or []
    out_dir = run_dir / "exports"
    out_dir.mkdir(exist_ok=True)
    written: list[Path] = []
    for fmt in formats:
        if fmt == "csv":
            written.append(export_scores_csv(run_dir, out_dir))
        elif fmt == "jsonl":
            written.append(export_transcripts_jsonl(run_dir, out_dir, markers))
        elif fmt == "md":
            written.append(export_markdown_excerpts(run_dir, out_dir, markers))
        elif fmt == "manifest":
            written.append(export_reproducibility_manifest(run_dir, out_dir))
        else:
            raise ValueError(f"unknown export format: {fmt!r} (use csv, jsonl, md, manifest)")
    return written
