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
- **`_make_hashed_id` import path changed in sphinx-needs v4** — each need-directive file
  (`coverage_module.py`, `coverage_package.py`, `coverage_function.py`) carries its own
  try/except shim at module level. Copy the shim pattern from one of those files if you
  add a new need directive; do not import `_make_hashed_id` directly.
- **`coverage.xml` package names are short** (`.`, `directives`, `functions`),
  not dotted Python names like `sphinxcontrib.coverage_report`. Do not assume
  dotted names when filtering by package.
- **`cr_rootdir` should be a `pathlib.Path` when set in `conf.py`** — the
  default (`app.confdir`) is a `str` and works fine at runtime, but if you
  set `cr_rootdir` explicitly, use `Path(__file__).parent` (as `docs/conf.py`
  does) to avoid Sphinx type-validation warnings.
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

## SpecDriven

We are using the "obra superpowers". Document locations:
Design Specs -> docs/superpowers/specs
Implementation plan -> docs/superpowers/plans

Always ensure those documents are available.

## What Not To Do

- Do **not** commit `docs/_coverage/` or `docs/_build/` — both are gitignored
  and generated at build time.
- Do **not** import directive files at the top level of `coverage_report.py` —
  all directive imports must stay inside `_register_directives()` to avoid
  circular imports at extension load time. Module-level `sphinx_needs` imports
  within a directive file are fine because the directive file itself is not
  imported until `_register_directives()` runs.
