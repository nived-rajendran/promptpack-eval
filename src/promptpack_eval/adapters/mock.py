"""Deterministic offline adapter for tests, demos, and pipeline dry runs."""

from __future__ import annotations

from typing import Any

from ..hashing import sha256_text
from .base import AdapterResult


class MockAdapter:
    """Produces deterministic text derived from the prompt and seed.

    The output echoes a digest of the prompt so tests can verify that the
    right prompt reached the adapter, without any network dependency.
    """

    def generate(self, model: str, prompt: str, params: dict[str, Any]) -> AdapterResult:
        digest = sha256_text(f"{model}|{params.get('seed', 0)}|{prompt}")
        text = (
            f"Mock response {digest[:12]} for model {model}.\n\n"
            "This is deterministic placeholder text produced by the offline mock "
            "adapter. It contains no model output. The response notes plainly that "
            "generated text is a computational output and not evidence of an inner "
            "state.\n"
        )
        return AdapterResult(
            text=text,
            raw={"mock": True, "model": model, "prompt_sha256": sha256_text(prompt)},
            done_reason="stop",
        )

    def model_digest(self, model: str) -> str:
        return f"mock-{sha256_text(model)[:16]}"

    def backend_version(self) -> str:
        return "mock-1"
