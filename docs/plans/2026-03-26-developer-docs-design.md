# Developer Documentation Design

**Date:** 2026-03-26
**Status:** Approved

---

## Overview

Add three developer-facing Markdown files at the project root:

- `ARCHITECTURE.md` — codebase map and data-flow explanation for contributors and AI agents
- `CONTRIBUTORS.md` — setup, test, and PR workflow guide for human contributors
- `AGENTS.md` — conventions, gotchas, and key-file index for AI coding agents

All three live at the project root (standard GitHub location; `AGENTS.md` root placement is the Claude Code convention).

---

## ARCHITECTURE.md

### Overview section
One-paragraph description of what the extension does: parses coverage files (Cobertura XML, coverage.py JSON, lcov), then exposes Sphinx directives that render coverage data either as standalone tables or as sphinx-needs nodes.

### Module Map

```
sphinxcontrib/coverage_report/
├── coverage_report.py              — setup(), config values, event wiring
├── config.py                       — config dataclass helpers
├── environment.py                  — CSS static file injection
├── exceptions.py                   — custom exceptions
├── coberturaparser.py              — Cobertura XML → CoverageData
├── jsonparser.py                   — coverage.py JSON → CoverageData
├── lcovparser.py                   — lcov → CoverageData
├── functions/__init__.py           — cr_link() dynamic function
└── directives/
    ├── coverage_common.py          — base directive + threshold logic
    ├── coverage_results.py         — standalone table (no sphinx-needs)
    ├── coverage_module.py          — sphinx-needs node: module
    ├── coverage_package.py         — sphinx-needs node: package
    ├── coverage_function.py        — sphinx-needs node: function
    └── coverage_report_directive.py — template expander
```

### Data Flow

```
coverage file  →  parser  →  CoverageData  →  directive  →  sphinx-needs add_need()
```

### sphinx-needs Integration

- Need types registered via `add_need_type()` in `_sphinx_needs_update()`
- Extra fields (line_rate, branch_rate, etc.) registered via `add_field` / `add_extra_option` compatibility shim
- IDs auto-generated with `_make_hashed_id()` (import shim handles API change in sphinx-needs v4)
- `cr_link()` registered as a dynamic function via `add_dynamic_function()`
- `add_doc()` called after each need to keep the env document registry consistent

### Extension Points

- **New parser:** implement `parse(filepath, encoding) -> CoverageData` and wire into the relevant directive's `run()` method
- **New directive:** subclass `CoverageCommonDirective`, register in `_register_directives()`

---

## CONTRIBUTORS.md

### Development Setup

```bash
uv venv && source .venv/bin/activate
pip install -e ".[test,docs]"
```

### Running Tests

```bash
pytest tests/ -v                  # fast, current Python only
nox -s tests                      # full matrix: Python 3.10/3.11/3.12 × sphinx-needs 6.3/7.0/8.0
```

### Running Docs Build

```bash
nox -s docs
# Generates docs/_coverage/coverage.xml, then runs sphinx-build -W
# Also serves as the e2e integration test
```

### Adding a Parser

1. Create `sphinxcontrib/coverage_report/<name>parser.py`
2. Return the same `CoverageData` shape as `coberturaparser.py`
3. Add tests in `tests/test_<name>_parser.py`

### Adding a Directive

1. Create `sphinxcontrib/coverage_report/directives/<name>.py`
2. Subclass `CoverageCommonDirective`
3. Register in `coverage_report.py::_register_directives()`
4. Add config value in `setup()` if needed

### PR Checklist

- [ ] `pytest tests/ -v` passes
- [ ] `nox -s docs` passes (e2e)
- [ ] No new Sphinx `-W` warnings

---

## AGENTS.md

### What This Project Does

A Sphinx extension that parses coverage files and renders the data as either standalone tables or sphinx-needs nodes in a Sphinx documentation site.

### Key Files

| File | Role |
|------|------|
| `sphinxcontrib/coverage_report/coverage_report.py` | Start here: `setup()`, config values, event wiring |
| `directives/coverage_common.py` | Base class for all need directives; threshold logic |
| `coberturaparser.py` / `jsonparser.py` / `lcovparser.py` | Parsers — all return the same CoverageData shape |
| `functions/__init__.py` | `cr_link()` dynamic function |

### Running Tests

```bash
pytest tests/ -v
nox -s docs   # e2e: generates coverage.xml + builds Sphinx site
```

### Known Gotchas

- `SphinxDirective` does **not** expose `self.app` — use `self.env.app`
- `_make_hashed_id` import path changed in sphinx-needs v4 — use the shim already in `coverage_common.py`
- `coverage.xml` package names are short (`.`, `directives`, `functions`), not dotted Python names
- `cr_rootdir` must be a `Path`, not a `str` (Sphinx type warning otherwise)

### Conventions

- New parsers return the same `CoverageData` shape as `coberturaparser`
- Need directives subclass `CoverageCommonDirective`
- Register new directives in `_register_directives()`, not at module level (avoids circular imports at extension load time)

### What Not To Do

- Do not commit `docs/_coverage/` or `docs/_build/` — both are gitignored and generated at build time
- Do not add `Co-Authored-By` trailers to commits
