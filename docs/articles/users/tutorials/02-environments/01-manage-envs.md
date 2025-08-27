# 01: Manage Environments

---
**Concepts covered:**

- Environment lifecycle management
- Environment switching and current environment tracking
- Environment metadata and descriptions

**Skills you will practice:**

- Listing and inspecting environments
- Switching between environments
- Removing environments when no longer needed

---

## Understanding Hatch Environments

Hatch environments provide isolated workspaces for different MCP server collections. Each environment can have:

- Its own package installations
- Optional Python environment (via conda/mamba)
- Independent configuration and state

**Limitation Note**: Multiple `hatch` instances modifying environments simultaneously may cause conflicts. Use one instance per workspace for reliability.

## Step 1: List All Environments

View all available environments with their details:

```bash
hatch env list
```

Example output:

```txt
Available environments:
* my_python_env - Environment with Python support
    Python: 3.11.9 (conda: my_python_env)
  my_first_env - My first Hatch environment
    Python: 3.13.5 (conda: my_first_env)

Python Environment Manager:
  Conda executable: /usr/local/bin/conda
  Mamba executable: /usr/local/bin/mamba
  Preferred manager: mamba
```

The `*` indicates the current active environment.

## Step 2: Switch Between Environments

Change your current working environment:

```bash
hatch env use my_first_env
```

Verify the switch:

```bash
hatch env current
```

This command shows:

```
Current environment: my_first_env
```

## Step 3: Remove Environments

Remove an environment you no longer need:

```bash
hatch env remove my_first_env
```

**Important:** This removes both the Hatch environment and any associated Python environment. Make sure to back up any important data first.

## Step 4: Understanding Environment Information

The `env list` command provides detailed information:

- **Environment name and description** - Basic identification
- **Current environment marker (*)** - Shows which environment is active
- **Python environment status** - Shows Python version and conda environment name
- **Python Environment Manager status** - Shows available conda/mamba executables

If conda/mamba is not available, you'll see:

```
Python Environment Manager: Conda/mamba not available
```

## Step 5: Managing Multiple Environments

You can maintain multiple environments for different projects:

```bash
# Project-specific environments
hatch env create project_a --description "Environment for Project A" --python-version 3.11
hatch env create project_b --description "Environment for Project B" --python-version 3.12

# Switch between them as needed
hatch env use project_a
# Work on project A...

hatch env use project_b  
# Work on project B...
```

**Exercise:**
Create three environments with different Python versions, switch between them, and observe how the current environment changes. Then remove one of the environments.

<details>
<summary>Solution</summary>

```bash
# Create environments
hatch env create env_311 --python-version 3.11 --description "Python 3.11 environment"
hatch env create env_312 --python-version 3.12 --description "Python 3.12 environment" 
hatch env create env_313 --python-version 3.13 --description "Python 3.13 environment"

# Switch between them
hatch env use env_311
hatch env current  # Should show env_311

hatch env use env_312
hatch env current  # Should show env_312

# List to see all three
hatch env list

# Remove one
hatch env remove env_313
```

</details>

> Previous: [Getting Started Checkpoint](../01-getting-started/04-checkpoint.md)  
> Next: [Python Environment Management](02-python-env.md)
