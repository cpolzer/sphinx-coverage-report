# Auto-Tagging and Version Bumping Design

**Date:** 2026-03-29
**Status:** Approved

## Problem

The `docs.yaml` workflow has a `docs-release` job triggered by `v*` tags, but no pipeline creates those tags. Version bumping and tagging are entirely manual, so releases never happen automatically.

## Goal

On every merge to `main`, automatically:
1. Detect releasable conventional commits since the last tag
2. Bump `version` in `pyproject.toml`
3. Commit the bump and push a `v*` tag
4. The existing `docs-release` job picks up the tag and deploys versioned docs

No PyPI publishing yet — that is a future step.

## Approach

Use **commitizen** (`cz bump`) driven by conventional commits. It reads commit history since the last tag, determines the appropriate semver bump, updates `pyproject.toml`, commits, and tags.

## Components

### 1. Commitizen config (`pyproject.toml`)

Add `[tool.commitizen]`:

```toml
[tool.commitizen]
version_provider = "pep621"
tag_format = "v$version"
bump_message = "chore: bump version $current_version → $new_version"
```

- `version_provider = "pep621"` reads/writes `[project] version` directly
- `tag_format = "v$version"` matches the existing `v*` trigger in `docs.yaml`

### 2. Release job in `ci.yaml`

A new `release` job, gated to pushes to `main` only, that runs after `tests` and `lint` pass:

- `fetch-depth: 0` checkout (commitizen needs full history to find the previous tag)
- Install `commitizen`
- Configure `git` identity as `github-actions[bot]`
- Run `cz bump --yes` — exits with code 21 (no-op) if no releasable commits; otherwise bumps, commits, and tags
- `git push --follow-tags` to push the bump commit + tag back to `main`

The new `v*` tag then triggers `docs-release` in `docs.yaml` as before.

### 3. Branch protection bypass

The `github-actions[bot]` needs permission to push directly to `main`.

**Manual step:** Repo Settings → Branches → edit the `main` protection rule → add `github-actions[bot]` to "Allow specified actors to bypass required pull requests".

### 4. Bootstrap tag

No `v*` tag exists yet, so commitizen has no baseline. Before the first automated run:

```bash
git tag v0.1.0
git push origin v0.1.0
```

### 5. Pre-commit hook for conventional commits

Add `.pre-commit-config.yaml` with the `commitizen-branch` hook so every local `git commit` is validated against the conventional commit format before it lands.

Add `commitizen` and `pre-commit` to dev dependencies in `pyproject.toml`.

Optionally add a `pre-commit run --hook-stage commit-msg` step to CI so contributor PRs are also checked.

## Data Flow

```
git commit (conventional) → pre-commit hook validates message
                          ↓
merge to main → CI: tests + lint pass
                          ↓
              release job: cz bump --yes
                          ↓
        no releasable commits? → exit 21, no-op
                          ↓
        bumps pyproject.toml, commits, tags v*
                          ↓
        git push --follow-tags
                          ↓
        docs.yaml docs-release job fires → versioned docs deployed
```

## Error Handling

- `cz bump` exit code 21 = no releasable commits since last tag → treat as success (no push needed)
- If push fails due to branch protection misconfiguration → workflow fails visibly with a clear error
- Malformed commit messages → pre-commit hook rejects locally; CI hook catches anything that slips through

## Out of Scope

- PyPI publishing (future work)
- Changelog generation (can be enabled later via `update_changelog_on_bump = true`)
- Release notes / GitHub Releases (future work)
