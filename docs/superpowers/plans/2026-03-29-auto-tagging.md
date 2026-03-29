# Auto-Tagging and Version Bumping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically bump `pyproject.toml` version, commit, and push a `v*` tag on every merge to `main` that contains releasable conventional commits.

**Architecture:** Commitizen (`cz bump`) reads conventional commits since the last tag, determines the semver bump, updates `pyproject.toml`, commits, and tags. A `release` job in `ci.yaml` runs after `tests` and `lint` pass on `main`. A `.pre-commit-config.yaml` enforces conventional commit format locally and in CI PRs.

**Tech Stack:** commitizen ≥3.0, pre-commit ≥3.0, GitHub Actions, flit/PEP 621 (`pyproject.toml`)

---

### Task 1: Add commitizen config and dev dependencies to `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add `[tool.commitizen]` section**

Append to `pyproject.toml`:

```toml
[tool.commitizen]
version_provider = "pep621"
tag_format = "v$version"
bump_message = "chore: bump version $current_version → $new_version"
```

- `version_provider = "pep621"` tells commitizen to read/write `[project] version`
- `tag_format = "v$version"` matches the `tags: "v*"` trigger already in `docs.yaml`
- `bump_message` sets the commit message for the automated bump commit

**Step 2: Add dev optional-dependencies group**

In the `[project.optional-dependencies]` section, add after the existing `docs` group:

```toml
dev = [
    "commitizen>=3.0",
    "pre-commit>=3.0",
]
```

**Step 3: Verify commitizen can read the version**

```bash
pip install "commitizen>=3.0"
cz version --project
```

Expected output: `0.1.0`

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add commitizen config and dev dependencies"
```

---

### Task 2: Create `.pre-commit-config.yaml` with conventional commit hook

**Files:**
- Create: `.pre-commit-config.yaml`

**Step 1: Check latest commitizen release tag**

```bash
pip index versions commitizen 2>/dev/null | head -1
# or visit https://github.com/commitizen-tools/commitizen/releases
```

Note the latest version (e.g. `v4.4.1`). Use it as `rev` below.

**Step 2: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.4.1  # replace with latest from step 1
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

The `commit-msg` stage means this hook fires on `git commit`, not `git add`. It validates the commit message against the conventional commit format configured in `[tool.commitizen]`.

**Step 3: Install the hooks**

```bash
pip install pre-commit
pre-commit install --hook-type commit-msg
```

Expected output:
```
pre-commit installed at .git/hooks/commit-msg
```

**Step 4: Test with a bad commit message**

```bash
echo "bad message" > /tmp/bad-msg.txt
pre-commit run commitizen --hook-stage commit-msg --commit-msg-filename /tmp/bad-msg.txt
```

Expected: FAILED with message about conventional commit format.

**Step 5: Test with a good commit message**

```bash
echo "feat: add something" > /tmp/good-msg.txt
pre-commit run commitizen --hook-stage commit-msg --commit-msg-filename /tmp/good-msg.txt
```

Expected: Passed.

**Step 6: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit hook for conventional commits"
```

---

### Task 3: Add commit-message check job to `ci.yaml` for PRs

**Files:**
- Modify: `.github/workflows/ci.yaml`

This job runs on PRs only and validates that every commit in the PR follows conventional commit format, catching contributors who haven't installed pre-commit locally.

**Step 1: Add `commit-check` job to `ci.yaml`**

After the `lint` job, add:

```yaml
  commit-check:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install "commitizen>=3.0"

      - name: Check commit messages
        run: cz check --rev-range origin/${{ github.base_ref }}..HEAD
```

`fetch-depth: 0` is required so `cz check` can walk the full commit range back to the merge base.

**Step 2: Validate the YAML is well-formed**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yaml'))" && echo "OK"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add .github/workflows/ci.yaml
git commit -m "ci: add conventional commit check for pull requests"
```

---

### Task 4: Add `release` job to `ci.yaml`

**Files:**
- Modify: `.github/workflows/ci.yaml`

**Step 1: Add `release` job**

After the `commit-check` job, add:

```yaml
  release:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: [tests, lint]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install commitizen
        run: pip install "commitizen>=3.0"

      - name: Configure git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Bump version
        id: cz
        run: |
          set +e
          cz bump --yes
          EXIT_CODE=$?
          set -e
          if [ $EXIT_CODE -eq 21 ]; then
            echo "No releasable commits since last tag, skipping release."
            echo "bumped=false" >> $GITHUB_OUTPUT
          elif [ $EXIT_CODE -eq 0 ]; then
            echo "bumped=true" >> $GITHUB_OUTPUT
          else
            exit $EXIT_CODE
          fi

      - name: Push bump commit and tag
        if: steps.cz.outputs.bumped == 'true'
        run: git push --follow-tags
```

Key points:
- `needs: [tests, lint]` — release only runs after CI passes
- `if: github.ref == 'refs/heads/main' && github.event_name == 'push'` — never runs on PRs
- `fetch-depth: 0` — commitizen needs full history to find the previous tag
- Exit code 21 = no releasable commits = normal, not an error
- `git push --follow-tags` pushes both the bump commit and the new `v*` tag
- The `v*` tag triggers `docs-release` in `docs.yaml` automatically

**Step 2: Validate the YAML**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yaml'))" && echo "OK"
```

Expected: `OK`

**Step 3: Commit**

```bash
git add .github/workflows/ci.yaml
git commit -m "ci: add automated release job using commitizen"
```

---

### Task 5: Manual setup steps (human required)

These cannot be automated — they require GitHub UI or admin access.

**Step 1: Configure branch protection bypass**

In the GitHub repository:
1. Go to **Settings → Branches**
2. Click **Edit** on the `main` protection rule
3. Under "Allow specified actors to bypass required pull requests", add `github-actions[bot]`
4. Save

Without this, the `git push --follow-tags` in the release job will be rejected.

**Step 2: Bootstrap the initial `v0.1.0` tag**

Commitizen needs an existing `v*` tag as a baseline. Since none exists yet:

```bash
git tag v0.1.0
git push origin v0.1.0
```

This push will also trigger `docs-release` in `docs.yaml` for the first time, deploying versioned docs for `0.1.0`. Verify the Actions run completes successfully.

**Step 3: Verify end-to-end**

Make a commit with a conventional message:

```bash
git commit --allow-empty -m "fix: trigger test release"
git push origin main
```

Watch the Actions tab — the `release` job should:
1. Run `cz bump --yes` → bumps to `0.1.1`
2. Push a bump commit + `v0.1.1` tag
3. Trigger `docs-release` for `v0.1.1`
