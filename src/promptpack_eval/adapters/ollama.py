"""Ollama adapter using the local HTTP API (stdlib only, no dependencies)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from .base import AdapterResult

DEFAULT_BASE_URL = "http://localhost:11434/api"
KNOWN_OPTIONS = ("temperature", "top_p", "num_ctx", "num_predict", "seed")


class OllamaAdapter:
    def __init__(self, base_url: str | None = None, timeout: float = 600.0) -> None:
        self.base_url = (base_url or os.environ.get("OLLAMA_API_BASE") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate(self, model: str, prompt: str, params: dict[str, Any]) -> AdapterResult:
        options = {key: params[key] for key in KNOWN_OPTIONS if key in params}
        payload = {
            "model": model,
            "stream": False,
            "think": False,
            "keep_alive": params.get("keep_alive", 0),
            "options": options,
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            raw = self._request("/chat", payload)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return AdapterResult(text="", error=f"ollama request failed: {exc}")

        text = (raw.get("message") or {}).get("content", "") or ""
        result = AdapterResult(text=text, raw=raw, done_reason=raw.get("done_reason", "") or "")
        if not text:
            result.error = "empty message.content in Ollama response"
        return result

    def model_digest(self, model: str) -> str:
        try:
            tags = self._request("/tags")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return ""
        for entry in tags.get("models", []):
            name = entry.get("name", "")
            if name == model or name.removesuffix(":latest") == model:
                return entry.get("digest", "")
        return ""

    def backend_version(self) -> str:
        try:
            return self._request("/version").get("version", "")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return ""
