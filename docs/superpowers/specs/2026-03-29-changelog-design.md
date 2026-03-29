---
name: Changelog Auto-Generation Design
description: Auto-generate CHANGELOG.md from conventional commits and include it in Sphinx docs
type: project
date: 2026-03-29
---

# Changelog Auto-Generation Design

## Goal

Auto-generate `CHANGELOG.md` from conventional commits on every release and include it in the Sphinx documentation site.

## Architecture

### Release job (`ci.yaml`)

Replace `cz bump --yes` with `cz bump --changelog` so commitizen generates/updates `CHANGELOG.md` and bumps `pyproject.toml` in a single step. Both files are committed together in the bump commit.

### Sphinx integration

- Add `myst-parser` to `[project.optional-dependencies] docs` in `pyproject.toml`
- Add `"myst_parser"` to `extensions` in `docs/conf.py`
- Remove `docs/changelog.rst`, replace with `docs/changelog.md`:

```markdown
# Changelog

\`\`\`{include} ../CHANGELOG.md
:relative-docs: true
:relative-images: true
\`\`\`
```

- `docs/index.rst` toctree entry `changelog` remains unchanged (Sphinx resolves both `.rst` and `.md`)

### Docs workflow (`docs.yaml`)

No changes needed. `CHANGELOG.md` is committed as part of the bump commit that the `v*` tag points to, so it is present at checkout time in `docs-release`. PR previews also pick it up from the branch.

## Dependencies

- `myst-parser>=2.0` added to `docs` optional-dependencies

## Files changed

| File | Change |
|---|---|
| `pyproject.toml` | Add `myst-parser` to `docs` deps; replace `cz bump --yes` flag |
| `.github/workflows/ci.yaml` | `cz bump --changelog` instead of `cz bump --yes` |
| `docs/conf.py` | Add `myst_parser` to extensions |
| `docs/changelog.rst` | Delete |
| `docs/changelog.md` | Create with `{include}` directive |
