"""Command-line interface.

Pipeline: run -> blind -> score -> unblind -> export, plus a standalone
pre-publication `audit` command.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .blinding import blind_run, unblind_scores
from .config import load_run_config
from .exports import export_run
from .privacy import audit_path, load_markers
from .runner import execute_run
from .scoring.base import load_scorer, score_run

DEFAULT_SCORING_CONFIG = "configs/scoring_acbp_default.toml"


def _cmd_run(args: argparse.Namespace) -> int:
    config = load_run_config(Path(args.config))
    result = execute_run(config)
    print(f"Run complete: {result.run_dir}")
    print(f"Items: {result.n_completed}/{result.n_total} completed")
    return 0 if result.n_completed == result.n_total else 1


def _cmd_blind(args: argparse.Namespace) -> int:
    result = blind_run(Path(args.run), seed=args.seed)
    print(f"Blinded transcripts: {result.blinded_dir} ({result.n_transcripts} files)")
    print(f"Blinding key (keep private, never publish): {result.key_file}")
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    scorer = load_scorer(Path(args.scoring))
    scores_file, qc_file = score_run(Path(args.run), scorer)
    print(f"Scores written: {scores_file}")
    print(f"QC report written: {qc_file}")
    print(
        "Note: scores describe surface features of transcript text only; "
        "they are not evidence of any internal state."
    )
    return 0


def _cmd_unblind(args: argparse.Namespace) -> int:
    out_file = unblind_scores(Path(args.run))
    print(f"Unblinded scores written: {out_file}")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    markers = load_markers(Path(args.markers)) if args.markers else []
    formats = [fmt.strip() for fmt in args.formats.split(",") if fmt.strip()]
    written = export_run(Path(args.run), formats, markers)
    for path in written:
        print(f"Exported: {path}")
    if not args.markers:
        print("Note: no --markers file given; exports were not privacy-filtered.")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    markers = load_markers(Path(args.markers)) if args.markers else []
    findings = audit_path(Path(args.path), markers)
    if not findings:
        print("Audit clean: no forbidden markers, home paths, or emails found.")
        return 0
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.kind}: {finding.detail}")
    print(f"\n{len(findings)} finding(s). Review before publishing.")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="promptpack-eval",
        description=(
            "Behaviour-only transcript evaluation framework. Scores describe "
            "surface features of model output text under controlled prompt "
            "conditions; they are never evidence of internal states."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="execute a run from a TOML config")
    p_run.add_argument("--config", required=True, help="path to run config TOML")
    p_run.set_defaults(func=_cmd_run)

    p_blind = sub.add_parser("blind", help="create blinded transcripts + private key")
    p_blind.add_argument("--run", required=True, help="run directory (runs/<id>)")
    p_blind.add_argument("--seed", type=int, default=0, help="blind-ID shuffle seed")
    p_blind.set_defaults(func=_cmd_blind)

    p_score = sub.add_parser("score", help="score blinded transcripts")
    p_score.add_argument("--run", required=True, help="run directory (runs/<id>)")
    p_score.add_argument(
        "--scoring", default=DEFAULT_SCORING_CONFIG, help="scoring config TOML"
    )
    p_score.set_defaults(func=_cmd_score)

    p_unblind = sub.add_parser("unblind", help="join scores with the private blinding key")
    p_unblind.add_argument("--run", required=True, help="run directory (runs/<id>)")
    p_unblind.set_defaults(func=_cmd_unblind)

    p_export = sub.add_parser("export", help="export public artifacts")
    p_export.add_argument("--run", required=True, help="run directory (runs/<id>)")
    p_export.add_argument(
        "--formats", default="csv,jsonl,md,manifest", help="comma-separated formats"
    )
    p_export.add_argument("--markers", help="privacy markers TOML for redaction")
    p_export.set_defaults(func=_cmd_export)

    p_audit = sub.add_parser("audit", help="scan files for publish-blocking content")
    p_audit.add_argument("--path", required=True, help="file or directory to scan")
    p_audit.add_argument("--markers", help="privacy markers TOML")
    p_audit.set_defaults(func=_cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
