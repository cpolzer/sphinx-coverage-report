# Docs Release Flow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a three-tier GitHub Actions docs deployment pipeline: per-PR previews, a rolling dev environment on every merge to `main`, and versioned + latest production on git tag.

**Architecture:** A single `.github/workflows/docs.yaml` with three conditional jobs sharing one `on:` block. Each job builds via the existing `nox -s docs` session (which runs tests + sphinx-build) and deploys to a different path on the `gh-pages` branch. `conf.py` reads `DOCS_VERSION` from the environment to show the version string in the rendered site.

**Tech Stack:** GitHub Actions, `rossjrw/pr-preview-action@v1` (PR previews), `JamesIves/github-pages-deploy-action@v4` (dev + prod), GitHub Pages (`gh-pages` branch).

---

## Task 1: Version injection in `conf.py`

**Files:**
- Modify: `docs/conf.py`

**Step 1: Replace the hardcoded `release` line**

In `docs/conf.py`, replace:
```python
release = "0.1.0"
```
with:
```python
version = release = os.environ.get("DOCS_VERSION", "local")
```

`os` is already imported. The `version` field is what Sphinx displays in the rendered site header (the `release` field is the full version string used in download links etc — setting both keeps them in sync).

**Step 2: Verify the change is valid Python**

```bash
python -c "import docs.conf" 2>/dev/null || python docs/conf.py
```

Or just do a quick smoke-check:
```bash
cd /path/to/repo && python -c "
import os, importlib.util
spec = importlib.util.spec_from_file_location('conf', 'docs/conf.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print(m.version, m.release)
"
```
Expected output: `local local`

**Step 3: Verify env override works**

```bash
DOCS_VERSION=pr-42 python -c "
import os; os.environ['DOCS_VERSION'] = 'pr-42'
import importlib.util
spec = importlib.util.spec_from_file_location('conf', 'docs/conf.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.version == 'pr-42', f'got {m.version}'
print('OK:', m.version)
"
```
Expected: `OK: pr-42`

**Step 4: Commit**

```bash
git add docs/conf.py
git commit -m "docs: read DOCS_VERSION from env for per-stage version display"
```

---

## Task 2: Create `.github/workflows/docs.yaml`

**Files:**
- Create: `.github/workflows/docs.yaml`

This single file covers all three deployment stages using conditional jobs.

**Step 1: Create the workflow file**

```yaml
name: Docs

on:
  pull_request:
    types: [opened, synchronize, reopened, closed]
  push:
    branches: [main]
    tags:
      - "v*"

jobs:
  # ── PR preview ────────────────────────────────────────────────────────────
  docs-preview:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build docs
        if: github.event.action != 'closed'
        run: pip install nox && nox -s docs
        env:
          DOCS_VERSION: pr-${{ github.event.pull_request.number }}

      - uses: rossjrw/pr-preview-action@v1
        with:
          source-dir: docs/_build/html
          preview-branch: gh-pages
          umbrella-dir: pr-preview

  # ── Dev (main) ────────────────────────────────────────────────────────────
  docs-dev:
    if: github.event_name == 'push' && github.ref_type == 'branch'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Set short SHA
        run: echo "SHORT_SHA=${GITHUB_SHA::7}" >> $GITHUB_ENV

      - name: Build docs
        run: pip install nox && nox -s docs
        env:
          DOCS_VERSION: dev+${{ env.SHORT_SHA }}

      - uses: JamesIves/github-pages-deploy-action@v4
        with:
          branch: gh-pages
          folder: docs/_build/html
          target-folder: dev
          clean: true

  # ── Release (tag) ─────────────────────────────────────────────────────────
  docs-release:
    if: github.event_name == 'push' && github.ref_type == 'tag'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Extract version from tag
        # strips leading 'v': v1.2.0 → 1.2.0
        run: echo "DOCS_VERSION=${GITHUB_REF_NAME#v}" >> $GITHUB_ENV

      - name: Build docs
        run: pip install nox && nox -s docs
        env:
          DOCS_VERSION: ${{ env.DOCS_VERSION }}

      - name: Deploy to root (latest)
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          branch: gh-pages
          folder: docs/_build/html
          clean: true
          clean-exclude: |
            pr-preview/
            dev/
            v*/

      - name: Deploy to versioned path
        uses: JamesIves/github-pages-deploy-action@v4
        with:
          branch: gh-pages
          folder: docs/_build/html
          target-folder: v${{ env.DOCS_VERSION }}
          clean: true
```

**Step 2: Validate the YAML is well-formed**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/docs.yaml'))" && echo OK
```
Expected: `OK`

**Step 3: Commit**

```bash
git add .github/workflows/docs.yaml
git commit -m "ci: add docs deployment workflow — PR preview, dev, versioned release"
```

---

## Task 3: Enable GitHub Pages (manual, one-time)

**No code changes.** This must be done by a repo admin in the GitHub UI.

Steps:
1. Go to the repo on GitHub → **Settings** → **Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: `gh-pages`, folder: `/ (root)`
4. Click **Save**

The `gh-pages` branch does not need to exist yet — `JamesIves/github-pages-deploy-action` creates it on first deploy.

After the first successful `docs-dev` or `docs-release` run, the site will be live at:
`https://<org>.github.io/sphinx-coverage-report/`

---

## Verification Checklist

After all tasks are done, verify the full flow by:

1. **PR preview** — open a PR, check that:
   - The `docs-preview` job passes
   - A comment appears on the PR with the preview URL
   - The rendered site shows `pr-<N>` as the version

2. **Dev deploy** — merge a PR to `main`, check that:
   - The `docs-dev` job passes
   - `…/sphinx-coverage-report/dev/` is reachable
   - The rendered site shows `dev+<sha>` as the version

3. **Release deploy** — push a tag (`git tag v0.1.0 && git push --tags`), check that:
   - The `docs-release` job passes
   - `…/sphinx-coverage-report/` (root) shows `0.1.0`
   - `…/sphinx-coverage-report/v0.1.0/` also shows `0.1.0`
   - The `dev/` and `pr-preview/` subdirs are still intact (not wiped)
