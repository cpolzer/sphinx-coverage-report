# Contributing

Thank you for contributing to `sphinx-coverage-report`!

## Development Setup

```bash
# Python 3.10+ required
uv venv && source .venv/bin/activate && uv pip install -e ".[test,docs]"
# or: python -m venv .venv && source .venv/bin/activate && pip install -e ".[test,docs]"
```

## Running Tests

```bash
# Fast — current Python only, latest sphinx-needs
pytest tests/ -v

# Full matrix — Python 3.10 / 3.11 / 3.12 × sphinx-needs 6.3.0 / 7.0.0 / 8.0.0
nox -s tests
# Requires Python 3.10, 3.11, and 3.12 on PATH.
# To run a single combination: nox -s "tests-3.12(sphinx_needs='8.0.0')"
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

1. Create a class `<Name>Parser` in `sphinxcontrib/coverage_report/<name>parser.py`.
   The constructor takes the filepath as its only argument; the class exposes a `.parse()` instance method.
2. Add an `elif ext in (...):` branch in `directives/coverage_common.py::_load_coverage_file()`
   that imports and instantiates your class.
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
3. Register in `sphinxcontrib/coverage_report/coverage_report.py::_register_directives()`.
4. Add a config value in `setup()` if needed.

## PR Checklist

- [ ] `pytest tests/ -v` passes
- [ ] `nox -s docs` passes (e2e + Sphinx -W)
- [ ] No new ruff lint errors (`nox -s lint`)
