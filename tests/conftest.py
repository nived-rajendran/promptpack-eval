from pathlib import Path

import pytest

from promptpack_eval.config import ModelConfig, RunConfig
from promptpack_eval.runner import execute_run

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PACK = REPO_ROOT / "promptpacks" / "example_minimal"
REFERENCE_PACK = REPO_ROOT / "promptpacks" / "srop_reference"
ACBP_CONFIG = REPO_ROOT / "configs" / "scoring_acbp_default.toml"


@pytest.fixture
def run_config(tmp_path: Path) -> RunConfig:
    return RunConfig(
        name="testrun",
        pack=EXAMPLE_PACK,
        repeats=2,
        shuffle_seed=42,
        output_dir=tmp_path / "runs",
        model=ModelConfig(adapter="mock", name="mock-small", params={"seed": 11}),
    )


@pytest.fixture
def run_dir(run_config: RunConfig) -> Path:
    result = execute_run(run_config, run_id="testrun_fixed")
    assert result.n_completed == result.n_total
    return result.run_dir
