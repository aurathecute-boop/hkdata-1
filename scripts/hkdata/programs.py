"""Program index: runnable, docstring-documented functions over HK open data.

The ``programs/`` package is the canonical, indexed library of composable
functions — one function per capability, grouped by department/org subpackage.
Each function's docstring is the retrieval surface and the reading surface (see
``programs/_template.py`` for the contract); the body is runnable code that
returns JSON-serializable data (never ``print``).

This module mirrors the catalog/experience split:

  * ``extract``    — AST-walk ``programs/`` into one record per function
  * ``build_vectors`` — embed docstrings into Chroma collection ``hkdata_programs``
  * ``search``      — hybrid (dense + keyword) retrieval that returns **source**
  * ``render_registry`` — generate ``programs/index.md`` (what exists)

The answer path is "retrieve source → inline → run in the terminal"; ``programs/``
is never ``import``ed at answer time, so there is no sys.path plumbing.
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import catalog, vectors

PROGRAMS_DIR = catalog.ROOT / "programs"
INDEX_MD_PATH = PROGRAMS_DIR / "index.md"
COLLECTION_NAME = "hkdata_programs"

# Docstring sections. Keys are normalised to lowercase; these are the canonical
# field names the rest of the module reads.
_SINGLE_VALUE_KEYS = {
    "dataset": "datasets",
    "datasets": "datasets",
    "department": "department",
    "org": "department",
    "organization": "department",
    "organisation": "department",
    "endpoint": "endpoints",
    "endpoints": "endpoints",
    "format": "formats",
    "formats": "formats",
}
_TEXT_KEYS = {
    "provides": "provides",
    "coverage": "coverage",
    "questions": "questions",
    "usage": "usage",
    "quirks": "quirks",
    "notes": "notes",
    "examples": "examples",
    "join": "join",
    "join keys": "join",
}
_ALL_KEYS = {**_SINGLE_VALUE_KEYS, **_TEXT_KEYS}

_FIELD_RE = re.compile(r"^([A-Za-z][A-Za-z ]*):\s*(.*)$")


def _module_id(rel_path: Path) -> str:
    """Return the dotted module id for a file relative to ``PROGRAMS_DIR``."""
    parts = list(rel_path.with_suffix("").parts)
    return ".".join(parts) if parts else rel_path.stem


def _parse_docstring(doc: Optional[str]) -> Dict:
    """Split a docstring into a summary and canonical section fields."""
    doc = (doc or "").strip()
    fields: Dict[str, List[str]] = {}
    summary_lines: List[str] = []
    current: Optional[str] = None

    for line in doc.splitlines():
        m = _FIELD_RE.match(line.strip())
        key = m.group(1).strip().lower() if m else None
        if key and key in _ALL_KEYS:
            current = _ALL_KEYS[key]
            fields.setdefault(current, [])
            inline = m.group(2).strip()
            if inline:
                fields[current].append(inline)
            continue
        if current is None:
            summary_lines.append(line.rstrip())
        else:
            fields[current].append(line.rstrip())

    summary = "\n".join(l for l in summary_lines if l.strip()).strip()

    def _text(name: str) -> str:
        return "\n".join(l.strip() for l in fields.get(name, []) if l.strip()).strip()

    def _list(name: str) -> List[str]:
        out: List[str] = []
        for raw in fields.get(name, []):
            for part in re.split(r"[,;]\s*", raw):
                part = part.strip().strip("`")
                if part and part not in out:
                    out.append(part)
        return out

    return {
        "summary": summary,
        "provides": _text("provides"),
        "coverage": _text("coverage"),
        "questions": _text("questions"),
        "usage": _text("usage"),
        "quirks": _text("quirks"),
        "notes": _text("notes"),
        "examples": _text("examples"),
        "join": _text("join"),
        "datasets": _list("datasets"),
        "department": _text("department"),
        "endpoints": _list("endpoints"),
        "formats": _list("formats"),
    }


def _func_signature(node: ast.FunctionDef, lines: List[str]) -> str:
    """Reconstruct ``name(args) -> ret`` from the def lines."""
    if not node.body:
        return f"{node.name}()"
    sig_lines = lines[node.lineno - 1:node.body[0].lineno - 1]
    sig = " ".join(s.strip() for s in sig_lines)
    sig = re.sub(r"^def\s+", "", sig)
    return sig.rstrip(":")


def _func_source(node: ast.FunctionDef, lines: List[str]) -> str:
    start = node.lineno
    if node.decorator_list:
        start = node.decorator_list[0].lineno
    return "\n".join(lines[start - 1:node.end_lineno]).rstrip("\n")


def extract() -> List[Dict]:
    """AST-walk ``programs/`` into one record per top-level function."""
    if not PROGRAMS_DIR.exists():
        return []

    records: List[Dict] = []
    for path in sorted(PROGRAMS_DIR.rglob("*.py")):
        if path.name.startswith("_"):
            continue  # __init__.py, _template.py, private modules
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        lines = source.splitlines()
        rel = path.relative_to(PROGRAMS_DIR)
        module = _module_id(rel)
        for node in tree.body:
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name.startswith("_"):
                continue
            doc = _parse_docstring(ast.get_docstring(node, clean=True))
            records.append({
                "id": f"{module}:{node.name}",
                "module": module,
                "func_name": node.name,
                "signature": _func_signature(node, lines),
                "source": _func_source(node, lines),
                "path": str(rel),
                "lineno": node.lineno,
                **doc,
            })
    records.sort(key=lambda r: r["id"])
    return records


def build_document(rec: Dict) -> str:
    """The text that gets embedded for one function (never the full source)."""
    parts: List[str] = []
    parts.append(rec.get("signature") or rec["func_name"])
    if rec.get("summary"):
        parts.append(rec["summary"])
    for key, label in (
        ("provides", "Provides"),
        ("coverage", "Coverage"),
        ("questions", "Questions"),
        ("usage", "Usage"),
        ("quirks", "Quirks"),
    ):
        if rec.get(key):
            parts.append(f"{label}: {rec[key]}")
    if rec.get("datasets"):
        parts.append("Datasets: " + ", ".join(rec["datasets"]))
    if rec.get("department"):
        parts.append("Department: " + rec["department"])
    if rec.get("endpoints"):
        parts.append("Endpoints: " + ", ".join(rec["endpoints"]))
    return "\n".join(parts)


def build_metadata(rec: Dict, model: str) -> Dict:
    return {
        "id": rec["id"],
        "module": rec["module"],
        "func_name": rec["func_name"],
        "signature": rec["signature"],
        "source": rec["source"],
        "path": rec["path"],
        "lineno": rec["lineno"],
        "datasets": ",".join(rec.get("datasets") or []),
        "department": rec.get("department") or "",
        "endpoints": ",".join(rec.get("endpoints") or []),
        "text_hash": vectors.text_hash(build_document(rec)),
        "model": model,
    }


# ---------------------------------------------------------------------------
# ChromaDB index
# ---------------------------------------------------------------------------


def build_vectors(model: str = vectors.DEFAULT_MODEL,
                  url: str = vectors.DEFAULT_OLLAMA_URL,
                  batch: int = vectors.EMBED_BATCH,
                  collection_name: str = COLLECTION_NAME,
                  embed_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
                  client=None, verbose: bool = True) -> dict:
    """Embed every extracted function, skipping unchanged documents."""
    records = extract()
    if not records:
        raise RuntimeError("No programs found. Add functions under programs/ "
                           "then re-run reindex.")

    if embed_fn is None:
        def embed_fn(texts: List[str]) -> List[List[float]]:
            return vectors.embed_texts(texts, model=model, url=url)
    if client is None:
        client = vectors._client(catalog.default_paths())
    collection = vectors._collection(client, collection_name)
    if vectors.reset_collection_if_stale(collection, client, collection_name,
                                         model):
        collection = vectors._collection(client, collection_name)

    existing = collection.get(include=["metadatas"])
    known = {i: (m or {}) for i, m in zip(existing["ids"], existing["metadatas"])}

    pending: List[Dict] = []
    docs: Dict[str, str] = {}
    metas: Dict[str, Dict] = {}
    for rec in records:
        doc = build_document(rec)
        meta = build_metadata(rec, model)
        docs[rec["id"]] = doc
        metas[rec["id"]] = meta
        old = known.get(rec["id"])
        if (old is None or old.get("text_hash") != meta["text_hash"]
                or old.get("model") != model):
            pending.append(rec)

    embedded = 0
    for start in range(0, len(pending), batch):
        chunk = pending[start:start + batch]
        collection.upsert(
            ids=[r["id"] for r in chunk],
            embeddings=embed_fn([docs[r["id"]] for r in chunk]),
            documents=[docs[r["id"]] for r in chunk],
            metadatas=[metas[r["id"]] for r in chunk],
        )
        embedded += len(chunk)
        if verbose:
            print(f"  embedded {embedded}/{len(pending)}", file=sys.stderr)

    stale = sorted(set(known) - set(docs))
    if stale:
        collection.delete(ids=stale)

    if verbose:
        print(f"Programs: {collection.count()} total, {embedded} (re)embedded, "
              f"{len(stale)} removed", file=sys.stderr)
    return {"total": collection.count(), "embedded": embedded,
            "removed": len(stale)}


def _rrf_rank(items: List[str], k: int = 60) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for rank, name in enumerate(items):
        if name:
            scores.setdefault(name, 1.0 / (k + rank + 1))
    return scores


def search(query: str, top_n: int = 5,
           model: str = vectors.DEFAULT_MODEL,
           url: str = vectors.DEFAULT_OLLAMA_URL,
           collection_name: str = COLLECTION_NAME,
           embed_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
           client=None, verbose: bool = True,
           query_instruction: str = vectors.QUERY_INSTRUCTION) -> List[dict]:
    """Hybrid (dense + keyword) retrieval; results carry the function source."""
    if embed_fn is None:
        def embed_fn(texts: List[str]) -> List[List[float]]:
            return vectors.embed_texts(texts, model=model, url=url)
    if client is None:
        client = vectors._client(catalog.default_paths())
    collection = vectors._collection(client, collection_name)
    if collection.count() == 0:
        if verbose:
            print("Program store is empty. Run: hkdata.py reindex", file=sys.stderr)
        return []

    fetch = max(top_n * 3, 20)
    query_vector = embed_fn([query_instruction + query])[0]

    def _rows(result):
        out = []
        for meta, dist in zip(result["metadatas"][0], result["distances"][0]):
            meta = meta or {}
            out.append({
                "id": meta.get("id", ""),
                "module": meta.get("module", ""),
                "func_name": meta.get("func_name", ""),
                "signature": meta.get("signature", ""),
                "source": meta.get("source", ""),
                "path": meta.get("path", ""),
                "datasets": [d for d in (meta.get("datasets") or "").split(",") if d],
                "department": meta.get("department", ""),
                "endpoints": [e for e in (meta.get("endpoints") or "").split(",") if e],
                "distance": dist,
            })
        return out

    dense_res = collection.query(query_embeddings=[query_vector], n_results=fetch,
                                 include=["metadatas", "distances"])
    dense = _rows(dense_res)
    by_name = {item["id"]: item for item in dense}

    tokens = [t for t in re.findall(r"[A-Za-z0-9\u3400-\u4dbf\u4e00-\u9fff]+", query)
              if len(t) >= 2]
    for value in vectors.expand_query(query):
        if value:
            tokens.append(value)
    keyword_names: List[str] = []
    for token in list(dict.fromkeys(tokens))[:4]:
        try:
            kw = collection.query(
                query_embeddings=[query_vector], n_results=fetch,
                where_document={"$regex": f"(?i){re.escape(token)}"},
                include=["metadatas", "distances"])
        except Exception:
            continue
        for item in _rows(kw):
            by_name.setdefault(item["id"], item)
            keyword_names.append(item["id"])

    scores = _rrf_rank([item["id"] for item in dense])
    for name, score in _rrf_rank(keyword_names).items():
        scores[name] = scores.get(name, 0.0) + score

    ranked = sorted(scores, key=lambda n: (-scores[n], n))
    results = []
    for name in ranked[:top_n]:
        item = dict(by_name[name])
        item["score"] = scores[name]
        results.append(item)
    return results


def status(collection_name: str = COLLECTION_NAME) -> dict:
    info: dict = {"program_files": 0, "functions": 0, "vectors": None}
    records = extract()
    info["program_files"] = len({r["path"] for r in records})
    info["functions"] = len(records)
    info["vectors"] = vectors.vector_status(catalog.default_paths(),
                                            collection_name=collection_name)
    return info


def render_registry(records: Optional[List[Dict]] = None,
                    path: Path = INDEX_MD_PATH) -> None:
    """Render ``programs/index.md`` (a generated view — never edit by hand)."""
    if records is None:
        records = extract()
    by_dept: Dict[str, List[Dict]] = {}
    for rec in records:
        dept = rec.get("department") or "Uncategorised"
        by_dept.setdefault(dept, []).append(rec)

    lines = [
        "# Program Registry",
        "",
        "_Generated by `reindex` from `programs/*.py` — do not edit by hand._",
        "",
        "Index of runnable, verified HK open-data functions. Search them with "
        "`programs-search`; run them by pasting the returned source into a "
        "terminal.",
        "",
    ]
    for dept in sorted(by_dept):
        lines.append(f"## {dept}")
        for rec in sorted(by_dept[dept], key=lambda r: r["id"]):
            summary = (rec.get("summary") or "").replace("\n", " ").strip()
            lines.append(f"- `{rec['id']}` — {summary}")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
