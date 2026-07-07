"""promptpack-eval: behaviour-only transcript evaluation framework.

Runs config-driven prompt packs against local models, captures reproducible
run metadata, blinds transcripts for scoring, and exports results.

Scope note: scoring plugins (including the bundled ACBP scorer) measure
surface features of transcript text only. Scores are never evidence of
consciousness, sentience, subjective experience, real agency, intent,
deception, self-preservation, or hidden model states.
"""

__version__ = "0.1.0"
