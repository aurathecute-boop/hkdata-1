"""Command-line interface for hkdata."""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import List

from . import __version__
from . import catalog
from . import programs
from . import vectors
from .common import USER_AGENT
from .inspect import info_multiple
from .parse import parse_data


def _eprint(message: str) -> None:
    print(message, file=sys.stderr)


def _require_chromadb() -> bool:
    if vectors.have_chromadb():
        return True
    _eprint("ChromaDB is not installed. Create the venv first (SETUP.md step 2):")
    _eprint("  .venv/bin/pip install -r requirements-vectors.txt")
    _eprint("then re-run your command.")
    return False


def _resolve_embedder(args: argparse.Namespace):
    """Resolve the embedding backend from CLI flags + environment variables."""
    provider = getattr(args, "provider", None)
    model = getattr(args, "model", None)
    url = getattr(args, "url", None)
    api_key = getattr(args, "api_key", None)
    return vectors.resolve_embedder(provider, model, url, api_key)


def _warn_store_mismatch(paths, collection_name: str, embedder) -> None:
    status = vectors.embed_status(paths, collection_name, embedder=embedder)
    if status.get("available") and not status.get("match"):
        _eprint(
            f"Warning: the vector store was built with "
            f"'{status.get('store_fingerprint')}' but the active embedder is "
            f"'{embedder.fingerprint}'. Run the matching *-embed command to rebuild."
        )


def cmd_info(args: argparse.Namespace) -> int:
    ids = list(args.dataset_ids)
    if not ids:
        _eprint("Error: at least one dataset ID is required.")
        return 1

    # Always emit a JSON array, so consumers never special-case 1-vs-N.
    results = info_multiple(ids)
    output = []
    errors = 0
    for dsid, result in zip(ids, results):
        if result.get("error"):
            _eprint(f"Error for '{dsid}': {result['error']}")
            errors += 1
        output.append(result["data"])
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if errors == len(ids) else 0


def cmd_test(args: argparse.Namespace) -> int:
    urls = list(args.urls)
    if not urls:
        _eprint("Error: at least one URL is required.")
        return 1

    exit_code = 0
    for url in urls:
        _eprint(f"Testing endpoint: {url}")
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
        except urllib.error.URLError as exc:
            _eprint(f"Error fetching {url}: {exc.reason}")
            exit_code = 1
            continue

        summary = parse_data(data, content_type=content_type, url=url)
        summary["url"] = url
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    return exit_code


# ---------------------------------------------------------------------------
# Programs (runnable, indexed functions) commands
# ---------------------------------------------------------------------------


def cmd_programs_search(args: argparse.Namespace) -> int:
    if not _require_chromadb():
        return 1
    query = " ".join(args.keywords)
    paths = catalog.default_paths()
    embedder = _resolve_embedder(args)
    _warn_store_mismatch(paths, programs.COLLECTION_NAME, embedder)
    try:
        hits = programs.search(
            query, top_n=args.top_n, embed_fn=embedder.embed,
            query_instruction=embedder.query_instruction)
    except RuntimeError as exc:
        _eprint(f"Error: {exc}")
        return 1
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=2))
        return 0
    if not hits:
        print(f"No program matches for: {query}")
        return 0
    for n, item in enumerate(hits, start=1):
        datasets = ", ".join(item.get("datasets") or []) or "-"
        dept = item.get("department") or "-"
        print(f"{n}. {item['score']:.4f} | {item['id']} | {item['signature']}")
        print(f"   {datasets} | {dept}")
        if args.source:
            print("---- source ----")
            print(item["source"])
            print("----------------")
    return 0


def cmd_programs_status(args: argparse.Namespace) -> int:
    info = programs.status()
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0
    print(f"Program files:  {info['program_files']}")
    print(f"Functions:      {info['functions']}")
    vec = info.get("vectors") or {}
    if vec.get("available"):
        print(f"Vector store:   {vec.get('count', 0)} functions")
    else:
        print("Vector store:   unavailable (install chromadb in the venv)")
    return 0


def cmd_reindex(args: argparse.Namespace) -> int:
    records = programs.extract()
    programs.render_registry(records)
    if not vectors.have_chromadb():
        _eprint(f"Rendered programs/index.md ({len(records)} functions). "
                f"ChromaDB not installed — the program search store was NOT "
                f"built. Install it (SETUP.md) and re-run reindex.")
        return 1
    embedder = _resolve_embedder(args)
    try:
        result = programs.build_vectors(
            model=embedder.fingerprint, embed_fn=embedder.embed_documents,
            batch=args.batch)
    except RuntimeError as exc:
        _eprint(f"Error: {exc}")
        return 1
    _eprint(f"Program store ready: {result['total']} functions "
            f"({embedder.fingerprint}); programs/index.md rendered.")
    return 0


# ---------------------------------------------------------------------------
# Catalog (offline discovery) commands
# ---------------------------------------------------------------------------


def cmd_catalog_sync(args: argparse.Namespace) -> int:
    paths = catalog.default_paths()
    try:
        langs = catalog.parse_langs(args.lang)
    except ValueError as exc:
        _eprint(f"Error: {exc}")
        return 1
    if args.refresh:
        result = catalog.sync_refresh(paths, rate=args.rate, langs=langs)
        if result["new"]:
            _eprint(f"New datasets added to seed: {', '.join(result['new'])}")
        return 0
    if not args.full:
        catalog.sync_seed(paths)
        return 0

    catalog.sync_seed(paths)
    result = catalog.sync_full(paths, rate=args.rate, limit=args.limit, langs=langs)
    if result["failed"]:
        _eprint(f"Failed ids ({len(result['failed'])}): "
                f"{', '.join(result['failed'][:10])}")
    return 0


def cmd_catalog_embed(args: argparse.Namespace) -> int:
    if not _require_chromadb():
        return 1
    paths = catalog.default_paths()
    embedder = _resolve_embedder(args)
    try:
        result = vectors.build_vectors(
            paths, model=embedder.fingerprint, embed_fn=embedder.embed_documents,
            batch=args.batch)
    except RuntimeError as exc:
        _eprint(f"Error: {exc}")
        return 1
    _eprint(f"Vector store ready: {result['total']} datasets "
            f"({embedder.fingerprint}).")
    return 0


def cmd_catalog_search(args: argparse.Namespace) -> int:
    if not _require_chromadb():
        return 1
    paths = catalog.default_paths()
    query = " ".join(args.keywords)
    embedder = _resolve_embedder(args)
    _warn_store_mismatch(paths, vectors.COLLECTION_NAME, embedder)
    try:
        results = vectors.hybrid_search(
            query, paths, top_n=args.top_n, embed_fn=embedder.embed,
            query_instruction=embedder.query_instruction)
    except RuntimeError as exc:
        _eprint(f"Error: {exc}")
        return 1
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    if not results:
        print(f"No catalog matches for: {query}")
        return 0
    for item in results:
        org = item.get("org") or "-"
        print(f"{item['score']:.4f} | {item['name']} | {item['title']} | {org}")
    return 0


def cmd_catalog_status(args: argparse.Namespace) -> int:
    paths = catalog.default_paths()
    data = catalog.status(paths)
    vec = vectors.vector_status(paths)
    data["vectors"] = vec
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print(f"Seed ids:      {data['seed_count']}")
    print(f"Fetched:       {data['fetched_count']}")
    print(f"Missing:       {data['missing_count']}")
    print(f"Locales:       {', '.join(data['langs']) or '-'}")
    print(f"Shards:        {data['shards']} ({data['shard_bytes'] / 1e6:.1f} MB)")
    if vec.get("available"):
        count = vec.get("count", 0)
        if count:
            print(f"Vector store:  {count} datasets")
        else:
            print("Vector store:  empty (run: catalog-embed)")
        print(f"Programs:      {len(programs.extract())} functions")
    else:
        print("Vector store:  unavailable (install chromadb in the venv)")
    print(f"Last full sync: {data['last_full_sync'] or '-'}")
    print(f"Last activity:  {data['fetched_at'] or '-'}")
    return 0


def cmd_embed_status(args: argparse.Namespace) -> int:
    paths = catalog.default_paths()
    embedder = _resolve_embedder(args)
    catalog_status = vectors.embed_status(paths, vectors.COLLECTION_NAME,
                                          embedder=embedder)
    prog_status = vectors.embed_status(paths, programs.COLLECTION_NAME,
                                       embedder=embedder)
    if args.json:
        print(json.dumps({"embedder": {"provider": embedder.name,
                                       "model": embedder.model,
                                       "fingerprint": embedder.fingerprint},
                          "catalog": catalog_status,
                          "programs": prog_status},
                         ensure_ascii=False, indent=2))
        return 0
    print(f"Provider:    {embedder.name}")
    print(f"Model:       {embedder.model}")
    print(f"Fingerprint: {embedder.fingerprint}")
    print(f"Registered:  {', '.join(vectors.registered_providers())}")
    rebuild = False
    for label, status in (("catalog", catalog_status),
                          ("programs", prog_status)):
        if not status.get("available"):
            print(f"{label}: unavailable")
            continue
        if status.get("empty"):
            print(f"{label}: empty (0 vectors) — run the matching *-embed command")
            continue
        match = "match" if status.get("match") else "MISMATCH"
        if not status.get("match"):
            rebuild = True
        print(f"{label}: {status.get('count', 0)} vectors | store "
              f"'{status.get('store_fingerprint')}' | {match}")
    if rebuild:
        print("Rebuild the mismatched store with the matching *-embed command.")
    return 0


def _add_embed_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--provider", default=None,
        help="Embedding provider: a registered name ('ollama', 'openai') or a "
             "dotted path 'pkg.module:ClassName' (default: env "
             "HKDATA_EMBED_PROVIDER or 'ollama')")
    parser.add_argument(
        "--model", default=None,
        help="Embedding model (default: env HKDATA_EMBED_MODEL or the backend default)")
    parser.add_argument(
        "--url", default=None,
        help="Embedding endpoint URL (default: env HKDATA_EMBED_URL or the backend default)")
    parser.add_argument(
        "--api-key", default=None,
        help="API key for the backend (default: env HKDATA_EMBED_API_KEY)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hkdata",
        description="Query and discover Hong Kong data.gov.hk datasets.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    info_parser = subparsers.add_parser("info", help="Show dataset metadata")
    info_parser.add_argument("dataset_ids", nargs="+", help="One or more dataset IDs")
    info_parser.set_defaults(func=cmd_info)

    test_parser = subparsers.add_parser("test", help="Test a dataset endpoint")
    test_parser.add_argument("urls", nargs="+", help="One or more endpoint URLs")
    test_parser.set_defaults(func=cmd_test)

    prog_search = subparsers.add_parser(
        "programs-search", help="Semantic search over runnable program functions")
    prog_search.add_argument("keywords", nargs="+", help="Natural-language query")
    prog_search.add_argument("--top-n", type=int, default=5,
                             help="Max results (default: 5)")
    prog_search.add_argument("--source", action="store_true",
                             help="Print the full function source")
    _add_embed_args(prog_search)
    prog_search.add_argument("--json", action="store_true", help="JSON output")
    prog_search.set_defaults(func=cmd_programs_search)

    prog_status = subparsers.add_parser(
        "programs-status", help="Show the program library and vector store")
    prog_status.add_argument("--json", action="store_true", help="JSON output")
    prog_status.set_defaults(func=cmd_programs_status)

    reindex_parser = subparsers.add_parser(
        "reindex", help="Extract + embed program functions and render the registry")
    _add_embed_args(reindex_parser)
    reindex_parser.add_argument("--batch", type=int, default=vectors.EMBED_BATCH,
                                help=f"Embedding batch size (default: {vectors.EMBED_BATCH})")
    reindex_parser.set_defaults(func=cmd_reindex)

    catalog_sync_parser = subparsers.add_parser(
        "catalog-sync", help="Seed/crawl the offline catalog (package_list + package_show)")
    catalog_sync_parser.add_argument("--full", action="store_true",
                                     help="Crawl every missing dataset (long, resumable)")
    catalog_sync_parser.add_argument("--refresh", action="store_true",
                                     help="Re-fetch datasets from the 14-day RSS feed")
    catalog_sync_parser.add_argument("--rate", type=float, default=catalog.DEFAULT_RATE,
                                     help=f"Requests per second (default: {catalog.DEFAULT_RATE})")
    catalog_sync_parser.add_argument("--limit", type=int, default=None,
                                     help="Max datasets to fetch in this run")
    catalog_sync_parser.add_argument("--lang", default="en",
                                     help="Comma-separated locales to fetch, e.g. en,tc,sc (default: en)")
    catalog_sync_parser.set_defaults(func=cmd_catalog_sync)

    catalog_embed_parser = subparsers.add_parser(
        "catalog-embed", help="Build the ChromaDB vector store (local or API embeddings)")
    _add_embed_args(catalog_embed_parser)
    catalog_embed_parser.add_argument("--batch", type=int, default=vectors.EMBED_BATCH,
                                      help=f"Embedding batch size (default: {vectors.EMBED_BATCH})")
    catalog_embed_parser.set_defaults(func=cmd_catalog_embed)

    catalog_search_parser = subparsers.add_parser(
        "catalog-search", help="Search the offline catalog (ChromaDB: dense + keyword)")
    catalog_search_parser.add_argument("keywords", nargs="+", help="Natural-language query")
    catalog_search_parser.add_argument("--top-n", type=int, default=10,
                                       help="Max results (default: 10)")
    _add_embed_args(catalog_search_parser)
    catalog_search_parser.add_argument("--json", action="store_true", help="JSON output")
    catalog_search_parser.set_defaults(func=cmd_catalog_search)

    catalog_status_parser = subparsers.add_parser(
        "catalog-status", help="Show offline catalog coverage")
    catalog_status_parser.add_argument("--json", action="store_true", help="JSON output")
    catalog_status_parser.set_defaults(func=cmd_catalog_status)

    embed_status_parser = subparsers.add_parser(
        "embed-status", help="Show the active embedding backend and store match")
    _add_embed_args(embed_status_parser)
    embed_status_parser.add_argument("--json", action="store_true", help="JSON output")
    embed_status_parser.set_defaults(func=cmd_embed_status)

    return parser


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ValueError as exc:  # e.g. unknown embedding provider
        _eprint(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
