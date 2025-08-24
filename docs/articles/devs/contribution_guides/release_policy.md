# Release Policy

This document records the project's release and dependency practices and, importantly, documents the implemented automated versioning flow used by CI and helper scripts.

This article is about:

- The repository's automated versioning helpers and where they live (`versioning/`)
- How version information is stored (`VERSION.meta`, `VERSION`) and when to update it
- The GitHub Actions that run the automation and create tags/releases
- Practical contributor guidance for interacting with the automation

## Overview

This file documents the real, implemented behavior for release/version automation, tag/release creation, and tag cleanup — not policies that are hypothetical. See the "Automated versioning" section for exact scripts, branch rules, and local commands.

## Release Management

### Versioning Strategy

Hatch follows semantic versioning (SemVer) for public releases. The project additionally uses a structured, automated versioning helper that maintains both a human-readable, componentized file and a setuptools-compatible simple file. Key points:

- **MAJOR** version: Incompatible API changes
- **MINOR** version: Backwards-compatible functionality additions
- **PATCH** version: Backwards-compatible bug fixes

Automation rules (implemented in the repository) determine how prerelease/dev/build components are generated based on branch naming and actions (see "Automated versioning" below).

### Version Files

Each project maintains version information in two companion files (the repository uses a dual-file system used by the versioning helpers and CI):

- `VERSION.meta` - Structured, human-readable key=value format that stores component fields (MAJOR, MINOR, PATCH, DEV_NUMBER, BUILD_NUMBER, BRANCH). Used as the canonical source for automated updates and CI.
- `VERSION` - Simple, setuptools-compatible version string derived from `VERSION.meta` (for building and packaging). This file is regenerated from `VERSION.meta` before builds.
- `pyproject.toml` - Package configuration with version specification

Example from `Hatch/pyproject.toml`:

```toml
[project]
name = "hatch"
version = "0.4.2"
description = "Package manager for Model Context Protocol servers"
dependencies = [
    "hatch-validator>=0.1.0",
    "requests>=2.28.0",
]
```

### Release Process

The release process is mostly automated via repository scripts and GitHub Actions. High-level steps:

1. Version management and bumping are driven by branch names and CI (see "Automated versioning").
2. CI runs tests and prepares a build artifact using the version resolved by the automation.
3. If CI succeeds, a job commits updated `VERSION`/`VERSION.meta` and creates a git tag with the resolved version string.
4. Pushed tags trigger the release workflow which creates a GitHub Release (pre-release for dev versions).
5. Optionally, scheduled/manual tag cleanup removes old dev/build tags.

You generally should not edit `VERSION` or `VERSION.meta` by hand unless you have a specific reason — use the provided helper scripts or let CI manage version updates.

See "How the automation works" for the exact flow and commands to run locally.

## Automated versioning (scripts + workflows)

The repository provides a small set of scripts and GitHub Actions that implement the automated bumping, tagging, and release flow. The important files are:

- `versioning/version_manager.py` — core helper that reads/writes `VERSION.meta`, computes semantic version strings, and exposes commands:
  - `--get` prints the current version string
  - `--increment {major,minor,patch,dev,build}` increments a component and updates both files
  - `--update-for-branch BRANCH` updates version fields according to the branch name and writes both `VERSION.meta` and `VERSION`
  - `--simple` / helpers to write the simple `VERSION` file from the structured meta

- `versioning/prepare_version.py` — small helper run before build that converts `VERSION.meta` into the simple `VERSION` file for setuptools compatibility (preserves `VERSION.meta`).

- `versioning/tag_cleanup.py` — CI/manual helper to find and delete old `+build` and `.dev` tags according to configured age thresholds (dry-run mode by default).

Workflows involved:

- `.github/workflows/test_build.yml` — callable workflow used to:
  - Run tests/builds
  - Execute `python versioning/version_manager.py --update-for-branch <branch>` to compute and write the new version (branch is passed from the calling workflow)
  - Emit the computed version as a workflow output
  - Run `python versioning/prepare_version.py` and build the package
  - Upload `VERSION` and `VERSION.meta` as artifacts for downstream jobs

- `.github/workflows/commit_version_tag.yml` — triggered on pushes to branches like `dev`, `main`, `feat/*`, `fix/*`. It:
  - Calls/depends on the `test_build` workflow
  - Downloads the `VERSION` files artifact
  - Commits any changes to `VERSION`/`VERSION.meta` made by CI
  - Creates and pushes a lightweight git tag named after the computed version (for example `v1.2.3` or `v1.2.3.dev4+build5`)

- `.github/workflows/tag-release.yml` — fires on pushed tags matching the project's tag patterns and:
  - Creates a GitHub Release for the tag
  - Marks tags containing `.dev` as pre-releases

- `.github/workflows/tag-cleanup.yml` — manual / (future: scheduled) workflow that runs `versioning/tag_cleanup.py` to remove old dev/build tags.

Tagging conventions used by the automation:

- Tags are created from the computed version string returned by `version_manager` and pushed by `commit_version_tag.yml`.
- Examples: `v1.2.3`, `v1.2.3.dev0`, `v1.2.3.dev0+build1`.
- Tags that include `.dev` are treated as pre-releases in the release workflow.

## Branch-driven bump rules (summary)

The `version_manager` logic implements these broad rules (read `versioning/version_manager.py` for full details):

- `main` — clean release: no dev/build metadata; `DEV_NUMBER` and `BUILD_NUMBER` cleared.
- `dev` — prerelease/dev versions (increments dev number).
- `feat/*` (new feature branch) — creates/advances a minor/dev sequence; new feature branches may reset dev/build counters and start from e.g. `0`.
- `fix/*` — patch-level changes; build numbers are used to distinguish iterative work on the same fix branch.
- Other branches — treated as dev/prerelease in most cases.

The manager writes `VERSION.meta` with component fields and `VERSION` with the setuptools-compatible string (derived from `VERSION.meta`).

## How to run and test locally

Quick commands you can run from the repository root (PowerShell examples):

```powershell
# Print current computed version
python versioning/version_manager.py --get

# Update version for a given branch (this writes both files)
python versioning/version_manager.py --update-for-branch dev

# Increment a patch locally (writes both files)
python versioning/version_manager.py --increment patch --branch dev

# Prepare simple VERSION file for a build (convert from VERSION.meta)
python versioning/prepare_version.py
```

Notes:

- After running local updates, commit the updated `VERSION` and `VERSION.meta` if you intend to push the change.
- Prefer letting CI run `--update-for-branch` and perform the commit/tag steps automatically unless you need to perform an explicit offline bump.

## Tag cleanup and maintenance

Old `+build` and `.dev` tags are considered ephemeral. The `versioning/tag_cleanup.py` helper is provided to safely remove tags older than configured thresholds (dry-run first). The repository includes a manual GitHub Action (`tag-cleanup.yml`) that runs this helper; it can be scheduled once the policy is finalized.

## Local bump contract (inputs/outputs)

- Input: `VERSION.meta` (canonical), current git branch
- Output: updated `VERSION.meta`, `VERSION` (simple string), and on CI a git tag pushed to origin with the resolved version string
- Error modes: git unavailable, malformed `VERSION.meta` or permissions to push in CI

## Guidance for contributors

- Do not hand-edit `VERSION` except for emergency/manual bumps. Prefer using the helper (`version_manager.py`) or relying on CI automation.
- If you need a local pre-release for testing, use a branch name that follows the conventions (e.g., `feat/…`, `fix/…`, or `dev`) and call `--update-for-branch` locally.
- The GitHub Actions require repository write permissions for commits and tags; the `commit_version_tag` job sets `contents: write` to allow committing and pushing version files and tags.

## Summary mapping to requirements

- Automated versioning scripts: documented (`versioning/version_manager.py`, `versioning/prepare_version.py`, `versioning/tag_cleanup.py`) — Done
- GitHub Actions that run the automation and create tags/releases: documented (`.github/workflows/test_build.yml`, `.github/workflows/commit_version_tag.yml`, `.github/workflows/tag-release.yml`, `.github/workflows/tag-cleanup.yml`) — Done
