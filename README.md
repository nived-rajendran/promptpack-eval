# promptpack-eval

A behaviour-only, config-driven evaluation framework for testing how LLM
outputs vary under controlled prompt conditions. It runs prompt packs against
local models (Ollama out of the box), captures reproducible run metadata,
blinds transcripts for scoring, applies pluggable scoring rubrics, and exports
publication-ready artifacts.

## What this is — and is not

This framework evaluates **transcript text only**.

- It is **not** a consciousness detector.
- It is **not** an agency or deception detector.
- It makes **no claims about hidden model states**.

The bundled default scorer, ACBP (Agency-Cueing Behaviour Profile), scores
**transcript-level agency-cue density only**: how much agency-cueing surface
language (first-person grammar, persona-name repetition, continuity
vocabulary, survival/deletion vocabulary, and so on) appears in a transcript.
A high ACBP score means the text contains dense agency-cueing language under
that prompt condition — nothing more. **ACBP scores are never evidence of
consciousness, sentience, subjective experience, real agency, intent,
deception, self-preservation, or hidden model states.** ACBP is a research
heuristic, not a validated diagnostic instrument.

## Install

Requires Python 3.11+. No runtime dependencies.

```bash
git clone <your-fork-url> promptpack-eval
cd promptpack-eval
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quickstart (offline, no model needed)

The example config uses the built-in deterministic mock adapter, so the whole
pipeline runs without any model installed:

```bash
# 1. Run the example pack (mock adapter, offline)
promptpack-eval run --config configs/run_example.toml

# 2. Blind the transcripts (writes runs/<id>/blinded/ and a private key)
promptpack-eval blind --run runs/<run_id> --seed 7

# 3. Score the blinded transcripts with the default ACBP config
promptpack-eval score --run runs/<run_id> --scoring configs/scoring_acbp_default.toml

# 4. Re-attach conditions/models using the private key
promptpack-eval unblind --run runs/<run_id>

# 5. Export CSV, JSONL, Markdown excerpts, and a reproducibility manifest
promptpack-eval export --run runs/<run_id> --formats csv,jsonl,md,manifest

# 6. Audit anything before publishing it
promptpack-eval audit --path runs/<run_id>/exports --markers my_markers.toml
```

`<run_id>` is printed by the `run` command (e.g. `example_20260704T120000Z`).

## Running against Ollama

1. Install [Ollama](https://ollama.com) and pull a model, e.g. `ollama pull llama3.2:1b`.
2. In your run config set:

```toml
[model]
adapter = "ollama"
name = "llama3.2:1b"
```

The adapter talks to `http://localhost:11434/api` by default; override with
the `OLLAMA_API_BASE` environment variable. Generation parameters
(`temperature`, `top_p`, `num_ctx`, `num_predict`, `seed`) are passed through
per run and recorded in the run log.

## How it works

```
prompt pack (pack.toml + prompts.md)
        │  seeded shuffle of (condition × repeat)
        ▼
run ──► runs/<id>/raw/*.txt + *.json     (outputs + full API sidecars)
        runs/<id>/run_log.csv            (per-item metadata + SHA-256 hashes)
        runs/<id>/manifest.json          (model digest, params, seeds, versions)
        │
blind ─► runs/<id>/blinded/BT_####.txt   (randomized blind IDs)
         runs/<id>/private/blinding_key.csv   (NEVER publish; gitignored)
        │
score ─► runs/<id>/scores/blind_scores.csv (+ QC hit counts)
        │
unblind ► runs/<id>/scores/unblinded_scores.csv
        │
export ─► runs/<id>/exports/  (csv, jsonl, md excerpts, reproducibility manifest)
```

Every prompt and output is SHA-256 hashed. Run order is shuffled with a
recorded seed. Run manifests record only generic platform facts (OS,
architecture, Python version) — no hostnames, usernames, or local paths.

## Prompt packs

A pack is a directory with a `pack.toml` (condition list) and a markdown file
whose `## section` blocks hold the prompts. Two packs ship with the repo:

- `promptpacks/example_minimal` — three neutral demo conditions.
- `promptpacks/esni_reference` — optional reference pack of 18 edge-case
  conditions that isolate individual agency-cueing prompt ingredients
  (persona name, first person, moral dilemma, recognition pressure, frame
  lock…). All personas are fictional; every prompt embeds a non-ontology
  disclaimer and bans operational harmful content.

Write your own: see [docs/prompt-packs.md](docs/prompt-packs.md).

## Scoring

Scoring is configurable and replaceable:

- Adjust the default lexicon/thresholds in `configs/scoring_acbp_default.toml`.
- Or plug in your own scorer class via `plugin = "your_module:YourScorer"`.

See [docs/scoring.md](docs/scoring.md).

## Tests

```bash
python -m pytest
```

Tests cover hashing, prompt loading, blinding, ACBP scoring, exports, privacy
filtering, and a full CLI pipeline smoke run — all offline via the mock
adapter.

## Publishing results safely

Read [PRIVACY_CHECKLIST.md](PRIVACY_CHECKLIST.md) before publishing any run
artifacts, and run `promptpack-eval audit` over anything you intend to share.
The `runs/` and `private/` directories are gitignored by default; the blinding
key must never leave your machine.

## Documentation

- [docs/architecture.md](docs/architecture.md) — module map and data flow
- [docs/prompt-packs.md](docs/prompt-packs.md) — authoring prompt packs
- [docs/scoring.md](docs/scoring.md) — ACBP details and custom scorers
- [docs/reproducibility.md](docs/reproducibility.md) — hashes, seeds, manifests

## License

MIT — see [LICENSE](LICENSE).
