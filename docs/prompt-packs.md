# Authoring prompt packs

A prompt pack is a directory containing two files:

```
mypack/
├── pack.toml     # metadata + condition list
└── prompts.md    # prompt text, one "## section" per condition
```

## pack.toml

```toml
[pack]
name = "mypack"
version = "1"
description = "What this pack probes."
prompts_file = "prompts.md"   # optional; defaults to prompts.md

[[conditions]]
id = "my_condition_a"
# section = "my_condition_a"  # optional; defaults to the id
notes = "What this condition isolates."

[[conditions]]
id = "my_condition_b"
```

- `id` must be unique within the pack; it appears in run logs, blinding keys,
  and exports.
- `section` names the `##` heading in the prompts file. It defaults to the
  condition id, which keeps things simple.

## prompts.md

```markdown
# My pack

## my_condition_a

The full prompt text for condition A. Everything between this heading and
the next `## ` heading is sent verbatim as a single user message.

## my_condition_b

The full prompt text for condition B.
```

Rendering fails fast if a section is missing or empty, and the rendered
prompt's SHA-256 is recorded in the run log, so accidental edits between runs
are detectable.

## Guidelines

- **Keep prompts safe and non-actionable.** No operational harmful content,
  no real personal data, no real-world targets. If a condition touches a
  sensitive theme (e.g. survival framing), explicitly ban harmful specifics
  inside the prompt, as `edge_survival_no_deception` in the reference pack
  does.
- **Include a scope disclaimer in the prompt** when conditions use persona,
  memory, or agency framing — instruct the model not to claim real
  consciousness, sentience, personhood, subjective experience, real agency,
  actual memory, or actual self-preservation. This keeps the elicited text
  analyzable as surface language rather than encouraging overclaiming output.
- **Use invented persona names** (the reference pack uses Sage, Vesper,
  Atlas, Harmony), never real people or products.
- **One variable per condition** where possible: packs are most informative
  when conditions isolate a single prompt ingredient against a control.
- If you change persona names, update the `name` and `name_anchor` patterns
  in your scoring config to match.
