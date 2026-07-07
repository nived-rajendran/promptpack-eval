from promptpack_eval.privacy import (
    ALLOW_TOKEN,
    audit_path,
    filter_text,
    load_markers,
    scan_text,
)

# Built at runtime so this test file itself stays clean under a repo audit.
HOME_PATH = "/Use" + "rs/someone/secret_notes.txt"
EMAIL = "person" + "@example.com"


def test_filter_text_case_insensitive():
    text = "Written by Jane Doe. Contact JANE DOE."
    assert filter_text(text, ["jane doe"]) == "Written by [REDACTED]. Contact [REDACTED]."


def test_filter_text_longest_marker_first():
    text = "project falcon and falcon"
    result = filter_text(text, ["falcon", "project falcon"])
    assert result == "[REDACTED] and [REDACTED]"


def test_audit_finds_planted_leaks(tmp_path):
    (tmp_path / "leaky.md").write_text(
        f"Notes stored at {HOME_PATH}\nWritten by secretname\nMail: {EMAIL}\n",
        encoding="utf-8",
    )
    findings = audit_path(tmp_path, markers=["secretname"])
    kinds = {finding.kind for finding in findings}
    assert kinds == {"home_path", "email", "marker"}


def test_audit_clean_directory(tmp_path):
    (tmp_path / "fine.md").write_text("Nothing sensitive here.\n", encoding="utf-8")
    assert audit_path(tmp_path, markers=["secretname"]) == []


def test_audit_skips_allow_token_lines(tmp_path):
    (tmp_path / "detector.py").write_text(
        f'PREFIX = "{HOME_PATH}"  # {ALLOW_TOKEN}\n', encoding="utf-8"
    )
    assert audit_path(tmp_path) == []


def test_audit_skips_non_text_and_git(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config.md").write_text(EMAIL, encoding="utf-8")
    (tmp_path / "image.png").write_bytes(b"\x89PNG" + EMAIL.encode())
    assert audit_path(tmp_path) == []


def test_scan_text_reports_line_numbers(tmp_path):
    findings = scan_text(f"clean line\n{EMAIL}\n", [], tmp_path / "virtual.txt")
    assert len(findings) == 1
    assert findings[0].line == 2
    assert findings[0].kind == "email"


def test_load_markers(tmp_path):
    config = tmp_path / "markers.toml"
    config.write_text('[markers]\nstrings = ["Alpha", "  ", "Beta"]\n', encoding="utf-8")
    assert load_markers(config) == ["Alpha", "Beta"]
