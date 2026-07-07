# Reproducibility

## What is recorded

Per run (`runs/<id>/`):

- **`manifest.json`** — framework version, Python version, OS and CPU
  architecture (generic facts only — no hostname, username, or paths), the
  adapter and backend version, model name and backend digest, all generation
  parameters, pack name/version, the SHA-256 of the pack's prompts file, the
  condition list, repeat count, and the order-shuffle seed.
- **`run_log.csv`** — one row per item: randomized execution order,
  UTC timestamp, prompt SHA-256 / word count / char count, generation
  parameters, output and JSON sidecar SHA-256, backend done-reason,
  completion status, and error text if any.
- **`raw/*.json`** — the full backend response per item (for Ollama this
  includes token counts and timing).

## Seeds

Three seeds control the pipeline, all recorded:

1. `shuffle_seed` (run config) — ordering of the `(condition × repeat)` list.
2. `seed` in `[model.params]` — the backend generation seed. With Ollama,
   the same model digest + parameters + seed is reproducible in principle,
   though backend updates can change outputs; that is why the model digest
   and backend version are recorded.
3. `--seed` on `blind` — the blind-ID assignment shuffle.

## Verifying a run

- Re-render a prompt and compare `prompt_sha256` in the run log; a mismatch
  means the pack changed since the run.
- Re-hash outputs (`shasum -a 256 runs/<id>/raw/<item>.txt`) against
  `output_sha256` to detect post-hoc edits.
- `promptpack-eval export --formats manifest` bundles the run manifest with
  fresh SHA-256 hashes of the run log, scores, and blinded transcripts into
  `exports/reproducibility_manifest.json` — publish this alongside results so
  others can verify file integrity.

## Reporting guidance

When publishing results, state: framework version, pack name/version and
prompts-file hash, model name and digest, backend version, all generation
parameters, all seeds, and the scoring config (which is itself plain TOML and
should be published with the results). Describe scores as transcript-level
surface-language measurements under the stated prompt conditions.
