# AGENTS.md

This is an AI-agent **skill** directory, not an application. There is no build, lint,
or typecheck (there is a pytest suite). The entrypoint is `SKILL.md`, which frames the
agent as a **coding agent** with a library of runnable functions. Everything below is
stuff `SKILL.md` implies but an agent commonly gets wrong.

## Running the scripts

First-time setup (venv, Ollama model, vector stores) is in [`SETUP.md`](SETUP.md).

Always invoke from the skill root via `bash ./hk.sh <subcommand>` — the wrapper picks
the venv interpreter (needed by search/embed commands, which require `chromadb`) and
falls back to `python3` otherwise. Never run `./hk.sh` directly; from another cwd, use
the absolute path (`bash ~/.agents/skills/hkdata/hk.sh …` for the symlink install) —
the wrapper is cwd-safe, but the doc text that names `./` paths assumes the skill root.
All paths in `SKILL.md` and the reference docs are `./`-relative.

```bash
# Path A — a runnable program already covers the question
bash ./hk.sh programs-search "<query>" [--source] [--json]
bash ./hk.sh reindex                       # extract + embed programs, render the registry
bash ./hk.sh programs-status               # library + vector-store report
# Path B — explore, then write a program
bash ./hk.sh catalog-search "<keyword>"    # full ~3,822-dataset catalog
bash ./hk.sh info "<dataset-id>"
bash ./hk.sh test "<endpoint-url>"
```

Under the hood this is `"$PWD/.venv/bin/python" ./scripts/hkdata.py <subcommand>`
(or `python3 ./scripts/hkdata.py <subcommand>` when no venv exists).

## The one gotcha that wastes the most time

There are **two retrieval layers, and they answer different questions**:

- `programs-search` — the **program library** (`programs/*.py`), the functions
  you have actually written and verified. Small, curated, runnable.
- `catalog-search` — the **full catalog** (`data/catalog/*.jsonl`, ~3,822
  datasets). This is the discovery fallback for anything with no program yet.

A query that misses in `programs-search` must fall through to `catalog-search`,
then `info`/`test`, then you **write a program and `reindex`**. That is the whole
learning loop.

CKAN's `package_search` is **Solr-backed and covers only ~631 of the ~3,822
datasets** that the DB-backed `package_list` returns. It has been removed; the
catalog is crawled once via `package_list` + `package_show` into JSONL shards
(`data/catalog/`, sanitized PII-free) and searched through ChromaDB.

If a store is empty, it is probably not built:
1. `bash ./hk.sh catalog-sync --full --lang en,tc` (once, ~2 h, resumable) — only if shards are missing
2. `bash ./hk.sh catalog-embed && bash ./hk.sh reindex`
3. Then search with `bash ./hk.sh programs-search "<topic>"` or `catalog-search "<topic>"`

## Writing a program (the new "memory write")

When Path B lands on a working recipe, persist it as a function — this is the
replacement for the old experience card, and it is the **hard gate**: until a
program is written and indexed, the discovery is not "remembered".

1. Copy `programs/_template.py` into the right `programs/<org>/<file>.py`.
2. One **function = one capability**; group related functions in one file.
3. Docstring leads with **what the data provides** (`Provides`), then `Coverage`,
   `Datasets`, `Department`, `Endpoint`, `Usage`, `Questions`, `Quirks`.
   `Questions` is the retrieval aid — write several rewordings.
4. The function returns JSON-serializable data and **never prints**; imports go
   *inside* the function so the returned source runs standalone in a heredoc.
5. `bash ./hk.sh reindex` — embeds the docstrings and renders `programs/index.md`
   (a generated view — never edit it by hand).

A program that has not run against the live endpoint is not done: `test` the URL
first, then write the function from what you observed.

## Org → subpackage guidance

Program files are grouped by **department/org**, not by the data.gov.hk category.
Use short slugs (`lcsd/`, `td/`, `hko/`, `epd/`, `gpa/`, `housing/`, `censtatd/`, …).
A function that joins two departments lives under its **primary** org and declares
**all** dataset IDs it touches in `Datasets:`. The complex transport multi-endpoint
joins (KMB route-finder, ferry+vessel, film-fund ROI) are deliberately deferred.

## Scope boundary

Only Hong Kong government data from data.gov.hk. Non-HK data, non-government
sources, or general web queries are out of scope — redirect those to the agent's
native web search. Do not try to satisfy them with this skill.

## Subagent delegation

For complex discovery you may spawn a **single** subagent with shell and file
access to run Path B end-to-end (catalog-search → info → test → write program →
reindex). Do not split into multiple subagents. Use the highest-reasoning model
available in your agent tool.

## End-to-end test (clean clone)

Verifies the **public** artifact actually runs — an agent following `SETUP.md`
then `SKILL.md` from a fresh clone. Run it before a release or after large
changes. The generated `programs/index.md` registry is gitignored; a clone
carrying only the engine + `programs/*.py` is exactly what the test checks.

1. `e2e-test/` is gitignored. Clean it and clone the **public remote** (not a local copy):
   ```bash
   rm -rf e2e-test/hkdata && mkdir -p e2e-test
   git clone https://github.com/gnokit/hkdata.git e2e-test/hkdata
   ```
2. Spawn **one** high-reasoning subagent (shell + file access). It must:
   - work only inside `e2e-test/hkdata`; never read/write the working repo or `~/.agents/skills/hkdata`;
   - **not** use `SKILL.md`'s root-resolution snippet — the `~/.agents/skills/hkdata` symlink points at the private repo and would silently contaminate the run. Set `export HKDATA_SKILL_DIR=$PWD` inside the clone and run `bash ./hk.sh …`;
   - follow `SETUP.md` steps 1–5, then `SETUP.md` §6 — the 3 hard questions through the **full** two-path loop (Path A → Path B, one written program + `reindex` each);
   - write raw commands + output to `e2e-test/REPORT.md` with a verdict and a per-finding PASS/FAIL table.
3. Expect ~64 tracked files and a green `bash ./hk.sh`-driven run; the suite needs `requirements-dev.txt`. No BLOCKER = pass.

## Keeping SKILL.md minimal

`SKILL.md` is the **runtime entrypoint** — what a skill consumer reads to answer a
query. Keep it to the two-path contract only. It must not grow when programs are
added, and it must not carry development, setup, or maintenance material:

| Content | Belongs in |
|---|---|
| Two-path workflow, program docstring contract, answer contract | `SKILL.md` |
| First-run install, venv, Ollama, building/refreshing the stores | `SETUP.md` |
| CLI reference, architecture, attribution | `README.md` |
| Repo upkeep, conventions, gotchas for maintainers | `AGENTS.md` |
| Response templates, deep guidance, failure patterns | `references/workflow-guides.md` |

The program library lives in `programs/`; its generated registry is
`programs/index.md` (built by `reindex`). The old `references/<dataset>.md` recipes
are being migrated into `programs/` and will be removed.

## Weekly self-evolution review (every 7 days)

1. Read the program library (`programs/*.py`) and `programs/index.md`
2. Identify patterns: stale endpoints, quirks worth folding into docstrings,
   functions that overlap and should be merged
3. Update `references/workflow-guides.md` and `AGENTS.md` if guidance changes
4. Re-test any program whose endpoint looks stale, then `bash ./hk.sh reindex`

**Trigger:** spawn a single subagent with the task "hkdata weekly self-evolution review".
