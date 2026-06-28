#!/usr/bin/env bash
# Newbie cloud bootstrap — idempotent install step for Cursor Cloud Agents and CI.
#
# Rebuilds everything a fresh VM needs that is NOT committed to the repo:
#   1. a Python virtualenv (.venv)
#   2. Python deps, including the MCP server deps (requirements-mcp.txt)
#   3. git submodules (no-op when there are none)
#   4. the library index — re-clones repos/<lib> at the pinned ref/commit from
#      config/libraries.yaml and re-chunks store/chunks/ (both are gitignored)
#
# Safe to run repeatedly: each step checks state before doing work. Never floats
# library versions — refs/commits come straight from config/libraries.yaml.
#
# Usage:  bash scripts/cloud_bootstrap.sh
# Env:    NB_SKIP_REINDEX=1   skip the (slow) index rebuild
#         NB_PYTHON=python3.13 choose the interpreter used to create the venv
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON_BIN="${NB_PYTHON:-python3}"
VENV_DIR="$REPO_ROOT/.venv"

echo "==> Newbie cloud bootstrap (repo: $REPO_ROOT)"

# 1. Virtualenv ---------------------------------------------------------------
if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "==> Creating virtualenv at .venv"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "==> Reusing existing virtualenv"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip --quiet

# 2. Python dependencies (runtime + MCP server) -------------------------------
echo "==> Installing Python dependencies"
if [ -f requirements-mcp.txt ]; then
  python -m pip install -r requirements-mcp.txt --quiet
elif [ -f requirements.txt ]; then
  python -m pip install -r requirements.txt --quiet
fi

# 3. Git submodules (idempotent; no-op without a .gitmodules) ------------------
if [ -f .gitmodules ]; then
  echo "==> Updating git submodules"
  git submodule update --init --recursive
fi

# 4. Rebuild the index at the pinned refs -------------------------------------
if [ "${NB_SKIP_REINDEX:-0}" = "1" ]; then
  echo "==> NB_SKIP_REINDEX=1 — skipping index rebuild"
else
  echo "==> Rebuilding library index from config/libraries.yaml (pinned refs)"
  python scripts/reindex_all.py
fi

echo "==> Health check"
python scripts/doctor.py || echo "doctor reported issues (see above) — bootstrap continued (fail-open)"

# 5. pypdf dev/test virtualenv (separate from .venv) --------------------------
# The repo also ships the pypdf library + its test suite. Its pinned test deps
# (requirements/ci-3.11.txt) pin typing-extensions to a version that conflicts
# with the MCP server's pydantic, so pypdf development uses its own .venv-pypdf.
# Fail-open: a problem here must never block the Newbie/MCP setup above.
if [ "${NB_SKIP_PYPDF_VENV:-0}" = "1" ]; then
  echo "==> NB_SKIP_PYPDF_VENV=1 — skipping pypdf dev venv setup"
elif [ -f requirements/ci-3.11.txt ] && [ -f pyproject.toml ]; then
  echo "==> Setting up pypdf dev/test venv at .venv-pypdf"
  (
    set -e
    if [ ! -x "$REPO_ROOT/.venv-pypdf/bin/python" ]; then
      "$PYTHON_BIN" -m venv "$REPO_ROOT/.venv-pypdf"
    fi
    # shellcheck disable=SC1091
    source "$REPO_ROOT/.venv-pypdf/bin/activate"
    python -m pip install --upgrade pip --quiet
    python -m pip install -r requirements/ci-3.11.txt -e . --quiet
  ) || echo "pypdf dev venv setup reported issues (see above) — bootstrap continued (fail-open)"
fi

echo "==> Newbie cloud bootstrap complete"
