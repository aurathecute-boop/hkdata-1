#!/bin/bash
# Single entry point for the hkdata CLI.
#
#   bash ./hk.sh <subcommand> [args...]     # the CLI (info, test, programs-search, ...)
#   bash ./hk.sh python - <<'EOF'           # run program source in the venv interpreter
#   EOF
#
# Picks the venv interpreter when it exists (chromadb + the program libraries
# live there), else python3.
set -eo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

if [ "${1:-}" = "python" ]; then
    shift
    if [ ! -x "$ROOT/.venv/bin/python" ]; then
        echo "hkdata: no venv at $ROOT/.venv — create it first (SETUP.md):" >&2
        echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements-vectors.txt -r requirements-programs.txt" >&2
        exit 1
    fi
    exec "$ROOT/.venv/bin/python" "$@"
fi

exec "$PY" "$ROOT/scripts/hkdata.py" "$@"
