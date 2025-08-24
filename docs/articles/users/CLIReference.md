# CLI Reference

This document is a compact reference of all Hatch CLI commands and options implemented in `hatch/cli_hatch.py` presented as tables for quick lookup.

## Table of Contents

- [Global options](#global-options)
- [Commands](#commands)
  - [hatch create](#hatch-create)
  - [hatch validate](#hatch-validate)
  - [hatch env](#hatch-env-environment-management)
    - [hatch env create](#hatch-env-create)
    - [hatch env remove](#hatch-env-remove)
    - [hatch env list](#hatch-env-list)
    - [hatch env use](#hatch-env-use)
    - [hatch env current](#hatch-env-current)
    - [hatch env python](#hatch-env-python-advanced-python-environment-subcommands)
      - [hatch env python init](#hatch-env-python-init)
      - [hatch env python info](#hatch-env-python-info)
      - [hatch env python remove](#hatch-env-python-remove)
      - [hatch env python shell](#hatch-env-python-shell)
  - [hatch package](#hatch-package-package-management)
    - [hatch package add](#hatch-package-add)
    - [hatch package remove](#hatch-package-remove)
    - [hatch package list](#hatch-package-list)

## Global options

These flags are accepted by the top-level parser and apply to all commands unless overridden.

| Flag | Type | Description | Default |
|------|------|-------------|---------|
| `--envs-dir` | path | Directory to store environments | `~/.hatch/envs` |
| `--cache-ttl` | int | Cache time-to-live in seconds | `86400` (1 day) |
| `--cache-dir` | path | Directory to store cached packages | `~/.hatch/cache` |

## Commands

Each top-level command has its own table. Use the Syntax line before the table to see how to call it.

### `hatch create`

Create a new package template.

Syntax:

`hatch create <name> [--dir DIR] [--description DESC]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `name` | string (positional) | Package name (required) | n/a |
| `--dir`, `-d` | path | Target directory for the template | current directory |
| `--description`, `-D` | string | Package description | empty string |

Examples:

`hatch create my_package`

`hatch create my_package --dir ./packages --description "My awesome package"`

---

### `hatch validate`

Validate a package structure and metadata.

Syntax:

`hatch validate <package_dir>`

| Argument | Type | Description |
|---:|---|---|
| `package_dir` | path (positional) | Path to package directory to validate (required) |

Examples:

`hatch validate ./my_package`

---

### `hatch env` (environment management)

Top-level syntax: `hatch env <create|remove|list|use|current|python> ...`

#### `hatch env create`

Create a new Hatch environment bootstrapping a Python/conda environment.

Syntax:

`hatch env create <name> [--description DESC] [--python-version VER] [--no-python] [--no-hatch-mcp-server] [--hatch_mcp_server_tag TAG]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `name` | string (positional) | Environment name (required) | n/a |
| `--description`, `-D` | string | Human-readable environment description | empty string |
| `--python-version` | string | Python version to create (e.g., `3.11`) | none (manager default) |
| `--no-python` | flag | Do not create a Python environment (skip conda/mamba) | false |
| `--no-hatch-mcp-server` | flag | Do not install `hatch_mcp_server` wrapper | false |
| `--hatch_mcp_server_tag` | string | Git tag/branch for wrapper install (e.g., `dev`, `v0.1.0`) | none |

#### `hatch env remove`

Syntax:

`hatch env remove <name>`

| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to remove (required) |

#### `hatch env list`

Syntax:

`hatch env list`

Description: Lists all environments. When a Python manager (conda/mamba) is available additional status and manager info are displayed.

#### `hatch env use`

Syntax:

`hatch env use <name>`

| Argument | Type | Description |
|---:|---|---|
| `name` | string (positional) | Environment name to set as current (required) |

#### `hatch env current`

Syntax:

`hatch env current`

Description: Print the name of the current environment.

---

### `hatch env python` (advanced Python environment subcommands)

Top-level syntax: `hatch env python <init|info|add-hatch-mcp|remove|shell> ...`

#### `hatch env python init`

Initialize or recreate a Python environment inside a Hatch environment.

Syntax:

`hatch env python init [--hatch_env NAME] [--python-version VER] [--force] [--no-hatch-mcp-server] [--hatch_mcp_server_tag TAG]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current env) | current environment |
| `--python-version` | string | Desired Python version (e.g., `3.12`) | none |
| `--force` | flag | Force recreation if it already exists | false |
| `--no-hatch-mcp-server` | flag | Skip installing `hatch_mcp_server` wrapper | false |
| `--hatch_mcp_server_tag` | string | Git tag/branch for wrapper installation | none |

#### `hatch env python info`

Show information about the Python environment for a Hatch environment.

Syntax:

`hatch env python info [--hatch_env NAME] [--detailed]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--detailed` | flag | Show additional diagnostics and package listing | false |

When available this command prints: status, python executable, python version, conda env name, environment path, creation time, package count and package list. With `--detailed` it also prints diagnostics from the manager.

#### `hatch env python add-hatch-mcp`

Install the `hatch_mcp_server` wrapper into the Python environment of a Hatch env.

Syntax:

`hatch env python add-hatch-mcp [--hatch_env NAME] [--tag TAG]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--tag` | string | Git tag/branch for wrapper install | none |

#### `hatch env python remove`

Remove the Python environment associated with a Hatch environment.

Syntax:

`hatch env python remove [--hatch_env NAME] [--force]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--force` | flag | Skip confirmation prompt and force removal | false |

#### `hatch env python shell`

Launch a Python REPL or run a single command inside the Python environment.

Syntax:

`hatch env python shell [--hatch_env NAME] [--cmd CMD]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--hatch_env` | string | Hatch environment name (defaults to current) | current environment |
| `--cmd` | string | Command to execute inside the Python shell (optional) | none |

---

### `hatch package` (package management)

Top-level syntax: `hatch package <add|remove|list> ...`

#### `hatch package add`

Add a package (local path or registry name) into an environment.

Syntax:

`hatch package add <package_path_or_name> [--env NAME] [--version VER] [--force-download] [--refresh-registry] [--auto-approve]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `package_path_or_name` | string (positional) | Path to package directory or registry package name (required) | n/a |
| `--env`, `-e` | string | Target Hatch environment name (defaults to current) | current environment |
| `--version`, `-v` | string | Version for registry packages | none |
| `--force-download`, `-f` | flag | Force fetching even if cached | false |
| `--refresh-registry`, `-r` | flag | Refresh registry metadata before resolving | false |
| `--auto-approve` | flag | Automatically approve dependency installation prompts | false |

Examples:

`hatch package add ./my_package`

`hatch package add registry_package --version 1.0.0 --env dev-env --auto-approve`

#### `hatch package remove`

Remove a package from a Hatch environment.

Syntax:

`hatch package remove <package_name> [--env NAME]`

| Argument / Flag | Type | Description | Default |
|---:|---|---|---|
| `package_name` | string (positional) | Name of the package to remove (required) | n/a |
| `--env`, `-e` | string | Hatch environment name (defaults to current) | current environment |

#### `hatch package list`

List packages installed in a Hatch environment.

Syntax:

`hatch package list [--env NAME]`

| Flag | Type | Description | Default |
|---:|---|---|---|
| `--env`, `-e` | string | Hatch environment name (defaults to current) | current environment |

Output: each package row includes name, version, hatch compliance flag, source URI and installation location.

---

## Exit codes

| Code | Meaning |
|---:|---|
| `0` | Success |
| `1` | Error or failure |

## Notes

- The implementation in `hatch/cli_hatch.py` does not provide a `--version` flag or a top-level `version` command. Use `hatch --help` to inspect available commands and options.
- This reference mirrors the command names and option names implemented in `hatch/cli_hatch.py`. If you change CLI arguments in code, update this file to keep documentation in sync.
