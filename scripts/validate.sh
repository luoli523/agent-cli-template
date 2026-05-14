#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$REPO_ROOT/.venv/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "ERROR: Python virtual environment not found at .venv/." >&2
    echo "Run: uv sync" >&2
    if ! command -v uv >/dev/null 2>&1; then
        echo "uv is not installed or not on PATH. Install uv first, then run: uv sync" >&2
    fi
    exit 1
fi

cd "$REPO_ROOT"
"$PYTHON_BIN" scripts/validate_repo.py "$@"
