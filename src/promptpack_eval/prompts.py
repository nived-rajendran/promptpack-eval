"""Prompt pack loading and section rendering.

A prompt pack is a directory containing:

- ``pack.toml`` — pack metadata plus a ``[[conditions]]`` array mapping
  condition ids to markdown section headings, and
- a markdown prompts file (default ``prompts.md``) whose ``## <section>``
  blocks hold the prompt text.

Rendering extracts everything between ``## <section>`` and the next ``## ``
heading, matching the section-extraction convention of markdown prompt banks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import ConfigError, load_toml


@dataclass
class Condition:
    id: str
    section: str
    notes: str = ""


@dataclass
class PromptPack:
    name: str
    version: str
    description: str
    path: Path
    prompts_file: Path
    conditions: list[Condition]

    def condition_ids(self) -> list[str]:
        return [c.id for c in self.conditions]

    def get_condition(self, condition_id: str) -> Condition:
        for condition in self.conditions:
            if condition.id == condition_id:
                return condition
        raise KeyError(f"condition not in pack '{self.name}': {condition_id}")

    def render(self, condition_id: str) -> str:
        condition = self.get_condition(condition_id)
        text = extract_section(self.prompts_file.read_text(encoding="utf-8"), condition.section)
        if not text.strip():
            raise ValueError(
                f"condition '{condition_id}' rendered an empty prompt "
                f"(section '## {condition.section}' in {self.prompts_file})"
            )
        return text


def extract_section(markdown: str, section: str) -> str:
    """Return the body of ``## <section>`` up to the next ``## `` heading."""
    lines = markdown.splitlines()
    heading = f"## {section}"
    collected: list[str] = []
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section:
            collected.append(line)
    return "\n".join(collected).strip() + "\n" if collected else ""


def load_pack(path: Path) -> PromptPack:
    pack_file = path / "pack.toml"
    if not pack_file.is_file():
        raise ConfigError(f"not a prompt pack (missing pack.toml): {path}")
    data = load_toml(pack_file)

    meta = data.get("pack", {})
    raw_conditions = data.get("conditions", [])
    if not raw_conditions:
        raise ConfigError(f"{pack_file}: no [[conditions]] defined")

    conditions = []
    seen: set[str] = set()
    for entry in raw_conditions:
        cid = entry.get("id")
        if not cid:
            raise ConfigError(f"{pack_file}: every condition needs an 'id'")
        if cid in seen:
            raise ConfigError(f"{pack_file}: duplicate condition id '{cid}'")
        seen.add(cid)
        conditions.append(
            Condition(id=cid, section=entry.get("section", cid), notes=entry.get("notes", ""))
        )

    prompts_file = path / meta.get("prompts_file", "prompts.md")
    if not prompts_file.is_file():
        raise ConfigError(f"prompts file not found: {prompts_file}")

    return PromptPack(
        name=meta.get("name", path.name),
        version=str(meta.get("version", "0")),
        description=meta.get("description", ""),
        path=path,
        prompts_file=prompts_file,
        conditions=conditions,
    )
