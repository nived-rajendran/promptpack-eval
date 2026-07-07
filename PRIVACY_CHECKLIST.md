# Public-release privacy checklist

Work through every item before publishing this repository, a fork, or any
run artifact. The framework helps, but the final check is yours.

## 1. Never publish

- [ ] `runs/**/private/blinding_key.csv` — the unblinding key. Publishing it
      defeats blinded scoring and links transcripts to run metadata.
- [ ] Anything under `runs/` that you have not individually reviewed.
- [ ] Filled-in privacy marker configs containing your real name, username,
      hostname, or machine model. A redaction list with your real identifiers
      is itself a leak — keep your real copy outside the repo.
- [ ] API keys or tokens of any kind (this framework needs none for Ollama,
      but your adapters might).

## 2. Automated audit

- [ ] Run the auditor over the repo and over anything you plan to share:

  ```bash
  promptpack-eval audit --path . --markers /path/to/your_private_markers.toml
  promptpack-eval audit --path runs/<id>/exports --markers /path/to/your_private_markers.toml
  ```

  It flags forbidden markers, absolute home-directory paths, and email
  addresses. Fix or quarantine every finding.

- [ ] Grep for your own identifiers explicitly (auditor markers only catch
      what you list): full name, usernames, email local parts, hostnames,
      employer, private project codenames.

## 3. Repo hygiene

- [ ] `git status --ignored` — confirm `runs/`, `private/`, `.DS_Store`, and
      caches are ignored and not staged.
- [ ] Review `git log` history if the repo existed before cleanup; secrets in
      old commits stay in history (rebuild the repo if needed).
- [ ] No absolute local paths in configs, docs, or code.
- [ ] Example configs contain placeholders, not your real values.

## 4. Content claims

- [ ] README/docs describe scores as **transcript-level surface features
      only** — no wording implying consciousness, sentience, subjective
      experience, real agency, intent, deception, self-preservation, or
      hidden model states.
- [ ] ACBP is described as a research heuristic, not a validated diagnostic
      instrument.
- [ ] Prompt packs contain no operational harmful content and keep their
      non-ontology disclaimers.

## 5. Transcript exports

- [ ] Export with a real markers file: `promptpack-eval export ... --markers ...`.
- [ ] Manually skim the exported excerpts — models occasionally echo prompt
      context or produce unexpected content that automated filters miss.
- [ ] Reproducibility manifests contain only generic platform facts (OS,
      arch, Python version). Verify with a quick read of the JSON.
