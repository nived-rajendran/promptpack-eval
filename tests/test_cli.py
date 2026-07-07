"""End-to-end CLI pipeline smoke test using the offline mock adapter."""

from pathlib import Path

import pytest

from promptpack_eval.cli import main

from conftest import ACBP_CONFIG, EXAMPLE_PACK


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "run.toml"
    config.write_text(
        f'''
[run]
name = "smoke"
pack = "{EXAMPLE_PACK}"
repeats = 1
shuffle_seed = 3
output_dir = "runs"

[model]
adapter = "mock"
name = "mock-small"

[model.params]
seed = 5
''',
        encoding="utf-8",
    )
    return tmp_path


def _only_run_dir(workdir: Path) -> Path:
    (run_dir,) = list((workdir / "runs").iterdir())
    return run_dir


def test_full_pipeline(workdir, capsys):
    assert main(["run", "--config", "run.toml"]) == 0
    run_dir = _only_run_dir(workdir)
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "run_log.csv").is_file()

    assert main(["blind", "--run", str(run_dir), "--seed", "2"]) == 0
    assert main(["score", "--run", str(run_dir), "--scoring", str(ACBP_CONFIG)]) == 0
    assert main(["unblind", "--run", str(run_dir)]) == 0
    assert main(["export", "--run", str(run_dir), "--formats", "csv,jsonl,md,manifest"]) == 0

    exports = run_dir / "exports"
    assert (exports / "scores.csv").is_file()
    assert (exports / "reproducibility_manifest.json").is_file()

    # mock outputs contain no personal data, so the audit is clean
    assert main(["audit", "--path", str(exports)]) == 0
    out = capsys.readouterr().out
    assert "Audit clean" in out


def test_run_rejects_missing_config(workdir, capsys):
    assert main(["run", "--config", "missing.toml"]) == 1
    assert "error:" in capsys.readouterr().err


def test_score_before_blind_fails_cleanly(workdir, capsys):
    assert main(["run", "--config", "run.toml"]) == 0
    run_dir = _only_run_dir(workdir)
    assert main(["score", "--run", str(run_dir), "--scoring", str(ACBP_CONFIG)]) == 1
    assert "blind" in capsys.readouterr().err


def test_audit_flags_findings(workdir, capsys):
    leaky = workdir / "leak"
    leaky.mkdir()
    (leaky / "note.md").write_text("contact: " + "someone" + "@example.org\n", encoding="utf-8")
    assert main(["audit", "--path", str(leaky)]) == 2
    assert "email" in capsys.readouterr().out
