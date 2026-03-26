# Developer Documentation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add three developer-facing Markdown files at the project root: `ARCHITECTURE.md`, `CONTRIBUTORS.md`, and `AGENTS.md`.

**Architecture:** Each file is a standalone Markdown document at the project root — the standard GitHub location for repo-level files. No code changes are required; these are pure documentation. `AGENTS.md` follows the Claude Code convention (root placement, machine-readable conventions).

**Tech Stack:** Markdown, git.

---

## Task 1: Create ARCHITECTURE.md

**Files:**
- Create: `ARCHITECTURE.md`

### Step 1: Create the file

```markdown
# Architecture

## Overview

`sphinx-coverage-report` is a Sphinx extension that parses code coverage files
(Cobertura XML, coverage.py JSON, lcov) and renders the data either as
standalone HTML tables or as [sphinx-needs](https://sphinx-needs.com/) nodes —
enabling coverage data to be cross-linked, filtered, and queried alongside
requirements and test-case nodes in a Sphinx documentation site.

## Module Map

```
sphinxcontrib/coverage_report/
├── coverage_report.py               — setup(), config values, Sphinx event wiring
├── config.py                        — config dataclass helpers
├── environment.py                   — CSS static-file injection
├── exceptions.py                    — CoverageReportFileNotFound, CoverageReportFileInvalid
├── coberturaparser.py               — Cobertura XML → CoverageData dict
├── jsonparser.py                    — coverage.py JSON → CoverageData dict
├── lcovparser.py                    — lcov → CoverageData dict
├── functions/
│   └── __init__.py                  — cr_link() dynamic function for sphinx-needs
└── directives/
    ├── coverage_common.py           — CoverageCommonDirective base class; threshold logic; file cache
    ├── coverage_results.py          — standalone table directive (no sphinx-needs dependency)
    ├── coverage_module.py           — sphinx-needs node for a single source file
    ├── coverage_package.py          — sphinx-needs node for a package; supports :expand:
    ├── coverage_function.py         — sphinx-needs node for a function/method
    └── coverage_report_directive.py — template-driven directive: expands into full report section
```

## Data Flow

```
coverage file (XML / JSON / lcov)
    │
    ▼
Parser (CoberturaParser / JsonParser / LcovParser)
    │  .parse() → plain dict:
    │  { line_rate, branch_rate, packages: [ { name, modules: [...] } ] }
    ▼
CoverageCommonDirective._resolve_path() + _load_coverage_file()
    │  resolves path relative to cr_rootdir, caches result on env.coveragereport_data
    ▼
Directive.run()
    │  extracts package/module/function entry from the dict
    │  computes status (passing / failing) against cr_threshold_* config values
    ▼
sphinx_needs.api.add_need()        ← need directives only
    │  creates a sphinx-needs node with custom fields (line_rate, branch_rate, …)
    ▼
Sphinx document tree
```

## sphinx-needs Integration

The `_sphinx_needs_update()` function (called on `config-inited`) does all
sphinx-needs setup in one place:

- **Extra fields** (`line_rate`, `branch_rate`, `lines_valid`, …) are registered
  via `add_field` (sphinx-needs ≥ 6) or `add_extra_option` (older). A
  compatibility shim in `coverage_report.py` selects the right call at runtime.
- **Need types** (`coveragereport`, `coveragepackage`, `coveragemodule`,
  `coveragefunction`) are registered via `add_need_type()` using the list-form
  config values `cr_report`, `cr_package`, `cr_module`, `cr_function`.
- **IDs** are auto-generated using `_make_hashed_id()`. The import path changed
  in sphinx-needs v4; the shim in `coverage_common.py` handles both.
- **`cr_link()`** is registered as a dynamic function via `add_dynamic_function()`
  so RST authors can write `:links: [[cr_link('filename', 'file')]]` to link
  coverage nodes to test-case nodes by field value.
- **`add_doc()`** is called after every `add_need()` to keep sphinx-needs'
  internal document registry consistent.

## Extension Points

### Adding a new parser

1. Create `sphinxcontrib/coverage_report/<name>parser.py`.
2. Implement a class with a `.parse()` method that returns a dict matching the
   shape produced by `CoberturaParser.parse()`:
   ```python
   {
       "line_rate": float,
       "branch_rate": float,
       "lines_valid": int,
       "lines_covered": int,
       "branches_valid": int,
       "branches_covered": int,
       "timestamp": str,
       "version": str,
       "packages": [
           {
               "name": str,
               "line_rate": float,
               "branch_rate": float,
               "lines_valid": int,
               "lines_covered": int,
               "branches_valid": int,
               "branches_covered": int,
               "modules": [
                   {
                       "name": str,
                       "filename": str,
                       "line_rate": float,
                       "branch_rate": float,
                       "lines_valid": int,
                       "lines_covered": int,
                       "branches_valid": int,
                       "branches_covered": int,
                       "missed_lines": list[int],
                       "complexity": float,
                       "functions": list[dict],  # {"name", "line_start", "hits"}
                   }
               ],
           }
       ],
   }
   ```
3. Register the extension in `_load_coverage_file()` in
   `directives/coverage_common.py` by adding a new `elif ext in (...):` branch.
4. Add tests in `tests/test_<name>_parser.py`.

### Adding a new directive

1. Create `sphinxcontrib/coverage_report/directives/<name>.py`.
2. Subclass `CoverageCommonDirective` (provides `_resolve_path`,
   `_warn_if_no_data`, and `get_location`).
3. Implement `run()` — resolve the path, load data, call `add_need()`.
4. Register in `coverage_report.py::_register_directives()` (not at module
   level — avoids circular imports at extension load time).
5. Add a config value in `setup()` if the directive needs configurable
   behaviour.
```

### Step 2: Verify the file renders correctly

Open `ARCHITECTURE.md` in any Markdown viewer and confirm:
- All three code fences close correctly
- The module tree diagram is readable
- The data-flow diagram is readable

### Step 3: Commit

```bash
git add ARCHITECTURE.md
git commit -m "docs: ARCHITECTURE.md — module map, data flow, extension points"
```

---

## Task 2: Create CONTRIBUTORS.md

**Files:**
- Create: `CONTRIBUTORS.md`

### Step 1: Create the file

```markdown
# Contributing

Thank you for contributing to `sphinx-coverage-report`!

## Development Setup

```bash
# Python 3.10+ required
uv venv && source .venv/bin/activate   # or: python -m venv .venv && source .venv/bin/activate
pip install -e ".[test,docs]"
```

## Running Tests

```bash
# Fast — current Python only, latest sphinx-needs
pytest tests/ -v

# Full matrix — Python 3.10 / 3.11 / 3.12 × sphinx-needs 6.3.0 / 7.0.0 / 8.0.0
nox -s tests
```

## Running the Docs Build

```bash
nox -s docs
```

This runs the test suite with `--cov` to emit `docs/_coverage/coverage.xml`,
then builds the Sphinx site with `-W` (warnings-as-errors).  It doubles as
an **end-to-end integration test** — a passing `nox -s docs` verifies the
extension loads, parses real coverage data, and creates valid sphinx-needs nodes.

## Linting

```bash
nox -s lint   # runs ruff over sphinxcontrib/ and tests/
```

## Adding a Parser

See `ARCHITECTURE.md` → *Extension Points* for the required dict shape.

1. Create `sphinxcontrib/coverage_report/<name>parser.py` with a `.parse()` method.
2. Register it in `directives/coverage_common.py::_load_coverage_file()`.
3. Add tests in `tests/test_<name>_parser.py`.

Existing parsers to use as reference:

| Format | File |
|--------|------|
| Cobertura XML | `coberturaparser.py` |
| coverage.py JSON | `jsonparser.py` |
| lcov | `lcovparser.py` |

## Adding a Directive

1. Create `sphinxcontrib/coverage_report/directives/<name>.py`.
2. Subclass `CoverageCommonDirective`.
3. Register in `coverage_report.py::_register_directives()`.
4. Add a config value in `setup()` if needed.

## PR Checklist

- [ ] `pytest tests/ -v` passes
- [ ] `nox -s docs` passes (e2e + Sphinx -W)
- [ ] No new ruff lint errors (`nox -s lint`)
```

### Step 2: Commit

```bash
git add CONTRIBUTORS.md
git commit -m "docs: CONTRIBUTORS.md — setup, test, lint, extension guide"
```

---

## Task 3: Create AGENTS.md

**Files:**
- Create: `AGENTS.md`

### Step 1: Create the file

```markdown
# Agent Guidelines

Guidelines for AI coding agents working in this repository.

## What This Project Does

A Sphinx extension that parses coverage files (Cobertura XML, coverage.py JSON,
lcov) and renders the data as standalone HTML tables or as
[sphinx-needs](https://sphinx-needs.com/) nodes.

## Key Files

| File | Role |
|------|------|
| `sphinxcontrib/coverage_report/coverage_report.py` | **Start here.** `setup()`, all config values, Sphinx event wiring. |
| `sphinxcontrib/coverage_report/directives/coverage_common.py` | Base directive class; file-load cache; threshold logic. |
| `sphinxcontrib/coverage_report/coberturaparser.py` | Reference parser — shows the expected CoverageData shape. |
| `sphinxcontrib/coverage_report/functions/__init__.py` | `cr_link()` sphinx-needs dynamic function. |
| `noxfile.py` | All runnable sessions: `tests`, `lint`, `coverage`, `docs`. |

## Running Tests

```bash
# Unit tests only (fast)
pytest tests/ -v

# End-to-end (generates coverage.xml, then builds Sphinx site with -W)
nox -s docs
```

## Known Gotchas

- **`SphinxDirective` does not expose `self.app`** — use `self.env.app` in all
  directive `run()` methods.
- **`_make_hashed_id` import path changed in sphinx-needs v4** — the shim in
  `coverage_common.py` handles both; do not import it directly.
- **`coverage.xml` package names are short** (`.`, `directives`, `functions`),
  not dotted Python names like `sphinxcontrib.coverage_report`. Do not assume
  dotted names when filtering by package.
- **`cr_rootdir` must be a `pathlib.Path`**, not a `str` — `docs/conf.py` uses
  `Path(__file__).parent`; a `str` triggers a Sphinx type warning.
- **Parsers are cached per Sphinx env** in `env.coveragereport_data` — if you
  add a new parser, register it in `_load_coverage_file()` in
  `directives/coverage_common.py`.

## Conventions

- New parsers return the same dict shape as `CoberturaParser.parse()` — see
  `ARCHITECTURE.md` for the full shape.
- Need directives subclass `CoverageCommonDirective`.
- Register new directives in `_register_directives()`, **not at module level**
  (late import avoids circular imports at extension load time).
- Config values for need types use a 6-element list:
  `[directive-name, type-id, title-prefix, id-prefix, colour, style]`.

## What Not To Do

- Do **not** commit `docs/_coverage/` or `docs/_build/` — both are gitignored
  and generated at build time.
- Do **not** add `Co-Authored-By` trailers or any attribution to commits.
- Do **not** import `sphinx_needs` APIs at module level in directive files —
  import inside `run()` or inside `_register_directives()` to avoid load-order
  issues.
```

### Step 2: Commit

```bash
git add AGENTS.md
git commit -m "docs: AGENTS.md — key files, gotchas, conventions for AI agents"
```
