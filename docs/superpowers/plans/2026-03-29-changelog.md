# Changelog Auto-Generation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Auto-generate `CHANGELOG.md` from conventional commits on every release and include it in the Sphinx docs via `myst-parser`.

**Architecture:** `cz bump --changelog` generates `CHANGELOG.md` and bumps the version in one step. The file is committed with the bump commit. Sphinx includes it via a `docs/changelog.md` wrapper using myst-parser's `{include}` directive.

**Tech Stack:** commitizen ≥3.0 (already installed), myst-parser ≥2.0, furo, Sphinx

---

### Task 1: Add myst-parser to docs dependencies and conf.py

**Files:**
- Modify: `pyproject.toml`
- Modify: `docs/conf.py`

**Step 1: Add myst-parser to docs optional-dependencies**

In `pyproject.toml`, update the `docs` group:

```toml
docs = [
    "sphinx",
    "furo",
    "sphinx-needs>=6.0.0",
    "myst-parser>=2.0",
]
```

**Step 2: Add myst_parser to Sphinx extensions**

In `docs/conf.py`, update the `extensions` list:

```python
extensions = [
    "sphinx_needs",
    "sphinxcontrib.coverage_report",
    "myst_parser",
]
```

**Step 3: Verify myst-parser installs cleanly**

```bash
pip install "myst-parser>=2.0"
python -c "import myst_parser; print('ok')"
```

Expected: `ok`

**Step 4: Commit**

```bash
git add pyproject.toml docs/conf.py
git commit -m "feat: add myst-parser for markdown support in docs"
```

---

### Task 2: Replace changelog.rst with changelog.md

**Files:**
- Delete: `docs/changelog.rst`
- Create: `docs/changelog.md`

**Step 1: Delete the existing changelog.rst**

```bash
git rm docs/changelog.rst
```

**Step 2: Create docs/changelog.md**

```markdown
# Changelog

\`\`\`{include} ../CHANGELOG.md
:relative-docs: true
:relative-images: true
\`\`\`
```

Note: the `toctree` entry in `docs/index.rst` already references `changelog` (no extension) — Sphinx with myst-parser will resolve `changelog.md` automatically. No change to `index.rst` needed.

**Step 3: Generate an initial CHANGELOG.md locally to test**

```bash
cz changelog
```

Expected: `CHANGELOG.md` created in repo root with entries for all tags since `v0.8.0`.

**Step 4: Build the docs locally and verify the changelog page renders**

```bash
pip install nox
DOCS_VERSION="local" nox -s docs
open docs/_build/html/changelog.html  # or xdg-open on Linux
```

Expected: Changelog page renders with version sections from the generated markdown.

**Step 5: Commit**

```bash
git add docs/changelog.md CHANGELOG.md
git commit -m "feat: replace changelog.rst with myst-parser include of CHANGELOG.md"
```

---

### Task 3: Update release job to use cz bump --changelog

**Files:**
- Modify: `.github/workflows/ci.yaml`

**Step 1: Replace `cz bump --yes` with `cz bump --changelog`**

In the `Bump version` step of the `release` job, change:

```yaml
          cz bump --yes
```

to:

```yaml
          cz bump --changelog
```

`--changelog` implies `--yes` and additionally generates/updates `CHANGELOG.md` before committing.

**Step 2: Validate the YAML is well-formed**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yaml'))" && echo "OK"
```

Expected: `OK`

**Step 3: Test locally that cz bump --changelog works**

```bash
# Dry run to see what would happen (does not commit or tag)
cz bump --changelog --dry-run
```

Expected output includes the new version number and changelog diff.

**Step 4: Commit**

```bash
git add .github/workflows/ci.yaml
git commit -m "feat: generate CHANGELOG.md automatically on version bump"
```
