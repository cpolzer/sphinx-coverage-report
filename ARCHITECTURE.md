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
