import json
from pathlib import Path

import pytest

from hkdata import programs as programs_mod
from hkdata.programs import (
    _module_id,
    _parse_docstring,
    build_document,
    build_metadata,
    extract,
    render_registry,
)

SAMPLE = '''"""Module docstring (not indexed)."""


def fitness_rooms() -> list:
    """HK-wide fitness rooms in LCSD sports centres.

    Provides:
        - name, district

    Coverage:
        - Geography: HK-wide
        - Time:      static

    Datasets:   hk-lcsd-facility-facility-fit
    Department: Leisure and Cultural Services Department
    Endpoint:   http://example.com/fitrm.json
    Format:     JSON

    Usage:
        >>> rooms = fitness_rooms()

    Questions:
        - "fitness room near me?"

    Quirks:
        - DMS coordinates
    """
    import json
    import urllib.request

    with urllib.request.urlopen("http://example.com/fitrm.json") as r:
        return json.loads(r.read())


def _private_helper():
    return 1
'''


@pytest.fixture
def prog_dir(tmp_path, monkeypatch):
    d = tmp_path / "programs"
    (d / "lcsd").mkdir(parents=True)
    (d / "lcsd" / "facility.py").write_text(SAMPLE, encoding="utf-8")
    (d / "__init__.py").write_text('"""pkg"""\n', encoding="utf-8")
    (d / "_template.py").write_text('"""template"""\n', encoding="utf-8")
    monkeypatch.setattr(programs_mod, "PROGRAMS_DIR", d)
    return d


def test_parse_docstring_sections():
    doc = """Summary line.

    Provides:
        - name
    Datasets:   hk-x, hk-y
    Department: Foo
    Questions:
        - "q?"
    """
    parsed = _parse_docstring(doc)
    assert parsed["summary"] == "Summary line."
    assert "name" in parsed["provides"]
    assert parsed["datasets"] == ["hk-x", "hk-y"]
    assert parsed["department"] == "Foo"
    assert "q?" in parsed["questions"]


def test_module_id():
    assert _module_id(Path("lcsd/facility.py")) == "lcsd.facility"
    assert _module_id(Path("hko/weather.py")) == "hko.weather"


def test_extract_skips_private_and_template(prog_dir):
    recs = extract()
    ids = {r["id"] for r in recs}
    assert "lcsd.facility:fitness_rooms" in ids
    assert not any(r["func_name"] == "_private_helper" for r in recs)


def test_extract_source_and_signature(prog_dir):
    rec = next(r for r in extract() if r["func_name"] == "fitness_rooms")
    assert rec["signature"] == "fitness_rooms() -> list"
    assert "def fitness_rooms" in rec["source"]
    assert rec["datasets"] == ["hk-lcsd-facility-facility-fit"]
    assert rec["path"] == "lcsd/facility.py"


def test_build_document_and_metadata(prog_dir):
    rec = next(r for r in extract() if r["func_name"] == "fitness_rooms")
    doc = build_document(rec)
    assert "fitness_rooms" in doc
    assert "hk-lcsd-facility-facility-fit" in doc
    meta = build_metadata(rec, "model")
    assert meta["id"] == "lcsd.facility:fitness_rooms"
    assert meta["text_hash"]
    assert meta["model"] == "model"


def test_build_metadata_source_roundtrip(prog_dir):
    rec = next(r for r in extract() if r["func_name"] == "fitness_rooms")
    meta = build_metadata(rec, "m")
    # The source stored in metadata must run standalone (no module imports).
    ns = {}
    exec(meta["source"], ns)
    assert callable(ns["fitness_rooms"])


def test_render_registry(prog_dir, tmp_path):
    recs = extract()
    out = tmp_path / "index.md"
    render_registry(recs, out)
    text = out.read_text(encoding="utf-8")
    assert "Leisure and Cultural Services Department" in text
    assert "lcsd.facility:fitness_rooms" in text


def test_status_counts(prog_dir):
    info = programs_mod.status()
    assert info["functions"] == 1
    assert info["program_files"] == 1
