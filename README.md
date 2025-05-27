# Hatch

Hatch is the official package manager for the Hatch! ecosystem. It provides powerful tools for managing MCP server packages, environments, and interacting with the Hatch registry. Its primary objective is to service **[Hatchling](https://github.com/CrackingShells/Hatchling)** (interactive CLI-based chat application integrating local Large Language Models with MCP for tool calling), but can of course be included in other projects.

## Project Update Summary

**May 27, 2025**: Version 0.2.1 release of the Hatch package manager ecosystem! 🎉

- **Integration with Hatchling** for MCP servers package management while chatting with LLMs
- **Environment isolation system** for managing different sets of MCP server packages
- **Registry integration** for discovering and installing packages
- **Package template generation** for creating new Hatch MCP server packages

## Features

- **Environment Management**: Create isolated environments for different sets of MCP servers
- **Package Installation**: Install packages from the registry or local directories
- **Dependency Resolution**: Automatically resolve and manage package dependencies
- **Template Generation**: Create new Hatch MCP server package templates with a single command
- **Package Validation**: Ensure packages conform to the Hatch schema standards

## Installation

```bash
# From source
git clone https://github.com/CrackingShells/Hatch.git
cd Hatch
pip install -e .
```

## Usage

Hatch provides both a command-line interface and a Python API for integration into other tools like Hatchling.

### Command Line Interface

The table below summarizes the available commands with their arguments:

| Command | Description | Arguments | Example |
|---------|-------------|----------|---------|
| `create` | Create a new package template | `name` - Package name<br>`--dir, -d` - Target directory<br>`--description, -D` - Package description | `hatch create my-package --description "My awesome MCP server package"` |
| `validate` | Validate a package against schema | `package_dir` - Path to package directory | `hatch validate ./my-package` |
| `env list` | List all available environments | None | `hatch env list` |
| `env create` | Create a new environment | `name` - Environment name<br>`--description, -D` - Environment description | `hatch env create my-env --description "Environment for biology tools"` |
| `env use` | Set the current active environment | `name` - Environment name | `hatch env use my-env` |
| `env remove` | Remove an environment | `name` - Environment name | `hatch env remove my-env` |
| `env current` | Show the current environment | None | `hatch env current` |
| `package add` | Add a package to an environment | `package_path_or_name` - Path or name of package<br>`--env, -e` - Environment name<br>`--version, -v` - Package version | `hatch package add ./my-package --env my-env` <br> `hatch package add awesome-package --env my-env` |
| `package list` | List packages in an environment | `--env, -e` - Environment name | `hatch package list --env my-env` |
| `package remove` | Remove a package from an environment | `package_name` - Name of package to remove<br>`--env, -e` - Environment name | `hatch package remove awesome-package --env my-env` |

### Python API

```python
from hatch import HatchEnvironmentManager, create_package_template

# Create a new package template
create_package_template("my-package", target_dir="./packages", description="My awesome package")

# Manage environments
env_manager = HatchEnvironmentManager()
env_manager.create_environment("my-env", description="My testing environment")
env_manager.add_package("my-package", env_name="my-env")
packages = env_manager.list_packages("my-env")
```

## Creating Packages

Hatch makes it easy to create new MCP server packages:

```bash
hatch create my-package --description "My MCP server package"
```

This creates a template with the following structure:

```
my-package/
├── __init__.py
├── server.py
├── hatch_metadata.json
└── README.md
```

Edit the `server.py` file to define your MCP tools:

```python
import logging
from hatchling import HatchMCP

# Initialize MCP server with metadata
hatch_mcp = HatchMCP("my-package",
                 origin_citation="Your Name, 'Original Software', Year",
                 mcp_citation="Your Name, 'MCP Implementation', Year")

@hatch_mcp.tool()
def my_tool(param1: str, param2: int) -> str:
    """Description of what your tool does.
    
    Args:
        param1 (str): First parameter description.
        param2 (int): Second parameter description.
        
    Returns:
        str: Description of the return value.
    """
    hatch_mcp.logger.info(f"Tool called with {param1} and {param2}")
    return f"Processed {param1} with value {param2}"

if __name__ == "__main__":
    hatch_mcp.run()
```

## Dependencies

Hatch depends on the following Python packages:

- jsonschema 4.0.0 or higher
- requests 2.25.0 or higher
- packaging 20.0 or higher
- [Hatch-Validator](https://github.com/CrackingShells/Hatch-Validator)

## Development

### Project Structure

- `hatch/`: Core package source code
  - `cli_hatch.py`: CLI implementation
  - `environment_manager.py`: Environment management functionality
  - `package_loader.py`: Package loading and installation
  - `registry_retriever.py`: Registry interaction
  - `registry_explorer.py`: Package search and discovery
  - `template_generator.py`: Package template generation

## Related Repositories

Hatch is part of the larger Hatch! ecosystem which includes:

- **[Hatchling](https://github.com/CrackingShells/Hatchling)**: Interactive CLI-based chat application integrating local Large Language Models with MCP for tool calling
- **[Hatch-Schemas](https://github.com/CrackingShells/Hatch-Schemas)**: JSON schemas for package metadata and validation
- **[Hatch-Validator](https://github.com/CrackingShells/Hatch-Validator)**: Validation tools for Hatch packages
- **[Hatch-Registry](https://github.com/CrackingShells/Hatch-Registry)**: Package registry for Hatch packages

## License

This project is licensed under the [GNU Affero General Public License v3](./LICENSE)
