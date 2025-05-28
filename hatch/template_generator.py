"""
Template Generator for Hatch packages.

This module contains functions to generate template files for Hatch MCP server packages.
Each function generates a specific file for the package template.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger("hatch.template_generator")

def generate_init_py():
    """Generate the __init__.py file content for a template package.
    
    Returns:
        str: Content for __init__.py file.
    """
    return "# Hatch package initialization\n"

def generate_server_py(package_name: str):
    """Generate the server.py file content for a template package.
    
    Args:
        package_name (str): Name of the package.
        
    Returns:
        str: Content for server.py file.
    """
    return f"""import logging
from hatchling import HatchMCP

# Initialize MCP server with metadata
hatch_mcp = HatchMCP("{package_name}",
                origin_citation="Origin citation for {package_name}",
                mcp_citation="MCP citation for {package_name}")

# Example tool function
@hatch_mcp.server.tool()
def example_tool(param: str) -> str:
    \"\"\"Example tool function.
    
    Args:
        param: Example parameter
        
    Returns:
        str: Example result
    \"\"\"
    hatch_mcp.logger.info(f"Example tool called with param: {{param}}")
    return f"Processed: {{param}}"

if __name__ == "__main__":
    hatch_mcp.logger.info("Starting MCP server")
    hatch_mcp.server.run()
"""

def generate_metadata_json(package_name: str, description: str = ""):
    """Generate the metadata JSON content for a template package.
    
    Args:
        package_name (str): Name of the package.
        description (str, optional): Package description. Defaults to empty string.
        
    Returns:
        dict: Metadata dictionary.
    """
    return {
        "package_schema_version": "1.1.0",
        "name": package_name,
        "version": "0.1.0",
        "description": description or f"A Hatch package for {package_name}",
        "tags": [],
        "author": {
            "name": "Hatch User",
            "email": ""
        },
        "license": {
            "name": "MIT"
        },
        "entry_point": "server.py",
        "tools": [
            {
                "name": "example_tool",
                "description": "Example tool function"
            }
        ],
        "citations": {
            "origin": f"Origin citation for {package_name}",
            "mcp": f"MCP citation for {package_name}"
        }
    }

def generate_readme_md(package_name: str, description: str = ""):
    """Generate the README.md file content for a template package.
    
    Args:
        package_name (str): Name of the package.
        description (str, optional): Package description. Defaults to empty string.
        
    Returns:
        str: Content for README.md file.
    """
    return f"""# {package_name}

{description}

## Tools

- **example_tool**: Example tool function
"""

def create_package_template(target_dir: Path, package_name: str, description: str = "") -> Path:
    """Create a package template directory with all necessary files.
    
    This function orchestrates the generation of a complete package structure by:
    1. Creating the package directory
    2. Generating and writing the __init__.py file
    3. Generating and writing the server.py file with example tools
    4. Creating the hatch_metadata.json with package information
    5. Generating a README.md with basic documentation
    
    Args:
        target_dir (Path): Directory where the package should be created.
        package_name (str): Name of the package.
        description (str, optional): Package description. Defaults to empty string.
        
    Returns:
        Path: Path to the created package directory.
    """
    logger.info(f"Creating package template for {package_name} in {target_dir}")
    
    # Create package directory
    package_dir = target_dir / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py
    init_content = generate_init_py()
    with open(package_dir / "__init__.py", 'w') as f:
        f.write(init_content)
    
    # Create server.py
    server_content = generate_server_py(package_name)
    with open(package_dir / "server.py", 'w') as f:
        f.write(server_content)
    
    # Create metadata.json
    metadata = generate_metadata_json(package_name, description)
    with open(package_dir / "hatch_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Create README.md
    readme_content = generate_readme_md(package_name, description)
    with open(package_dir / "README.md", 'w') as f:
        f.write(readme_content)
    
    logger.info(f"Package template created successfully at {package_dir}")
    return package_dir
