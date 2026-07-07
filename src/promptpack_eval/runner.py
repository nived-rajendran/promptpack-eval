"""Run loop: randomized order, per-item hashing, run log, and manifest."""

from __future__ import annotations

import csv
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from .adapters import get_adapter
from .config import RunConfig
from .hashing import sha256_file, sha256_text
from .metadata import build_manifest, utc_now_iso, utc_stamp
from .prompts import load_pack

RUN_LOG_FIELDS = [
    "item_id",
    "random_order",
    "timestamp_iso",
    "adapter",
    "model",
    "model_digest",
    "condition",
    "repeat",
    "prompt_sha256",
    "prompt_word_count",
    "prompt_char_count",
    "temperature",
    "top_p",
    "num_ctx",
    "num_predict",
    "seed",
    "output_file",
    "json_file",
    "output_sha256",
    "json_sha256",
    "done_reason",
    "completed",
    "error",
    "shuffle_seed",
]


@dataclass
class RunResult:
    run_dir: Path
    n_total: int
    n_completed: int


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def execute_run(config: RunConfig, run_id: str | None = None) -> RunResult:
    pack = load_pack(config.pack)
    condition_ids = config.conditions or pack.condition_ids()
    for cid in condition_ids:
        pack.get_condition(cid)  # fail fast on unknown conditions

    adapter = get_adapter(config.model.adapter)
    model = config.model.name
    params = config.model.params

    run_id = run_id or f"{config.name}_{utc_stamp()}"
    run_dir = config.output_dir / run_id
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)

    items = [(cid, rep) for cid in condition_ids for rep in range(1, config.repeats + 1)]
    rng = random.Random(config.shuffle_seed)
    rng.shuffle(items)

    manifest = build_manifest(
        run_id=run_id,
        run_name=config.name,
        adapter=config.model.adapter,
        model=model,
        model_digest=adapter.model_digest(model),
        backend_version=adapter.backend_version(),
        params=params,
        pack_name=pack.name,
        pack_version=pack.version,
        prompts_sha256=sha256_file(pack.prompts_file),
        conditions=condition_ids,
        repeats=config.repeats,
        shuffle_seed=config.shuffle_seed,
    )
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    n_completed = 0
    log_path = run_dir / "run_log.csv"
    with log_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_LOG_FIELDS, lineterminator="\n")
        writer.writeheader()

        for order, (condition, repeat) in enumerate(items, start=1):
            item_id = f"{condition}_rep{repeat}"
            prompt = pack.render(condition)
            prompt_sha = sha256_text(prompt)

            result = adapter.generate(model, prompt, params)

            output_file = raw_dir / f"{item_id}.txt"
            json_file = raw_dir / f"{item_id}.json"
            output_file.write_text(result.text, encoding="utf-8")
            json_file.write_text(
                json.dumps(result.raw, indent=2, default=str) + "\n", encoding="utf-8"
            )

            completed = result.ok
            if completed:
                n_completed += 1

            writer.writerow(
                {
                    "item_id": item_id,
                    "random_order": order,
                    "timestamp_iso": utc_now_iso(),
                    "adapter": config.model.adapter,
                    "model": model,
                    "model_digest": manifest["model"]["digest"],
                    "condition": condition,
                    "repeat": repeat,
                    "prompt_sha256": prompt_sha,
                    "prompt_word_count": word_count(prompt),
                    "prompt_char_count": len(prompt),
                    "temperature": params.get("temperature", ""),
                    "top_p": params.get("top_p", ""),
                    "num_ctx": params.get("num_ctx", ""),
                    "num_predict": params.get("num_predict", ""),
                    "seed": params.get("seed", ""),
                    "output_file": f"raw/{output_file.name}",
                    "json_file": f"raw/{json_file.name}",
                    "output_sha256": sha256_file(output_file),
                    "json_sha256": sha256_file(json_file),
                    "done_reason": result.done_reason,
                    "completed": "yes" if completed else "no",
                    "error": result.error,
                    "shuffle_seed": config.shuffle_seed,
                }
            )

    return RunResult(run_dir=run_dir, n_total=len(items), n_completed=n_completed)


def read_run_log(run_dir: Path) -> list[dict[str, str]]:
    with (run_dir / "run_log.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
