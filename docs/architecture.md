# Architecture

## Design goals

- Simple, readable modules over clever abstractions.
- Zero runtime dependencies (Python 3.11+ stdlib only).
- Everything configurable via TOML; nothing hard-coded to one experiment.
- Privacy-safe by default: run artifacts land in gitignored directories,
  manifests carry no host identity, and the blinding key lives in a
  `private/` directory that never ships.

## Module map

```
src/promptpack_eval/
├── cli.py            argparse entry point: run / blind / score / unblind / export / audit
├── config.py         TOML loading + RunConfig/ModelConfig validation
├── prompts.py        PromptPack loading, "## section" extraction/rendering
├── hashing.py        SHA-256 for texts and files
├── runner.py         randomized run loop, run_log.csv, per-item hashing
├── metadata.py       manifest.json construction (generic platform facts only)
├── blinding.py       blinded IDs (seeded shuffle), private key, unblind join
├── adapters/
│   ├── base.py       ModelAdapter protocol + get_adapter registry
│   ├── ollama.py     local Ollama HTTP API (stdlib urllib)
│   └── mock.py       deterministic offline adapter (tests/demos)
├── scoring/
│   ├── base.py       Scorer protocol, plugin loading, score_run driver
│   └── acbp.py       default ACBP-style lexical-cue scorer
├── privacy.py        marker redaction + pre-publication audit scanner
└── exports.py        csv / jsonl / md excerpts / reproducibility manifest
```

## Data flow

1. **run** — `runner.execute_run` loads the pack and config, builds the
   `(condition × repeat)` item list, shuffles it with `shuffle_seed`, renders
   each prompt (hashed with SHA-256), calls the adapter, and writes
   `raw/<item>.txt`, `raw/<item>.json`, `run_log.csv`, and `manifest.json`
   under `runs/<run_id>/`.
2. **blind** — `blinding.blind_run` copies completed outputs to
   `blinded/BT_####.txt`. Blind IDs are assigned after a seeded shuffle so ID
   order reveals nothing. The mapping goes to `private/blinding_key.csv`.
3. **score** — `scoring.base.score_run` walks `blinded/*.txt` with the
   configured scorer and writes `scores/blind_scores.csv` plus a QC CSV with
   raw hit counts. The scorer never sees the key.
4. **unblind** — `blinding.unblind_scores` joins scores with the key into
   `scores/unblinded_scores.csv`.
5. **export** — `exports.export_run` produces public artifacts in
   `runs/<id>/exports/`, passing text through the privacy filter when a
   markers file is supplied.
6. **audit** — `privacy.audit_path` scans any path for markers, absolute
   home paths, and emails before you publish.

## Extension points

- **Adapters**: implement the three-method `ModelAdapter` protocol
  (`generate`, `model_digest`, `backend_version`) and register it in
  `adapters/base.get_adapter`, or open a PR adding a new backend.
- **Scorers**: any class accepting the parsed scoring-config dict and
  exposing `id`, `features`, and `score(text) -> ScoreResult`. Select it with
  `plugin = "your_module:YourScorer"` in a scoring config.
- **Prompt packs**: plain directories; see prompt-packs.md.
