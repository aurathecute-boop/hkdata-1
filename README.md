# 港數通 · hkdata

**香港政府開放數據 × AI Agent 技能** — a self-extending query toolkit for
[DATA.GOV.HK](https://data.gov.hk) open data.

> **中文版** → [README.zh-HK.md](README.zh-HK.md)

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![datasets](https://img.shields.io/badge/datasets-3%2C822-blueviolet.svg)](https://data.gov.hk)
[![version](https://img.shields.io/badge/version-0.4.0-lightgrey.svg)](scripts/hkdata/__init__.py)

Ask it questions like *「長沙灣有冇政府健身室？」* or *"what's the air quality
right now?"* and it finds the right official dataset, queries its live API, and
answers **with an honest "no dataset exists" when that's the truth**.

```text
You    : how many PRH public housing estates are in Kwun Tong?
港數通  : 14 estates (as at 2026-06-22, HKT).
          Source: Housing Authority PSI API
          Dataset: hk-housing-eslocator-eslocator
          Endpoint: https://data.housingauthority.gov.hk/psi/rest/export/prh-estates
          Caveat: district names use "&" (Central & Western) — normalise before joining.
```

---

## In action

Real answers from the AI Agent (GrokBot) — every one cites the data.gov.hk dataset behind it.

| | | |
|---|---|---|
| <img src="docs/screenshots/parking-vacancy-nearby.webp" width="260" alt="Live car-park vacancy near a shopping mall"> | <img src="docs/screenshots/library-new-books.webp" width="260" alt="Library new additions matching a title search"> | <img src="docs/screenshots/sports-running-classes.webp" width="260" alt="Community sports running courses and enrolment windows"> |
| **Live car-park vacancy**<br>Five nearest car parks to a mall, vacancy updated in real time | **Library new additions**<br>Search LCSD's newest books, by relevance or by date added | **Sports courses**<br>Running classes from SmartPLAY, with enrolment windows |
| <img src="docs/screenshots/ferry-cheung-chau-eta.webp" width="260" alt="Ferry timetable joined with live vessel ETA"> | <img src="docs/screenshots/film-fund-roi.webp" width="260" alt="Film Development Fund return-on-subsidy ranking"> | <img src="docs/screenshots/kindergarten-enrolment-trend.webp" width="260" alt="Kindergarten and primary enrolment trend 2015 to 2025"> |
| **Ferry + live ETA**<br>Static timetable joined with live vessel positions | **Film-fund ROI**<br>Box office ÷ funding — two datasets joined | **Enrolment trend**<br>Kindergarten → primary series, 2015–2025 |

## What it can do

港數通 turns a natural-language question into a sourced, live answer:

- **Search the whole catalog** — all ~3,822 datasets on data.gov.hk, in English
  **and** 繁體中文, not a partial index.
- **Understand Chinese** — `康文署` resolves to `康樂及文化事務署`, so
  Cantonese / Traditional-Chinese queries just work.
- **Query the live API** — finds the right endpoint, tests it, and auto-detects
  JSON / XML / CSV to pull the current data.
- **Answer honestly** — every answer cites the dataset ID, endpoint, and the
  data's own HKT timestamp, and says "no dataset" when that's the truth.
- **Extend itself** — each verified recipe is saved as a runnable function in
  `programs/`, so the next similar question answers instantly by calling it.

Under the hood it crawls data.gov.hk once into a local, PII-free catalog and
searches it with hybrid retrieval (dense multilingual embeddings + keyword), and
keeps a **program library** of runnable, docstring-documented functions:

```text
catalog-sync --full --lang en,tc    crawl the whole catalog (resumable)
        │                            package_list seed → package_show per dataset
        ▼
data/catalog/*.jsonl                8 shards, 500 datasets each, PII-free
        │
catalog-embed                       embed with a local (or remote) model
        ▼
.cache/catalog/chroma/hkdata_datasets   "what datasets exist"
        ▲
programs/*.py                       runnable functions, grouped by department
        │                            docstring = retrieval + reading surface
reindex                             embed docstrings
        ▼
.cache/catalog/chroma/hkdata_programs   "how to answer this question"
```

## What makes it different: it learns by writing code

You are a **coding agent**, not a search wizard. When a question is new, you
explore (`catalog-search` → `info` → `test`), write a function, run it to answer,
then `reindex` — the next time that question comes up it's a one-step lookup.

```mermaid
flowchart TD
    Q(["question<br/>English or 繁體中文"]) --> PS["programs-search<br/>hybrid: embeddings + keyword"]
    PS --> D{"a program<br/>covers it?"}

    D -->|"Path A — yes"| RUN["run the returned source<br/>bash hk.sh python &lt;&lt;EOF"]
    RUN --> A1(["answer now<br/>dataset ID · endpoint · HKT timestamp"])

    D -->|"Path B — no"| CS["catalog-search<br/>all 3,822 datasets"]
    CS --> IT["info &lt;id&gt; → test &lt;url&gt;<br/>detect JSON / XML / CSV"]
    IT --> A2(["answer now<br/>same contract"])
    A2 -->|"after the answer"| W["write programs/&lt;org&gt;/&lt;file&gt;.py<br/>one function = one capability"]
    W --> RI["reindex"]

    RI -.->|"next similar question is Path A"| PS
    A1 --> DONE(["done"])
    RI --> DONE
```

Only Path B writes code — Path A answers from an existing function and stops. The dotted
edge back to `programs-search` is the learning loop: `reindex` makes the next similar
question a one-step lookup.

Concretely, for *"gym room in Cheung Sha Wan"*:

```text
1. programs-search "gym room Cheung Sha Wan"     → no hit
2. catalog-search "gym room"                     → hk-lcsd-facility-facility-fit
3. info + test the endpoint                       → live JSON, 87 rooms
4. write programs/lcsd/facility.py:fitness_rooms → run it, answer
5. reindex                                        → the function is indexed
6. programs-search "fitness room Sham Shui Po"   → answered at step 1 ✓
```

| | 港數通 |
|---|---|
| **Bilingual** | English + 繁體中文 metadata (`康文署` → `康樂及文化事務署`) |
| **Hybrid search** | ChromaDB dense embeddings fused with a keyword pass + abbreviation aliases |
| **Self-extending** | every new recipe becomes a runnable, indexed function |
| **Pluggable embeddings** | local Ollama by default; any OpenAI-compatible API (or your own backend) |
| **Honest by contract** | cites dataset ID, endpoint, and the data's own HKT timestamp |
| **Scoped** | Hong Kong government data only — everything else is redirected |

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-vectors.txt -r requirements-programs.txt
ollama pull embeddinggemma-2:740m

bash ./hk.sh catalog-embed                 # ~10 min (shards are committed, no crawl)
bash ./hk.sh reindex                       # index the program library
bash ./hk.sh programs-search "badminton courts"
bash ./hk.sh programs-search "康文署羽毛球場"
```

The catalog shards in `data/catalog/` are committed, so a fresh clone **only needs
to build the vector stores** — no crawl. Full setup is in [SETUP.md](SETUP.md).

## Usage

```bash
# Path A — a runnable program already covers it
bash ./hk.sh programs-search "gym room Cheung Sha Wan"
bash ./hk.sh programs-search "gym room Cheung Sha Wan" --source   # print source to run

# Path B — explore, then write a program and reindex
bash ./hk.sh catalog-search "badminton courts"
bash ./hk.sh info hk-lcsd-facility-facility-fit
bash ./hk.sh test "http://www.lcsd.gov.hk/datagovhk/facility/facility-fitrm.json"

# Maintenance
bash ./hk.sh programs-status
bash ./hk.sh catalog-status
bash ./hk.sh embed-status
```

### Commands

| Command | Purpose |
|---|---|
| `programs-search "<query>" [--source] [--json]` | Semantic search over runnable functions — Path A |
| `reindex` | Extract + embed functions from `programs/`, render the registry |
| `programs-status` | Program file/function count + vector-store state |
| `catalog-search "<query>"` | ChromaDB hybrid search over the full catalog — Path B |
| `catalog-sync [--full] [--refresh] [--lang en,tc]` | Seed / crawl / refresh the offline catalog |
| `catalog-embed` | Build the ChromaDB catalog vector store |
| `catalog-status` | Coverage and vector-store report |
| `embed-status` | Active embedding backend + store match (catalog, programs) |
| `info "<id>"` | Dataset metadata (`package_show`) |
| `test "<url>"` | Test an endpoint and detect JSON / XML / CSV |

All commands run through `bash ./hk.sh`, which picks the `.venv` interpreter
automatically when `chromadb` or the program dependencies are needed, and falls
back to plain `python3` otherwise. Pasted program source runs in the venv:
`bash ./hk.sh python - <<'EOF' … EOF`.

### Embedding backends

Local Ollama (`embeddinggemma-2:740m`) is the default. Switch to any
OpenAI-compatible API, or bring your own backend via the `Embedder` interface:

```bash
export HKDATA_EMBED_PROVIDER=openai
export HKDATA_EMBED_MODEL=text-embedding-3-small
export HKDATA_EMBED_URL=https://api.openai.com/v1/embeddings
export HKDATA_EMBED_API_KEY=sk-...
bash ./hk.sh catalog-embed && bash ./hk.sh reindex
```

See [SETUP.md](SETUP.md) *"Integrating a new backend"* for the interface.

## Layout

```
hk.sh                     single CLI entry point (picks venv or python3)
SKILL.md                  the coding-agent workflow (the agent entrypoint)
AGENTS.md                 notes for agents using the skill
programs/                 runnable, indexed function library (one fn = one capability)
scripts/hkdata/           CLI + engine (catalog.py, vectors.py, programs.py, …)
data/catalog/             sanitized catalog shards (committed)
tests/                    pytest suite
```

## Writing a program

Copy [`programs/_template.py`](programs/_template.py) into a new file under the
right `programs/<org>/` subpackage. A program is a single function whose docstring
leads with **what the data provides** and lists its dataset ID, endpoint(s), usage,
example questions, and quirks. Functions return JSON-serializable data and never
print. Then run `bash ./hk.sh reindex`.

## Scope

**Hong Kong government data from data.gov.hk only.** Non-HK data, non-government
sources, or general web queries are out of scope and redirected to the agent's
native web search — this keeps the store focused and the answers trustworthy.

## Data source & attribution

All dataset metadata comes from **[DATA.GOV.HK](https://data.gov.hk)** and remains
subject to its [terms and conditions](https://data.gov.hk/en/terms-and-conditions).
The committed shards in `data/catalog/` are a **sanitized projection** of
`package_show` responses: personal contact details (author/maintainer emails and
phones) are stripped, and only the fields needed for search are retained. The JSONL
store can be regenerated at any time with `catalog-sync`.

### Further reading

- [data.gov.hk Developer Guide](https://data.gov.hk/en/help/developer-guide)
- [CKAN API Documentation](https://docs.ckan.org/en/latest/api/)
- [HK Census and Statistics Department](https://www.censtatd.gov.hk/)
- [HK Observatory](https://www.hko.gov.hk/)

## Tests

```bash
.venv/bin/pip install -r requirements-vectors.txt -r requirements-programs.txt -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -q
```

## License

[MIT](LICENSE) for the code and documentation. The underlying government data is
covered by the DATA.GOV.HK terms of use, not the MIT licence.

---

_港數通 · hkdata — 香港政府開放數據，問得準，答得真。_
