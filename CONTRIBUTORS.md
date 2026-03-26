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
