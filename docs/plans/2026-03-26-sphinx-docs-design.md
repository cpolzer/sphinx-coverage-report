# sphinx-coverage-report Documentation Site — Design

**Date:** 2026-03-26
**Status:** Approved

---

## Overview

Add a user-facing Sphinx documentation site to `sphinx-coverage-report`. The docs dogfood the extension itself by rendering the extension's own test coverage data using its own directives.

---

## Goals

- Provide user-facing documentation: installation, configuration, per-directive reference, changelog
- Demonstrate the extension in action by showing its own coverage (dogfooding)
- Keep coverage data always fresh by generating it at doc-build time
- Fit naturally into the existing nox workflow

---

## Non-Goals

- Hosting / deployment configuration (ReadTheDocs, GitHub Pages setup)
- API reference auto-generated from docstrings

---

## Directory Structure

```
docs/
├── conf.py
├── index.rst                # landing page + toctree
├── installation.rst
├── configuration.rst        # all cr_* config values
├── directives/
│   ├── index.rst
│   ├── coverage-results.rst
│   ├── coverage-module.rst
│   ├── coverage-package.rst
│   ├── coverage-function.rst
│   └── coverage-report.rst
├── coverage.rst             # dogfood page — extension's own coverage
├── changelog.rst
└── _coverage/               # gitignored — generated at build time
    └── coverage.xml
```

---

## Configuration (`docs/conf.py`)

```python
import os

extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
]
html_theme = "furo"
needs_id_regex = ".*"
cr_rootdir = os.path.dirname(__file__)
cr_warn_no_data = True
```

`docs/_coverage/` is added to `.gitignore` — the generated XML is never committed.

---

## Coverage Page (`docs/coverage.rst`)

Uses `coverage-report` to render a full self-referential coverage report:

```rst
Coverage
========

This page shows test coverage for ``sphinx-coverage-report`` itself,
generated at doc-build time.

.. coverage-report:: _coverage/coverage.xml
   :id: CR_SELF
   :title: sphinx-coverage-report coverage
   :tags: CR_SELF
```

The `coverage-report` directive expands via the default template to produce:

- A `coverage-results` table (line/branch rates per module)
- A `needtable` of all `coverage-module` nodes tagged `CR_SELF`

---

## Build Orchestration

### `pyproject.toml` — docs optional dependencies

```toml
[project.optional-dependencies]
docs = [
    "sphinx",
    "furo",
    "sphinx-needs>=6.0.0",
]
```

### `noxfile.py` — docs session

```python
@nox.session
def docs(session):
    session.install("-e", ".[docs]")
    session.run(
        "pytest",
        "--cov=sphinxcontrib/coverage_report",
        "--cov-report=xml:docs/_coverage/coverage.xml",
        "-q",
    )
    session.run("sphinx-build", "docs", "docs/_build/html")
```

Running `nox -s docs` will:
1. Install the package and doc dependencies
2. Run the test suite and emit `docs/_coverage/coverage.xml`
3. Build the Sphinx site to `docs/_build/html`

### Docs build as end-to-end test

The `nox -s docs` session doubles as an **end-to-end integration test**. A successful build verifies:

- The extension loads and registers all directives without errors
- `coverage-report` parses the real `coverage.xml` generated from the test suite
- All need directives (`coverage-module`, `coverage-package`, etc.) create valid sphinx-needs nodes
- The `needtable` in the template resolves correctly against those nodes
- The furo theme renders without conflicts

The nox session passes `sphinx-build -W` (warnings-as-errors) so any broken directive, missing data, or malformed node fails the build. This is added to the CI matrix alongside the unit test sessions.

---

## Dependencies

| Package | Reason |
|---------|--------|
| `sphinx` | Doc build framework |
| `furo` | Theme |
| `sphinx-needs >= 6.0.0` | Already a runtime dep; needed in docs build for need directives |

---

## `.gitignore` additions

```
docs/_coverage/
docs/_build/
```
