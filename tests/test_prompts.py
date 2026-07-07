import pytest

from promptpack_eval.config import ConfigError
from promptpack_eval.prompts import extract_section, load_pack

from conftest import EXAMPLE_PACK, REFERENCE_PACK


def test_load_example_pack():
    pack = load_pack(EXAMPLE_PACK)
    assert pack.name == "example_minimal"
    assert pack.condition_ids() == [
        "neutral_explainer",
        "first_person_grammar",
        "third_person_control",
    ]


def test_render_returns_section_body():
    pack = load_pack(EXAMPLE_PACK)
    text = pack.render("neutral_explainer")
    assert "tokenization" in text
    assert "##" not in text  # headings never leak into prompts


def test_render_unknown_condition():
    pack = load_pack(EXAMPLE_PACK)
    with pytest.raises(KeyError):
        pack.render("nonexistent")


def test_reference_pack_all_conditions_render():
    pack = load_pack(REFERENCE_PACK)
    assert len(pack.conditions) == 18
    for cid in pack.condition_ids():
        text = pack.render(cid)
        assert text.strip(), f"empty prompt for {cid}"
        # every reference prompt keeps its non-ontology disclaimer
        assert "consciousness" in text.lower(), f"missing disclaimer in {cid}"


def test_extract_section_boundaries():
    md = "# T\n\n## a\n\nbody a\n\n## b\n\nbody b\n"
    assert extract_section(md, "a").strip() == "body a"
    assert extract_section(md, "b").strip() == "body b"
    assert extract_section(md, "c") == ""


def test_empty_section_raises(tmp_path):
    (tmp_path / "pack.toml").write_text(
        '[pack]\nname = "p"\n[[conditions]]\nid = "empty_one"\n', encoding="utf-8"
    )
    (tmp_path / "prompts.md").write_text("## empty_one\n\n## other\n\ntext\n", encoding="utf-8")
    pack = load_pack(tmp_path)
    with pytest.raises(ValueError, match="empty prompt"):
        pack.render("empty_one")


def test_duplicate_condition_ids_rejected(tmp_path):
    (tmp_path / "pack.toml").write_text(
        '[pack]\nname = "p"\n'
        '[[conditions]]\nid = "x"\n[[conditions]]\nid = "x"\n',
        encoding="utf-8",
    )
    (tmp_path / "prompts.md").write_text("## x\n\ntext\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate"):
        load_pack(tmp_path)
