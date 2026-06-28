# AGENTS.md

## Cursor Cloud specific instructions

This repo hosts **two products in one tree**:

1. **Newbie** — a library code-indexing + retrieval/MCP toolchain (`scripts/`, `config/libraries.yaml`, `store/`, `.cursor/`). Its runnable service is the **nb-symbols MCP server**.
2. **pypdf** — a pure-Python PDF library (`pypdf/`, `tests/`, `pyproject.toml`). It is a library, so there is no app server; "running" it means importing it and running its test suite.

### Environment / virtualenvs (important, non-obvious)

The install step is `bash scripts/cloud_bootstrap.sh` (wired via `.cursor/environment.json`, which builds `.cursor/Dockerfile`). It is idempotent and creates **two separate virtualenvs**:

- **`.venv`** — Newbie toolchain + MCP server deps (`requirements-mcp.txt`). Used by the `nb-symbols` terminal in `environment.json` and by the indexing scripts.
- **`.venv-pypdf`** — pypdf dev/test deps (`requirements/ci-3.11.txt` + editable pypdf).

**Why two venvs:** pypdf's pinned `requirements/ci-3.11.txt` pins `typing-extensions==4.12.2`, which breaks the MCP server's `pydantic`/`pydantic_core` (they need `typing-extensions>=4.14.1`, e.g. `ImportError: cannot import name 'Sentinel'`). Keep them separate — do **not** install pypdf's CI requirements into `.venv`.

The pypdf venv setup in `cloud_bootstrap.sh` is fail-open (never blocks Newbie/MCP setup) and can be skipped with `NB_SKIP_PYPDF_VENV=1`. Index rebuild can be skipped with `NB_SKIP_REINDEX=1`. The Dockerfile installs `python3-venv`; without it `python3 -m venv` fails.

### Running the nb-symbols MCP server (the runnable service)

Started automatically by `.cursor/environment.json` on HTTP port `8848`. To run manually:

```bash
. .venv/bin/activate
NB_MCP_TRANSPORT=http NB_MCP_HOST=127.0.0.1 NB_MCP_PORT=8848 python scripts/mcp_symbols_server.py --transport http
```

A plain `curl http://127.0.0.1:8848/mcp` returns HTTP 406 — that is expected; the endpoint requires an MCP handshake (`Accept: application/json, text/event-stream`). Tools: `list_libraries`, `get_library_path`, `search_library_code`, `lookup_symbol`, `search_symbols`, `verify_imports`. CLI equivalent: `python scripts/query.py --library pypdf --prompt "..."`. Health check: `python scripts/doctor.py`.

### Lint / test commands

pypdf (use `.venv-pypdf`):

```bash
. .venv-pypdf/bin/activate
ruff check pypdf make_release.py      # library lint (see Makefile `ruff` target)
mypy pypdf                            # Makefile `mypy` target
pytest tests -m "not enable_socket and not slow" --ignore=tests/chunk  # offline suite
```

Notes:
- pytest defaults to `--disable-socket` (`pyproject.toml`); tests marked `enable_socket` need network and download PDFs into `tests/pdf_cache/` (CI runs `download_test_pdfs()` first).
- `ruff check .` / `mypy .` (as CI's codestyle job runs in the upstream pypdf-only tree) report many errors here because this tree also contains the Newbie overlay (`scripts/`, `tests/chunk/`) and the gitignored `repos/<lib>` checkout, which don't follow pypdf's strict `select = ["ALL"]` config. Scope ruff to `pypdf` (+ `make_release.py`) for the library.

Newbie chunk tests (use `.venv`, which has tree-sitter): `pytest tests/chunk`. The `test_pypdf_symbol_regression` case can fail when `tests/chunk/pypdf_symbols_baseline.json` is out of date relative to the pinned `customer_pypdf` ref in `config/libraries.yaml` — this is a baseline/data mismatch, not an environment problem.
