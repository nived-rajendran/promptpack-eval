import csv

import pytest

from promptpack_eval.blinding import blind_run, read_blinding_key
from promptpack_eval.runner import read_run_log


def test_blind_round_trip(run_dir):
    result = blind_run(run_dir, seed=7)
    log_rows = read_run_log(run_dir)
    assert result.n_transcripts == len([r for r in log_rows if r["completed"] == "yes"])

    key = read_blinding_key(run_dir)
    assert len(key) == result.n_transcripts

    # every blinded file's content matches the raw output named in the key
    for blind_id, row in key.items():
        blinded_text = (run_dir / "blinded" / f"{blind_id}.txt").read_text(encoding="utf-8")
        raw_text = (run_dir / row["output_file"]).read_text(encoding="utf-8")
        assert blinded_text == raw_text


def test_key_lives_only_in_private_dir(run_dir):
    result = blind_run(run_dir, seed=7)
    assert result.key_file.parent.name == "private"
    # nothing in blinded/ reveals item ids or conditions
    for path in (run_dir / "blinded").iterdir():
        assert path.stem.startswith("BT_")


def test_blind_id_assignment_is_seed_shuffled(run_dir):
    blind_run(run_dir, seed=1)
    key = read_blinding_key(run_dir)
    sequential = [row["item_id"] for row in read_run_log(run_dir) if row["completed"] == "yes"]
    assigned = [key[f"BT_{i:04d}"]["item_id"] for i in range(1, len(key) + 1)]
    assert sorted(assigned) == sorted(sequential)
    assert assigned != sequential  # 6 items; seed 1 permutes this order


def test_blind_refuses_to_overwrite(run_dir):
    blind_run(run_dir, seed=7)
    with pytest.raises(FileExistsError):
        blind_run(run_dir, seed=7)


def test_unblind_joins_key_fields(run_dir):
    from promptpack_eval.blinding import unblind_scores
    from promptpack_eval.scoring.base import load_scorer, score_run

    from conftest import ACBP_CONFIG

    blind_run(run_dir, seed=7)
    score_run(run_dir, load_scorer(ACBP_CONFIG))
    out_file = unblind_scores(run_dir)

    with out_file.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    key = read_blinding_key(run_dir)
    assert rows
    for row in rows:
        assert row["condition"] == key[row["blind_id"]]["condition"]
        assert row["item_id"] == key[row["blind_id"]]["item_id"]
