---
name: hkdata
description: >
  Use when the user asks about Hong Kong government open data, statistics, or
  datasets — e.g. transport, weather, population, employment, finance, health,
  education, housing, crime, tourism, facilities, etc. — in English or Chinese.
  Queries data.gov.hk and returns sourced, live answers, or an honest "no dataset".
compatibility: Requires python3 + chromadb for search/embed (see SETUP.md); needs a reachable embedding backend — Ollama by default, or any backend via the Embedder interface (see SETUP.md "Integrating a new backend").
license: MIT
---

# 港數通 · hkdata — Hong Kong Open Data Library

**Scope: Hong Kong data.gov.hk datasets only.** General web search, non-HK data,
or non-government sources are handled by the agent's native web search tools, not
this skill.

## You are a coding agent with a library of reusable programs

This skill gives you a growing library of **runnable, docstring-documented
functions** under `programs/` — each one a **reusable capability over one
data.gov.hk API/dataset**, grouped by department/org. Each function returns
JSON-serializable data (it never prints); its docstring says what data it
provides, its dataset ID, endpoints, and quirks.

**A program answers a *class* of questions, not one specific question.**
`address_lookup(q)` is the reusable capability; "where is the Housing Authority
headquarters?" is a query you answer *with* it. Write a program only when you
find a dataset/API that a whole family of future questions will need — never for
a single concrete fact.

### Think in programs before you search

When a question arrives, first decompose it: **what program / function / API /
dataset would produce this answer?** Then retrieve those primitives and compose
them, rather than reaching for web search or a one-off:

```text
"what's the Housing Authority HQ address, and the bus from Un Chau Estate?"
    → address_lookup("Housing Authority Headquarters")   # geocode → 33 Fat Kwong St
    → kmb_routes()                                        # find Cheung Sha Wan → Ho Man Tin (route 18)
```

A specific fact (an address, a coordinate, a route) is usually *retrievable
through an existing primitive* — compose your programs first. Only fall through
to exploration (Path B) when no program or catalog dataset can produce it.

Answer a question in **two paths**, not a fixed set of steps:

### Path A — a program already covers it (fast, repeatable)

```bash
bash "$SKILL_DIR/hk.sh" programs-search "<user query>"
```

Retrieve the top-k functions (bilingual semantic + keyword). If one covers the
question, **paste its source into a terminal and run it** — write-and-run on the
fly, no file I/O:

```bash
python3 - <<'EOF'
<paste the returned source, then call it>
EOF
```

Compose when needed: `function_a(...) + new_function_b(...)`, all in that
throwaway heredoc.

### Path B — nothing covers it (explore, then write a program)

```bash
bash "$SKILL_DIR/hk.sh" catalog-search "<query>"    # discovery over all ~3,822 datasets
bash "$SKILL_DIR/hk.sh" info "<dataset-id>"          # metadata + endpoint URLs
bash "$SKILL_DIR/hk.sh" test "<endpoint-url>"        # fetch + detect JSON/XML/CSV
```

Once you have a working recipe, **write it as a reusable function** (a whole class
of questions, not this one instance) under `programs/<org>/<file>.py` (copy
`programs/_template.py` for the docstring contract), combine it with any existing
function to answer, then index it:

```bash
bash "$SKILL_DIR/hk.sh" reindex
```

That makes the *next* similar question a Path-A hit — this is the learning loop.

## Program docstring contract

Every function's docstring is both the retrieval surface and the reading surface.
Lead with **what the data provides**, then coverage, then the mechanics. The full
contract with a copyable example is in [`programs/_template.py`](programs/_template.py).
Required sections: `Provides`, `Coverage`, `Datasets`, `Department`, `Endpoint`,
`Usage`, `Questions`, `Quirks`. `Questions` lists example natural-language queries
and is the main retrieval aid — a reworded query should still hit the right
function.

## Command summary

| Command | Purpose |
|---------|---------|
| `programs-search "<query>" [--source] [--json]` | Semantic search over runnable functions; `--source` prints full source (Path A) |
| `reindex` | Extract + embed functions from `programs/`, render the registry |
| `programs-status` | Program file/function count + vector-store state |
| `catalog-search "<query>"` | ChromaDB search over the full catalog (Path B discovery) |
| `info "<id>"` | CKAN `package_show` metadata (Path B) |
| `test "<url>"` | Test endpoint and detect format (Path B) |
| `embed-status` | Active embedding backend + store match (catalog, programs) |

Full CLI list (catalog build/refresh) in [`README.md`](README.md).

## Auto-fallback and no-dataset contract

When `programs-search` and `catalog-search` both return nothing useful, web search
`site:data.gov.hk <topic>`. If Path B reveals **no dataset answers the query**,
your answer MUST:

1. State clearly: "No suitable dataset found on data.gov.hk"
2. Include an exploration log listing each dataset examined and why it didn't fit
3. If a proxy exists, use it with an explicit caveat

## Answer contract (when a program answers)

Every successful answer MUST include, alongside the direct answer:

1. **Dataset ID** (and the source department) — so the claim is re-checkable.
2. **Endpoint** actually queried (URL).
3. **Data timestamp** of the figures themselves, in **HKT**, distinct from
   "retrieved at" — e.g. "figures are as at 2026-03-13 (HKT)".

The program's docstring carries the dataset ID and endpoint; the data's own
timestamp comes from the returned records. Presentation: multiple rows → a table;
a trend → a chart (with the source dataset and its temporality labelled). A
procedural/form question ("how do I apply …") is rarely a dataset — data.gov.hk
holds statistics/fee tables, not application steps; redirect to the department's
site and say so rather than reporting a "dataset miss".

## Deeper guidance

- [`references/workflow-guides.md`](references/workflow-guides.md) — response templates, cross-dataset joins, proxy indicators, temporality, error handling, known broken endpoints.
- [`programs/_template.py`](programs/_template.py) — the program docstring contract.
- [`SETUP.md`](SETUP.md) — install, build, and refresh the catalog and vector stores.
