# Docs Release Flow — Design

**Date:** 2026-03-26
**Status:** Approved

---

## Overview

Implement a three-tier docs deployment pipeline using GitHub Actions and GitHub Pages:
- Per-PR preview environments
- A rolling `dev` environment on every merge to `main`
- Versioned + latest production deployments on git tag

---

## URL Structure

All docs are served from the `gh-pages` branch, which is the GitHub Pages source.

| Trigger | URL path | `gh-pages` path |
|---|---|---|
| PR open/update | `/pr-preview/pr-<N>/` | `pr-preview/pr-<N>/` |
| PR close/merge | (removed automatically) | — |
| Push to `main` | `/dev/` | `dev/` |
| Git tag `v*` | `/` (latest) | root |
| Git tag `v*` | `/v<tag>/` (versioned) | `v<tag>/` |

Example base URL: `https://<org>.github.io/sphinx-coverage-report/`

---

## Version Display

`conf.py` reads `DOCS_VERSION` from the environment for both `version` and `release`, falling back to `"local"` for local builds:

```python
version = release = os.environ.get("DOCS_VERSION", "local")
```

| Stage | `DOCS_VERSION` value | Example |
|---|---|---|
| PR preview | `pr-<N>` | `pr-42` |
| Dev | `dev+<short-sha>` | `dev+a1b2c3d` |
| Tag | tag without `v` prefix | `1.2.0` |
| Local | `local` (fallback) | `local` |

---

## Workflow Structure

New file: `.github/workflows/docs.yaml`

### Job: `docs-preview`

**Trigger:** `pull_request` (types: opened, synchronize, reopened, closed)

**Steps:**
1. Checkout
2. Build docs (skipped if PR is being closed) with `DOCS_VERSION=pr-<N>`
3. `rossjrw/pr-preview-action` — deploys to `pr-preview/pr-<N>/`, posts PR comment with preview URL, removes deployment on close

**Permissions:** `contents: write`, `pull-requests: write`

---

### Job: `docs-dev`

**Trigger:** `push` to `main`

**Steps:**
1. Checkout
2. Build docs with `DOCS_VERSION=dev+<short-sha>`
3. `JamesIves/github-pages-deploy-action` with `destination-dir: dev/`

**Permissions:** `contents: write`

---

### Job: `docs-release`

**Trigger:** `push` to tags matching `v*`

**Steps:**
1. Checkout
2. Build docs once with `DOCS_VERSION=<tag>` (strip leading `v`)
3. Two parallel deploy steps (both use `JamesIves/github-pages-deploy-action`):
   - **Latest:** deploy to root `/`, `clean-exclude: [pr-preview, dev, "v*"]`
   - **Versioned:** deploy to `v<tag>/` subdirectory

**Permissions:** `contents: write`

---

## Doc Build

All three jobs build docs the same way — via the existing `nox -s docs` session which:
1. Runs pytest and emits `docs/_coverage/coverage.xml`
2. Runs `sphinx-build docs docs/_build/html`

The `DOCS_VERSION` env var is available to `conf.py` throughout.

---

## One-Time Repo Setup

Manual step (not automated):
- Enable GitHub Pages in repo Settings → Pages → Source: `gh-pages` branch, root `/`
- The `gh-pages` branch is created automatically on first deploy

---

## Non-Goals

- Custom domain
- Redirects from old versioned paths
- Version switcher UI in the docs (e.g. dropdown to select version)
