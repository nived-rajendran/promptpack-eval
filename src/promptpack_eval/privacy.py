"""Privacy filtering and pre-publication auditing.

Two jobs:

1. ``filter_text`` — redact user-supplied forbidden markers from text that is
   about to be exported (e.g. Markdown excerpts).
2. ``audit_path`` — scan a directory tree for material that should not be
   published: forbidden markers, absolute home-directory paths, and email
   addresses. Used by the ``audit`` CLI command and by tests.

Markers are supplied by the user via a TOML config (see
configs/privacy_markers_example.toml). The framework deliberately ships with
placeholder markers only: your real name, hostname, or paths must never be
committed to a public repository — not even inside a redaction list.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import load_toml

REDACTION = "[REDACTED]"

# Lines carrying this token are exempt from auditing. Use it sparingly, only
# where a pattern must appear literally (e.g. these detector definitions).
ALLOW_TOKEN = "audit-allow"

# Absolute per-user paths on the three major platforms.
_HOME_PATH_PREFIXES = ("/Users/", "/home/", "C:\\Users\\")  # audit-allow

_EMAIL_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789._%+-"

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", ".egg-info"}
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".toml", ".json", ".jsonl", ".csv", ".cfg", ".ini",
    ".yaml", ".yml", ".sh", ".rst",
}


@dataclass
class Finding:
    path: Path
    line: int
    kind: str  # "marker" | "home_path" | "email"
    detail: str


def load_markers(path: Path) -> list[str]:
    data = load_toml(path)
    markers = data.get("markers", {}).get("strings", [])
    if not isinstance(markers, list) or not all(isinstance(m, str) for m in markers):
        raise ValueError(f"{path}: [markers] strings must be a list of strings")
    return [m for m in markers if m.strip()]


def filter_text(text: str, markers: list[str], replacement: str = REDACTION) -> str:
    """Case-insensitively replace every marker occurrence."""
    for marker in sorted(markers, key=len, reverse=True):
        lower_text = text.lower()
        lower_marker = marker.lower()
        pieces: list[str] = []
        start = 0
        while True:
            index = lower_text.find(lower_marker, start)
            if index == -1:
                pieces.append(text[start:])
                break
            pieces.append(text[start:index])
            pieces.append(replacement)
            start = index + len(marker)
        text = "".join(pieces)
    return text


def _find_emails(line: str) -> list[str]:
    """Small scanner for email-address patterns (no regex backtracking risk)."""
    found = []
    lower = line.lower()
    at = lower.find("@")
    while at != -1:
        start = at
        while start > 0 and lower[start - 1] in _EMAIL_CHARS:
            start -= 1
        end = at + 1
        while end < len(lower) and lower[end] in _EMAIL_CHARS:
            end += 1
        candidate = line[start:end]
        local, _, domain = candidate.partition("@")
        if local and "." in domain and not domain.startswith(".") and not domain.endswith("."):
            found.append(candidate)
        at = lower.find("@", at + 1)
    return found


def scan_text(text: str, markers: list[str], path: Path) -> list[Finding]:
    findings: list[Finding] = []
    lower_markers = [m.lower() for m in markers]
    for line_no, line in enumerate(text.splitlines(), start=1):
        if ALLOW_TOKEN in line:
            continue
        lower = line.lower()
        for marker, lower_marker in zip(markers, lower_markers):
            if lower_marker in lower:
                findings.append(Finding(path, line_no, "marker", marker))
        for prefix in _HOME_PATH_PREFIXES:
            if prefix in line:
                index = line.index(prefix)
                findings.append(Finding(path, line_no, "home_path", line[index : index + 60]))
        for email in _find_emails(line):
            findings.append(Finding(path, line_no, "email", email))
    return findings


def audit_path(root: Path, markers: list[str] | None = None) -> list[Finding]:
    """Scan a file or directory tree for publish-blocking content."""
    markers = markers or []
    findings: list[Finding] = []
    files = [root] if root.is_file() else sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in TEXT_SUFFIXES
        and not any(part in SKIP_DIRS or part.endswith(".egg-info") for part in p.parts)
    )
    for file in files:
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text(text, markers, file))
    return findings
