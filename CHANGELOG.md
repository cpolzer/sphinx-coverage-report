## v0.9.0 (2026-03-29)

### Feat

- generate CHANGELOG.md automatically on version bump
- replace changelog.rst with myst-parser include of CHANGELOG.md
- add myst-parser for markdown support in docs

### Fix

- **dics**: fix docs build by excluding our specs and plans
- add --yes to cz bump to prevent interactive prompt edge case

## v0.8.3 (2026-03-29)

### Fix

- **ci**: skip CI and docs-dev on bump commits, handle exit code 3

## v0.8.2 (2026-03-29)

### Fix

- **ci**: again testing tag bump triggering gh pages deploy

## v0.8.1 (2026-03-29)

### Fix

- **ci**: testing autom tagging

## v0.8.0 (2026-03-29)

### Feat

- cr_link() dynamic function for cross-linking to test-case nodes
- coverage-module, coverage-package, coverage-function, coverage-report directives
- coverage-results standalone table directive
- extension setup, config values, sphinx-needs shim
- JsonParser — parse coverage.py JSON to normalized dicts
- LcovParser — parse lcov.info to normalized dicts
- CoberturaParser — parse coverage.xml to normalized dicts

### Fix

- use annotated tags so git push --follow-tags works
- add [skip ci] to bump commit message to prevent loop
- ensure .nojekyll on gh-pages to prevent Jekyll stripping _static/
- split combined imports in test fixture conf.py files (ruff E401)
- move pytest-cov to test extras, not docs
- log CSS registration errors at DEBUG, document add_field name-as-description
- JsonParser — use true line_rate for functions (covered/statements)
- LcovParser — add docstrings, wrap parse errors, strengthen tests
- CoberturaParser — wrap malformed XML error, strengthen package tests, add docstrings

### Refactor

- use SphinxDirective base, cache on env, use self.config
