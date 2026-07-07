import csv
import json

import pytest

from promptpack_eval.blinding import blind_run, unblind_scores
from promptpack_eval.exports import export_run
from promptpack_eval.scoring.base import load_scorer, score_run

from conftest import ACBP_CONFIG


@pytest.fixture
def scored_run(run_dir):
    blind_run(run_dir, seed=7)
    score_run(run_dir, load_scorer(ACBP_CONFIG))
    unblind_scores(run_dir)
    return run_dir


def test_export_all_formats(scored_run):
    written = export_run(scored_run, ["csv", "jsonl", "md", "manifest"])
    names = {path.name for path in written}
    assert names == {
        "scores.csv",
        "transcripts.jsonl",
        "excerpts.md",
        "reproducibility_manifest.json",
    }
    for path in written:
        assert path.is_file() and path.stat().st_size > 0


def test_scores_csv_prefers_unblinded(scored_run):
    (path,) = export_run(scored_run, ["csv"])
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert "condition" in rows[0]  # unblinded variant carries join fields


def test_jsonl_one_record_per_transcript(scored_run):
    (path,) = export_run(scored_run, ["jsonl"])
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    n_blinded = len(list((scored_run / "blinded").glob("*.txt")))
    assert len(records) == n_blinded
    for record in records:
        assert record["blind_id"].startswith("BT_")
        assert record["text"]
        assert record["scores"]["total"].isdigit()


def test_exports_are_privacy_filtered(scored_run):
    # the mock adapter's output contains the word "deterministic"
    written = export_run(scored_run, ["jsonl", "md"], markers=["deterministic"])
    for path in written:
        content = path.read_text(encoding="utf-8")
        assert "deterministic" not in content.lower()
        assert "[REDACTED]" in content


def test_manifest_hashes_and_no_host_identity(scored_run):
    (path,) = export_run(scored_run, ["manifest"])
    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["sha256"]["run_log.csv"]
    assert any(name.startswith("blinded/") for name in manifest["sha256"])
    environment = manifest["run_manifest"]["environment"]
    assert set(environment) == {"python", "os", "arch"}  # no hostname/username


def test_unknown_format_rejected(scored_run):
    with pytest.raises(ValueError, match="unknown export format"):
        export_run(scored_run, ["xml"])
