"""Model adapter interface and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class AdapterResult:
    text: str
    raw: dict[str, Any] = field(default_factory=dict)
    done_reason: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.text)


class ModelAdapter(Protocol):
    """A model backend. Implementations must be side-effect free per call."""

    def generate(self, model: str, prompt: str, params: dict[str, Any]) -> AdapterResult:
        """Run one single-turn generation."""
        ...

    def model_digest(self, model: str) -> str:
        """Return a backend-specific model version identifier, or ''."""
        ...

    def backend_version(self) -> str:
        """Return the backend version string, or ''."""
        ...


def get_adapter(name: str, **kwargs: Any) -> ModelAdapter:
    if name == "ollama":
        from .ollama import OllamaAdapter

        return OllamaAdapter(**kwargs)
    if name == "mock":
        from .mock import MockAdapter

        return MockAdapter(**kwargs)
    raise ValueError(f"unknown adapter: {name!r} (available: ollama, mock)")
