# Sphinx Documentation Site Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a user-facing Sphinx documentation site for `sphinx-coverage-report` that dogfoods the extension by rendering its own test coverage data.

**Architecture:** A `docs/` Sphinx site using the furo theme. A dedicated `nox -s docs` session first runs `pytest --cov` to emit `docs/_coverage/coverage.xml`, then calls `sphinx-build -W` (warnings-as-errors). The docs build therefore doubles as an end-to-end integration test. Coverage data is never committed — always generated fresh.

**Tech Stack:** Python 3.10+, Sphinx, furo, sphinx-needs >= 6.0.0, sphinxcontrib.coverage_report (this package), nox, pytest-cov.

---

## File Map

```
docs/
├── conf.py
├── index.rst
├── installation.rst
├── configuration.rst
├── directives/
│   ├── index.rst
│   ├── coverage-results.rst
│   ├── coverage-module.rst
│   ├── coverage-package.rst
│   ├── coverage-function.rst
│   └── coverage-report.rst
├── coverage.rst
├── changelog.rst
└── _coverage/           ← gitignored, generated at build time
    └── coverage.xml

pyproject.toml           ← add [docs] optional deps
noxfile.py               ← add docs session
.github/workflows/ci.yaml ← add docs job
.gitignore               ← add docs/_coverage/ and docs/_build/
```

---

## Task 1: Scaffolding — pyproject, .gitignore, conf.py, index.rst

**Files:**
- Modify: `pyproject.toml`
- Modify: `.gitignore`
- Create: `docs/conf.py`
- Create: `docs/index.rst`

- [ ] **Step 1: Add docs optional deps to pyproject.toml**

```toml
[project.optional-dependencies]
docs = [
    "sphinx",
    "furo",
    "sphinx-needs>=6.0.0",
    "pytest-cov",
]
```

- [ ] **Step 2: Add generated dirs to .gitignore**

Append to `.gitignore`:
```
docs/_coverage/
docs/_build/
```

- [ ] **Step 3: Create docs/conf.py**

```python
# docs/conf.py
import os

project = "sphinx-coverage-report"
author = "~chrstian polzer"
release = "0.1.0"

extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
]

html_theme = "furo"
needs_id_regex = ".*"
cr_rootdir = os.path.dirname(__file__)
cr_warn_no_data = True
```

- [ ] **Step 4: Create docs/index.rst**

```rst
sphinx-coverage-report
======================

Sphinx extension for rendering code coverage reports as structured documentation.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   configuration
   directives/index
   coverage
   changelog
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore docs/conf.py docs/index.rst
git commit -m "docs: scaffolding — conf.py, index, deps, gitignore"
```

---

## Task 2: Installation and configuration pages

**Files:**
- Create: `docs/installation.rst`
- Create: `docs/configuration.rst`

- [ ] **Step 1: Create docs/installation.rst**

```rst
Installation
============

Install via pip::

    pip install sphinx-coverage-report

Add to your Sphinx ``conf.py``::

    extensions = [
        "sphinx_needs",
        "sphinxcontrib.coverage_report",
    ]

``sphinx-needs`` must be listed before ``sphinxcontrib.coverage_report``.

Requirements
------------

- Python >= 3.10
- Sphinx > 4.0
- sphinx-needs >= 6.0.0
```

- [ ] **Step 2: Create docs/configuration.rst**

```rst
Configuration
=============

All configuration values are set in your Sphinx ``conf.py``.

Root directory
--------------

.. code-block:: python

   cr_rootdir = "."  # default: Sphinx confdir

Base directory for resolving relative paths in directives.

Import encoding
---------------

.. code-block:: python

   cr_import_encoding = "utf-8"

Extra options
-------------

.. code-block:: python

   cr_extra_options = []

List of additional field names to register with sphinx-needs.

Need type configuration
-----------------------

Each coverage level maps to a sphinx-needs type. The format is
``[directive-name, type-id, title-prefix, id-prefix, color, style]``.

.. code-block:: python

   cr_report   = ["coverage-report",   "coveragereport",   "Coverage Report",   "CR_", "#4a90d9", "node"]
   cr_package  = ["coverage-package",  "coveragepackage",  "Coverage Package",  "CP_", "#7ab648", "folder"]
   cr_module   = ["coverage-module",   "coveragemodule",   "Coverage Module",   "CM_", "#f0ad4e", "rectangle"]
   cr_function = ["coverage-function", "coveragefunction", "Coverage Function", "CF_", "#cccccc", "rectangle"]

Thresholds
----------

.. code-block:: python

   cr_threshold_line_rate   = 0.80  # default
   cr_threshold_branch_rate = 0.75  # default

   # per-level overrides (optional)
   cr_threshold_report  = {}
   cr_threshold_package = {}
   cr_threshold_module  = {}

A need's ``status`` is set to ``"failing"`` if either rate falls below the threshold.

ID hash lengths
---------------

.. code-block:: python

   cr_module_id_length  = 5
   cr_package_id_length = 3

JSON mapping
------------

.. code-block:: python

   cr_json_mapping = { ... }  # see source for full default

Controls how coverage.py JSON keys map to normalized fields.

Warnings
--------

.. code-block:: python

   cr_warn_no_data = True

Emit Sphinx warnings when a directive references missing coverage data.
```

- [ ] **Step 3: Commit**

```bash
git add docs/installation.rst docs/configuration.rst
git commit -m "docs: installation and configuration pages"
```

---

## Task 3: Directive reference pages

**Files:**
- Create: `docs/directives/index.rst`
- Create: `docs/directives/coverage-results.rst`
- Create: `docs/directives/coverage-module.rst`
- Create: `docs/directives/coverage-package.rst`
- Create: `docs/directives/coverage-function.rst`
- Create: `docs/directives/coverage-report.rst`

- [ ] **Step 1: Create docs/directives/index.rst**

```rst
Directives
==========

.. toctree::

   coverage-results
   coverage-module
   coverage-package
   coverage-function
   coverage-report
```

- [ ] **Step 2: Create docs/directives/coverage-results.rst**

```rst
coverage-results
================

Renders a standalone coverage table with no sphinx-needs dependency.

.. code-block:: rst

   .. coverage-results:: path/to/coverage.xml

Options
-------

``:package:``
    Filter to a single package by name.

Example
-------

.. code-block:: rst

   .. coverage-results:: coverage.xml
      :package: mypackage
```

- [ ] **Step 3: Create docs/directives/coverage-module.rst**

```rst
coverage-module
===============

Creates a sphinx-needs node for a single source file.

.. code-block:: rst

   .. coverage-module:: path/to/coverage.xml
      :package: mypackage
      :module: module.py
      :id: CM_001

Options
-------

``:id:``
    Explicit sphinx-needs ID. Auto-generated from a hash if omitted.

``:status:``
    Override computed status (``passing`` or ``failing``).

``:tags:``
    Comma-separated sphinx-needs tags.

``:links:``
    Comma-separated IDs to link to (e.g. test-case nodes).

``:package:``
    Package name to look up in the coverage file.

``:module:``
    Module filename (``module.py`` or ``mypackage/module.py``).

Fields populated
----------------

``line_rate``, ``branch_rate``, ``lines_valid``, ``lines_covered``,
``branches_valid``, ``branches_covered``, ``missed_lines``,
``filename``, ``package``, ``complexity``.
```

- [ ] **Step 4: Create docs/directives/coverage-package.rst**

```rst
coverage-package
================

Creates a sphinx-needs node for a package with aggregated coverage stats.

.. code-block:: rst

   .. coverage-package:: path/to/coverage.xml
      :package: mypackage
      :id: CP_001

Options
-------

``:id:``, ``:status:``, ``:tags:``, ``:links:``, ``:package:``
    Same as :doc:`coverage-module`.

``:expand:``
    Flag. When set, auto-generates a ``coverage-module`` node for every
    module in the package, linked back to this package node.

Fields populated
----------------

``line_rate``, ``branch_rate``, ``lines_valid``, ``lines_covered``,
``branches_valid``, ``branches_covered``, ``package``.
```

- [ ] **Step 5: Create docs/directives/coverage-function.rst**

```rst
coverage-function
=================

Creates a sphinx-needs node for a single function or method.

.. code-block:: rst

   .. coverage-function:: path/to/coverage.xml
      :package: mypackage
      :module: module.py
      :function: my_function
      :id: CF_001

Options
-------

``:id:``, ``:status:``, ``:tags:``, ``:links:``, ``:package:``, ``:module:``
    Same as :doc:`coverage-module`.

``:function:``
    Function name to look up. Returns the first match if omitted.

Fields populated
----------------

``hits``, ``line_start``, ``filename``, ``package``.

.. note::

   Function-level data is only available from JSON and lcov formats.
   Cobertura XML does not carry reliable function hit counts.
```

- [ ] **Step 6: Create docs/directives/coverage-report.rst**

```rst
coverage-report
===============

Template-driven directive that expands into a full coverage report section.

Inserts a ``coverage-results`` table and a ``needtable`` of all
``coverage-module`` nodes matching the given tag.

.. code-block:: rst

   .. coverage-report:: path/to/coverage.xml
      :id: CR_001
      :title: My Coverage Report
      :tags: backend

Options
-------

``:id:``
    ID used as the tag filter in the expanded ``needtable``.

``:title:``
    Section heading. Defaults to ``Coverage Report: <filepath>``.

``:tags:``
    Additional sphinx-needs tags. Defaults to the value of ``:id:``.

Template
--------

The default template lives at
``sphinxcontrib/coverage_report/directives/coverage_report_template.txt``.
Override globally with ``cr_report_template = "/path/to/template.txt"`` in
``conf.py``.
```

- [ ] **Step 7: Commit**

```bash
git add docs/directives/
git commit -m "docs: directive reference pages"
```

---

## Task 4: Coverage (dogfood) and changelog pages

**Files:**
- Create: `docs/coverage.rst`
- Create: `docs/changelog.rst`

- [ ] **Step 1: Create docs/coverage.rst**

```rst
Coverage
========

This page shows test coverage for ``sphinx-coverage-report`` itself,
generated at doc-build time by running the test suite with ``pytest --cov``.

.. coverage-report:: _coverage/coverage.xml
   :id: CR_SELF
   :title: sphinx-coverage-report coverage
   :tags: CR_SELF
```

- [ ] **Step 2: Create docs/changelog.rst**

```rst
Changelog
=========

0.1.0 (2026-03-26)
-------------------

- Initial release.
- Parsers: Cobertura XML, lcov, coverage.py JSON.
- Directives: ``coverage-results``, ``coverage-module``, ``coverage-package``,
  ``coverage-function``, ``coverage-report``.
- sphinx-needs integration: need types, extra fields, ``cr_link()`` dynamic function.
- Threshold-based ``status`` (passing/failing).
- Configurable warnings for missing coverage data.
```

- [ ] **Step 3: Commit**

```bash
git add docs/coverage.rst docs/changelog.rst
git commit -m "docs: coverage dogfood page and changelog"
```

---

## Task 5: nox docs session and first build

**Files:**
- Modify: `noxfile.py`

- [ ] **Step 1: Add docs session to noxfile.py**

```python
@nox.session
def docs(session):
    session.install("-e", ".[docs,test]")
    session.run(
        "pytest",
        "--cov=sphinxcontrib/coverage_report",
        "--cov-report=xml:docs/_coverage/coverage.xml",
        "-q",
    )
    session.run("sphinx-build", "-W", "docs", "docs/_build/html")
```

The `.[docs,test]` extra installs furo, sphinx, sphinx-needs, and pytest-cov.
`-W` turns warnings into errors so broken directives fail the build.

- [ ] **Step 2: Run the docs build**

```bash
nox -s docs
```

Expected: all pytest tests pass, then `sphinx-build` completes with exit 0 and outputs `docs/_build/html/index.html`.

If you see a sphinx-needs warning about a missing `needs_id_regex`, add `needs_id_regex = ".*"` to `docs/conf.py` (it is already in the template above).

If `coverage-report` expands into a `needtable` that cannot find any nodes, verify the `_coverage/coverage.xml` was written to `docs/_coverage/` and that `cr_rootdir` is set to `os.path.dirname(__file__)` in `conf.py`.

- [ ] **Step 3: Commit**

```bash
git add noxfile.py
git commit -m "docs: nox docs session — coverage generation + sphinx build"
```

---

## Task 6: CI integration

**Files:**
- Modify: `.github/workflows/ci.yaml`

- [ ] **Step 1: Add docs job to ci.yaml**

Add this job alongside the existing `tests` and `lint` jobs:

```yaml
  docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install nox
      - run: nox -s docs
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yaml
git commit -m "ci: add docs build job (serves as e2e integration test)"
```

---

## Verification checklist

After all tasks:

- [ ] `nox -s docs` exits 0
- [ ] `docs/_build/html/index.html` exists
- [ ] `docs/_build/html/coverage.html` contains "sphinx-coverage-report coverage"
- [ ] `docs/_build/html/coverage.html` contains at least one module filename (e.g. `coverage_report.py`)
- [ ] `docs/_coverage/` is not tracked by git (`git status` shows nothing in that path)
