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


# ---------------------------------------------------------------------------
# Self-contained source (module-level helpers are inlined)
# ---------------------------------------------------------------------------

HELPER_SAMPLE = '''"""Module with a private helper and a constant."""

_BASE = "https://example.com"


def _url(name):
    return f"{_BASE}/{name}.json"


def upper_rows() -> list:
    """Rows from the helper-backed endpoint.

    Provides:
        - rows

    Datasets:   hk-x
    Department: Foo
    Endpoint:   https://example.com/x.json
    Questions:
        - "rows?"

    Quirks:
        - none
    """
    import json
    import urllib.request

    with urllib.request.urlopen(_url("x")) as resp:
        return json.loads(resp.read())
'''


@pytest.fixture
def helper_dir(tmp_path, monkeypatch):
    d = tmp_path / "programs"
    (d / "demo").mkdir(parents=True)
    (d / "demo" / "rows.py").write_text(HELPER_SAMPLE, encoding="utf-8")
    (d / "__init__.py").write_text('"""pkg"""\n', encoding="utf-8")
    monkeypatch.setattr(programs_mod, "PROGRAMS_DIR", d)
    return d


def test_extract_inlines_module_helpers(helper_dir):
    rec = next(r for r in extract() if r["func_name"] == "upper_rows")
    source = rec["source"]
    assert "_BASE = " in source
    assert "def _url(name):" in source
    assert "def upper_rows" in source
    # helper definitions must precede the function that calls them
    assert source.index("def _url") < source.index("def upper_rows")
    ns: dict = {}
    exec(source, ns)
    assert callable(ns["upper_rows"])


def test_metadata_source_hash_tracks_body(helper_dir):
    rec = next(r for r in extract() if r["func_name"] == "upper_rows")
    before = build_metadata(rec, "m")["source_hash"]
    changed = dict(rec, source=rec["source"].replace("resp.read()", "b'[]'"))
    after = build_metadata(changed, "m")["source_hash"]
    assert before != after


def test_repo_programs_sources_are_self_contained():
    """Every embedded source must bind the module-level names it references."""
    import ast as _ast

    records = extract()
    assert records
    for rec in records:
        path = programs_mod.PROGRAMS_DIR / rec["path"]
        tree = _ast.parse(path.read_text(encoding="utf-8"))
        module_names = set(programs_mod._module_segments(tree))
        used = programs_mod._loaded_names(_ast.parse(rec["source"]))
        ns: dict = {}
        exec(rec["source"], ns)
        missing = sorted((module_names & used) - set(ns))
        assert not missing, f"{rec['id']} references missing module names: {missing}"


def test_build_vectors_reembeds_when_source_changes(prog_dir):
    chromadb = pytest.importorskip("chromadb")
    client = chromadb.EphemeralClient()

    def embed(texts):
        return [[1.0, 0.0] for _ in texts]

    first = programs_mod.build_vectors(embed_fn=embed, client=client,
                                       collection_name="t_prog_src", verbose=False)
    assert first["embedded"] == 1

    again = programs_mod.build_vectors(embed_fn=embed, client=client,
                                       collection_name="t_prog_src", verbose=False)
    assert again["embedded"] == 0

    path = prog_dir / "lcsd" / "facility.py"
    path.write_text(
        SAMPLE.replace("return json.loads(r.read())",
                       "return [json.loads(r.read())]"),
        encoding="utf-8")

    changed = programs_mod.build_vectors(embed_fn=embed, client=client,
                                         collection_name="t_prog_src", verbose=False)
    assert changed["embedded"] == 1
    stored = client.get_collection("t_prog_src").get(
        ids=["lcsd.facility:fitness_rooms"])["metadatas"][0]
    assert "[json.loads(r.read())]" in stored["source"]

