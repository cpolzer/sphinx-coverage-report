# sphinx-coverage-report — Feature Design

**Date:** 2026-03-23
**Status:** Approved

---

## Overview

`sphinx-coverage-report` is a Sphinx extension that imports code coverage report files and renders them as structured documentation inside a Sphinx build. It mirrors the architecture of `sphinx-test-reports` and integrates with `sphinx-needs` to create filterable, linkable coverage nodes that participate in full requirements traceability chains.

---

## Goals

- Parse coverage reports in Cobertura XML, lcov, and JSON formats
- Expose coverage data at four levels: report, package, module, function/method
- Produce both standalone docutils tables (no sphinx-needs dependency) and sphinx-needs "need" nodes
- Compute pass/fail status against configurable thresholds
- Enable cross-linking from coverage nodes to `sphinx-test-reports` test-case nodes via a `cr_link()` dynamic function
- Support sphinx-needs >= 1.0.1 through 8.0.0+ with a compatibility shim
- Emit configurable Sphinx warnings (via `sphinx.logging`) when coverage data is missing

---

## Non-Goals

- Real-time or watch-mode coverage collection (this is a report renderer, not a runner)
- Generating `.coverage`, `coverage.xml`, or `lcov.info` files (user supplies these)
- Diff coverage or trend tracking across builds

---

## Package Structure

```
sphinxcontrib/coverage_report/
├── __init__.py                        # re-exports setup()
├── coverage_report.py                 # setup(), config values, event hooks, _register_field shim
├── coberturaparser.py                 # Parses coverage.xml (Cobertura) → normalized dicts
├── lcovparser.py                      # Parses lcov.info → normalized dicts
├── jsonparser.py                      # Parses coverage.json → normalized dicts
├── config.py                          # DEFAULT_OPTIONS, threshold defaults
├── environment.py                     # CSS static file injection (mirrors test_reports pattern)
├── exceptions.py                      # Custom exception types
├── directives/
│   ├── coverage_common.py             # Base directive class
│   ├── coverage_results.py            # Standalone table directive (no sphinx-needs dep)
│   ├── coverage_report_directive.py   # Template-expanded full report directive
│   ├── coverage_function.py           # Need node per function/method
│   ├── coverage_module.py             # Need node per source file
│   ├── coverage_package.py            # Need node per package/directory
│   └── coverage_report_template.txt   # Default RST report template
├── functions/
│   └── __init__.py                    # cr_link() dynamic function for sphinx-needs
└── schemas/
    └── cobertura.xsd                  # Optional XSD for Cobertura validation
```

---

## Supported Input Formats

| Format | Parser | Notes |
|--------|--------|-------|
| Cobertura XML (`coverage.xml`) | `CoberturaParser` | Primary format; lxml + optional XSD validation |
| lcov (`lcov.info`) | `LcovParser` | Pure Python; parses `DA:`, `FN:`, `FNDA:`, `BRDA:`, `BRF:`, `BRH:` records. `BRDA:` provides per-branch detail; `BRF:`/`BRH:` provide summary branch totals. |
| JSON (`coverage.json`) | `JsonParser` | Driven by `cr_json_mapping` config; same pattern as `tr_json_mapping` |

Function/method-level data is populated by JSON and lcov only — Cobertura does not carry it reliably.

---

## Normalized Data Model

All parsers produce the same shape so directives are format-agnostic. Results are cached in `app.coveragereport_data[filepath]`.

```python
# Report (top level)
{
    "line_rate": float,
    "branch_rate": float,
    "lines_valid": int,
    "lines_covered": int,
    "branches_valid": int,
    "branches_covered": int,
    "timestamp": str,
    "version": str,
    "packages": [<package>, ...]
}

# Package
{
    "name": str,
    "line_rate": float,
    "branch_rate": float,
    "lines_valid": int,
    "lines_covered": int,
    "branches_valid": int,
    "branches_covered": int,
    "modules": [<module>, ...]
}

# Module
{
    "name": str,               # e.g. "module.py"
    "filename": str,           # e.g. "mypackage/module.py"
    "line_rate": float,
    "branch_rate": float,
    "lines_valid": int,
    "lines_covered": int,
    "branches_valid": int,
    "branches_covered": int,
    "missed_lines": [int, ...],
    "complexity": float,
    "functions": [<function>, ...]
}

# Function/method
{
    "name": str,
    "line_start": int,
    "line_rate": float,
    "hits": int,
}
```

---

## Directives

| Directive | Needs dep? | Purpose |
|-----------|-----------|---------|
| `coverage-results` | No | Standalone docutils table — line/branch rates per module |
| `coverage-report` | Yes | Template-expanded full report with needtables |
| `coverage-package` | Yes | Need node for a package with aggregated stats |
| `coverage-module` | Yes | Need node per source file with rates, missed lines |
| `coverage-function` | Yes | Need node per function/method |

### Example RST usage

```rst
.. coverage-results:: path/to/coverage.xml

.. coverage-report:: path/to/coverage.xml
   :id: CR_001
   :tags: backend, sprint-42

.. coverage-module:: path/to/coverage.xml
   :package: mypackage
   :module: module.py
   :id: CM_001
   :links: TC_001, TC_002
   :tags: backend
```

### Common options (all need-based directives)

`:id:`, `:status:`, `:tags:`, `:links:`, `:file:`, `:package:`, `:module:`

### Auto-expansion

`coverage-report` and `coverage-package` accept an `:expand:` option that auto-generates child directives (packages → modules → functions), mirroring `test-file` behaviour in sphinx-test-reports.

---

## Threshold-Based Status

Status is computed at directive run time by comparing `line_rate` and `branch_rate` against configured thresholds. If either falls below the threshold, `status` is set to `"failing"`; otherwise `"passing"`. A manually supplied `:status:` option always wins.

---

## Configuration (`conf.py`)

```python
cr_rootdir = "."
cr_import_encoding = "utf-8"
cr_extra_options = []                   # user-defined passthrough fields; rebuild scope "env"

# Need type config: [directive-name, need-type, title-prefix, id-prefix, color, style]
cr_report   = ["coverage-report",   "coveragereport",   "Coverage Report",   "CR_", "#4a90d9", "node"]
cr_package  = ["coverage-package",  "coveragepackage",  "Coverage Package",  "CP_", "#7ab648", "folder"]
cr_module   = ["coverage-module",   "coveragemodule",   "Coverage Module",   "CM_", "#f0ad4e", "rectangle"]
cr_function = ["coverage-function", "coveragefunction", "Coverage Function", "CF_", "#cccccc", "rectangle"]

# Global thresholds (applied to all levels unless overridden)
cr_threshold_line_rate   = 0.80
cr_threshold_branch_rate = 0.75

# Per-level threshold overrides (optional)
cr_threshold_report  = {"line_rate": 0.80}
cr_threshold_package = {"line_rate": 0.85}
cr_threshold_module  = {"line_rate": 0.90, "branch_rate": 0.80}

# ID hash suffix lengths
cr_module_id_length   = 5
cr_package_id_length  = 3

# JSON format mapping (mirrors tr_json_mapping structure)
# Each field: (key_path_list, default_value)
cr_json_mapping = {
    "json_config": {
        "report": {
            "line_rate":        (["line_rate"],        "0"),
            "branch_rate":      (["branch_rate"],      "0"),
            "lines_valid":      (["summary", "num_statements"], "0"),
            "lines_covered":    (["summary", "covered_lines"],  "0"),
            "branches_valid":   (["summary", "num_branches"],   "0"),
            "branches_covered": (["summary", "covered_branches"], "0"),
            "timestamp":        (["meta", "timestamp"], "unknown"),
            "version":          (["meta", "version"],   "unknown"),
        },
        "package": {
            "name":             (["name"], "unknown"),
            "line_rate":        (["line_rate"], "0"),
            "branch_rate":      (["branch_rate"], "0"),
        },
        "module": {
            "name":             (["name"], "unknown"),
            "filename":         (["filename"], "unknown"),
            "line_rate":        (["summary", "percent_covered_display"], "0"),
            "branch_rate":      (["summary", "percent_branches_complete"], "0"),
            "lines_valid":      (["summary", "num_statements"], "0"),
            "lines_covered":    (["summary", "covered_lines"], "0"),
            "missing_lines":    (["missing_lines"], []),
        },
        "function": {
            "name":             (["name"], "unknown"),
            "line_start":       (["start_line"], 0),
            "hits":             (["executed"], 0),
        },
    }
}

# Custom RST report template path.
# Defaults to the bundled coverage_report_template.txt inside the package.
# Set to an absolute path to use a custom template.
cr_report_template = None  # None → bundled default

# Emit a Sphinx warning (via sphinx.logging) when a directive references a
# coverage file that contains no data for the requested package/module/function.
# Set to False to silence these warnings.
cr_warn_no_data = True
```

### User-defined extra options — version-aware pattern

```python
import sphinx_needs
from packaging.version import Version

if Version(sphinx_needs.__version__) >= Version("8.0.0"):
    needs_fields = {"my_field": {"nullable": True}}
else:
    needs_extra_options = ["my_field"]
cr_extra_options = ["my_field"]
```

---

## sphinx-needs Compatibility Shim

Two breaking changes are handled via an import-detection shim in `coverage_report.py`:

| sphinx-needs version | Change |
|---------------------|--------|
| < 8.0.0 | `add_extra_option(app, name)` — no schema support |
| >= 8.0.0 | `add_field(name, description, *, schema=...)` — `app` removed, `description` positional, schema required |
| >= 8.0.0 | `needs_extra_options` in `conf.py` deprecated → use `needs_fields` dict |

The shim uses `try/except ImportError` (not version-number comparison) to detect which API is present, matching the proven pattern in `sphinx-test-reports`:

```python
# _register_field shim in coverage_report.py
try:
    from sphinx_needs.api import add_field as _add_field
    # sphinx-needs >= 8.0.0: add_field(name, description, *, schema)
    def _register_field(app, name, schema=None):
        _add_field(name, name, schema=schema or {"type": "string"})
except ImportError:
    from sphinx_needs.api import add_extra_option as _add_extra_option
    # sphinx-needs < 8.0.0: add_extra_option(app, name[, schema=])
    def _register_field(app, name, schema=None):
        _add_extra_option(app, name, **({} if schema is None else {"schema": schema}))
```

`_register_field` is called unconditionally for all coverage fields — no version-number branch needed in `sphinx_needs_update()`:

```python
def sphinx_needs_update(app, config):
    _register_field(app, "line_rate",         schema={"type": "number"})
    _register_field(app, "branch_rate",       schema={"type": "number"})
    _register_field(app, "lines_valid",       schema={"type": "integer"})
    _register_field(app, "lines_covered",     schema={"type": "integer"})
    _register_field(app, "branches_valid",    schema={"type": "integer"})
    _register_field(app, "branches_covered",  schema={"type": "integer"})
    _register_field(app, "missed_lines",      schema={"type": "string"})
    _register_field(app, "filename",          schema={"type": "string"})
    _register_field(app, "package",           schema={"type": "string"})
    _register_field(app, "complexity",        schema={"type": "number"})
    _register_field(app, "hits",              schema={"type": "integer"})
    _register_field(app, "line_start",        schema={"type": "integer"})
    # ... extra options from cr_extra_options
```

The `schema=` kwarg is safely ignored by the `add_extra_option` fallback on older versions that don't support it.

---

## Cross-Linking with sphinx-test-reports

A `cr_link()` dynamic function is registered with sphinx-needs, enabling automatic linking from coverage module nodes to test-case nodes by matching filenames:

```python
# functions/__init__.py
def cr_link(app, need, needs, option, filter_string=None, **kwargs):
    """
    Returns IDs of test-case needs whose 'file' option matches
    this coverage module's 'filename' option.
    """
```

**RST usage:**

```rst
.. coverage-module:: coverage.xml
   :package: mypackage
   :module: module.py
   :links: [[cr_link('filename', 'file')]]
```

**Full traceability chain:**

```
Requirement (sphinx-needs)
    └── Test Case (sphinx-test-reports)
            └── Coverage Module (sphinx-coverage-report)
                    └── Coverage Function
```

---

## Missing Data Warnings

When a directive references a coverage file but the requested package, module, or function is not found in the parsed data, the extension emits a Sphinx warning using `sphinx.logging`:

```python
import sphinx.util.logging
logger = sphinx.util.logging.getLogger(__name__)

if data_missing and app.config.cr_warn_no_data:
    logger.warning(
        "sphinx-coverage-report: no coverage data found for '%s' in '%s'",
        identifier, filepath,
        location=self.get_location(),
    )
```

`cr_warn_no_data = True` (default) — set to `False` in `conf.py` to silence these warnings globally.

---

## Need Extra Options Registered

```
line_rate, branch_rate, lines_valid, lines_covered,
branches_valid, branches_covered, missed_lines,
filename, package, complexity, hits, line_start
```

---

## Dependencies

| Package | Reason |
|---------|--------|
| `sphinx > 4.0` | Extension framework |
| `sphinx-needs >= 1.0.1` | Need object creation and management |
| `lxml` | Cobertura XML parsing and XSD validation |
| `packaging` | Version comparison for sphinx-needs compatibility shim |

---

## Testing Strategy

- One parser test file per format: `test_cobertura_parser.py`, `test_lcov_parser.py`, `test_json_parser.py`
- Fixture files: `coverage.xml`, `lcov.info`, `coverage.json` under `tests/fixtures/`
- Sphinx doc-build tests for each directive (mirrors `test_basic_doc.py` pattern)
- Threshold status tests: assert `status == "failing"` below threshold, `"passing"` at or above
- Cross-link tests: assert `cr_link()` resolves correct test-case IDs
- nox matrix: Python 3.10–3.12 × sphinx-needs versions (pre-6.0, 6.x, 7.x, 8.x)
