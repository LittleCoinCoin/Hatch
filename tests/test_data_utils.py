"""Test data utilities for Hatch test suite.

This module provides utilities for loading test data and creating self-contained
test packages for the Hatch testing infrastructure.
"""

import json
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime


class TestDataLoader:
    """Utility class for loading test data from standardized locations."""
    
    def __init__(self):
        """Initialize the test data loader."""
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.configs_dir = self.test_data_dir / "configs"
        self.responses_dir = self.test_data_dir / "responses"
        self.packages_dir = self.test_data_dir / "packages"
        
        # Ensure directories exist
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """Load a test configuration file.
        
        Args:
            config_name: Name of the config file (without .json extension)
            
        Returns:
            Loaded configuration as a dictionary
        """
        config_path = self.configs_dir / f"{config_name}.json"
        if not config_path.exists():
            # Create default config if it doesn't exist
            self._create_default_config(config_name)
        
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def load_response(self, response_name: str) -> Dict[str, Any]:
        """Load a mock response file.
        
        Args:
            response_name: Name of the response file (without .json extension)
            
        Returns:
            Loaded response as a dictionary
        """
        response_path = self.responses_dir / f"{response_name}.json"
        if not response_path.exists():
            # Create default response if it doesn't exist
            self._create_default_response(response_name)
        
        with open(response_path, 'r') as f:
            return json.load(f)
    
    def get_test_packages_dir(self) -> Path:
        """Get the test packages directory path."""
        return self.packages_dir

    def setup(self):
        """Set up test data infrastructure."""
        # Ensure all test packages exist
        self._ensure_test_packages_exist()

    def cleanup(self):
        """Clean up test data (placeholder for future cleanup logic)."""
        # Currently no cleanup needed as test packages are persistent
        pass
    
    def create_test_package(self, package_name: str, dependencies: Dict[str, Any] = None, schema_version: str = "1.2.1") -> Path:
        """Create a test package with specified dependencies conforming to Hatch schemas.

        Args:
            package_name: Name of the package to create
            dependencies: Dictionary of dependencies (format depends on schema version)
            schema_version: Schema version to use (1.2.1, 1.2.0, or 1.1.0)

        Returns:
            Path to the created package directory
        """
        package_dir = self.packages_dir / package_name
        package_dir.mkdir(exist_ok=True)

        # Create metadata conforming to the specified schema version
        if schema_version == "1.2.1":
            metadata = self._create_v1_2_1_metadata(package_name, dependencies)
        elif schema_version == "1.2.0":
            metadata = self._create_v1_2_0_metadata(package_name, dependencies)
        else:  # Default to 1.1.0 for backward compatibility
            metadata = self._create_v1_1_0_metadata(package_name, dependencies)

        metadata_path = package_dir / "hatch_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        # Create entry point files based on schema version
        if schema_version == "1.2.1":
            self._create_dual_entry_points(package_dir, package_name)
        else:  # v1.2.0 and v1.1.0 use single entry point
            self._create_single_entry_point(package_dir, package_name)

        return package_dir

    def _create_v1_2_1_metadata(self, package_name: str, dependencies: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create metadata conforming to v1.2.1 schema."""
        metadata = {
            "package_schema_version": "1.2.1",
            "name": package_name,
            "version": "1.0.0",
            "description": f"Test package: {package_name}",
            "tags": ["test", "hatch", "mcp"],
            "author": {
                "name": "Test Suite",
                "email": "test@crackingshells.com"
            },
            "license": {
                "name": "MIT",
                "uri": "https://opensource.org/licenses/MIT"
            },
            "entry_point": {
                "mcp_server": "mcp_server.py",
                "hatch_mcp_server": "hatch_mcp_server.py"
            },
            "tools": [
                {
                    "name": f"{package_name}_tool",
                    "description": f"Example tool for {package_name}"
                }
            ]
        }

        if dependencies:
            metadata["dependencies"] = dependencies

        return metadata

    def _create_v1_2_0_metadata(self, package_name: str, dependencies: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create metadata conforming to v1.2.0 schema."""
        metadata = {
            "package_schema_version": "1.2.0",
            "name": package_name,
            "version": "1.0.0",
            "description": f"Test package: {package_name}",
            "tags": ["test", "hatch", "mcp"],
            "author": {
                "name": "Test Suite",
                "email": "test@crackingshells.com"
            },
            "license": {
                "name": "MIT",
                "uri": "https://opensource.org/licenses/MIT"
            },
            "entry_point": "main.py",  # Single string entry point for v1.2.0
            "tools": [
                {
                    "name": f"{package_name}_tool",
                    "description": f"Example tool for {package_name}"
                }
            ]
        }

        # v1.2.0 uses unified dependencies object (same as v1.2.1)
        if dependencies:
            metadata["dependencies"] = dependencies

        return metadata

    def _create_v1_1_0_metadata(self, package_name: str, dependencies: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create metadata conforming to v1.1.0 schema (legacy format)."""
        metadata = {
            "package_schema_version": "1.1.0",
            "name": package_name,
            "version": "1.0.0",
            "description": f"Test package: {package_name}",
            "tags": ["test", "hatch", "mcp"],
            "author": {
                "name": "Test Suite",
                "email": "test@crackingshells.com"
            },
            "license": {
                "name": "MIT",
                "uri": "https://opensource.org/licenses/MIT"
            },
            "entry_point": "main.py"
        }

        # v1.1.0 uses separate dependency arrays
        if dependencies:
            # Handle hatch dependencies
            if "hatch" in dependencies:
                metadata["hatch_dependencies"] = []
                for dep in dependencies["hatch"]:
                    metadata["hatch_dependencies"].append({
                        "name": dep["name"],
                        "type": {"type": "remote"},
                        "version_constraint": dep["version_constraint"]
                    })

            # Handle python dependencies
            if "python" in dependencies:
                metadata["python_dependencies"] = []
                for dep in dependencies["python"]:
                    python_dep = {
                        "name": dep["name"],
                        "version_constraint": dep["version_constraint"],
                        "package_manager": dep.get("package_manager", "pip")
                    }
                    metadata["python_dependencies"].append(python_dep)

        return metadata

    def validate_package_schema(self, package_name: str, schema_version: str = "1.2.1") -> bool:
        """Validate that a generated package conforms to its schema.

        Args:
            package_name: Name of the package to validate
            schema_version: Schema version to validate against

        Returns:
            bool: True if package is valid, False otherwise
        """
        try:
            import json
            import jsonschema

            # Load the package metadata
            package_dir = self.packages_dir / package_name
            metadata_file = package_dir / "hatch_metadata.json"

            if not metadata_file.exists():
                return False

            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            # Load the appropriate schema
            schema_path = Path(__file__).parent.parent.parent / "Hatch-Schemas" / "package" / f"v{schema_version}" / "hatch_pkg_metadata_schema.json"

            if not schema_path.exists():
                print(f"Schema file not found: {schema_path}")
                return False

            with open(schema_path, 'r') as f:
                schema = json.load(f)

            # Validate metadata against schema
            jsonschema.validate(metadata, schema)
            return True

        except jsonschema.ValidationError as e:
            print(f"Schema validation error for {package_name}: {e}")
            return False
        except Exception as e:
            print(f"Validation error for {package_name}: {e}")
            return False

    def _create_dual_entry_points(self, package_dir: Path, package_name: str):
        """Create dual entry points for v1.2.x schemas."""
        # Create mcp_server.py
        mcp_server_content = f'''"""
FastMCP server implementation for {package_name}.
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("{package_name}", log_level="WARNING")

@mcp.tool()
def {package_name}_tool(param: str) -> str:
    """Example tool function for {package_name}.

    Args:
        param (str): Example parameter.

    Returns:
        str: Example result.
    """
    return f"Processed by {package_name}: {{param}}"

if __name__ == "__main__":
    mcp.run()
'''

        mcp_server_path = package_dir / "mcp_server.py"
        with open(mcp_server_path, 'w') as f:
            f.write(mcp_server_content)

        # Create hatch_mcp_server.py
        hatch_mcp_server_content = f'''"""
HatchMCP wrapper for {package_name}.
"""
import sys
from pathlib import Path

# Add package directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server import mcp

def main():
    """Main entry point for HatchMCP wrapper."""
    print("Starting {package_name} via HatchMCP wrapper")
    mcp.run()

if __name__ == "__main__":
    main()
'''

        hatch_mcp_server_path = package_dir / "hatch_mcp_server.py"
        with open(hatch_mcp_server_path, 'w') as f:
            f.write(hatch_mcp_server_content)

    def _create_single_entry_point(self, package_dir: Path, package_name: str):
        """Create single entry point for v1.1.0 schema."""
        main_py_content = f'''"""
Test package: {package_name}
"""

def main():
    """Main entry point for {package_name}."""
    print("Hello from {package_name}!")
    return "{package_name} executed successfully"

if __name__ == "__main__":
    main()
'''

        main_py_path = package_dir / "main.py"
        with open(main_py_path, 'w') as f:
            f.write(main_py_content)
    
    def create_test_registry(self) -> Dict[str, Any]:
        """Create a test registry with all required test packages."""
        # Ensure test packages exist
        self._ensure_test_packages_exist()
        
        registry = {
            "registry_schema_version": "1.1.0",
            "last_updated": datetime.now().isoformat(),
            "repositories": [
                {
                    "name": "test-repo",
                    "url": f"file://{self.packages_dir}",
                    "packages": [],
                    "last_indexed": datetime.now().isoformat()
                }
            ],
            "stats": {
                "total_packages": 0,
                "total_versions": 0
            }
        }
        
        # Add packages to registry
        package_names = [
            "arithmetic_pkg", "base_pkg_1", "base_pkg_2", "python_dep_pkg",
            "circular_dep_pkg_1", "circular_dep_pkg_2", "complex_dep_pkg", 
            "simple_dep_pkg", "missing_dep_pkg", "version_dep_pkg"
        ]
        
        for pkg_name in package_names:
            pkg_path = self.packages_dir / pkg_name
            if pkg_path.exists():
                metadata_path = pkg_path / "hatch_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    package_entry = {
                        "name": metadata["name"],
                        "versions": [
                            {
                                "version": metadata["version"],
                                "dependencies": metadata.get("dependencies", {}),
                                "path": str(pkg_path),
                                "metadata": metadata
                            }
                        ]
                    }
                    registry["repositories"][0]["packages"].append(package_entry)
        
        registry["stats"]["total_packages"] = len(registry["repositories"][0]["packages"])
        registry["stats"]["total_versions"] = sum(
            len(pkg["versions"]) for pkg in registry["repositories"][0]["packages"]
        )
        
        return registry
    
    def _ensure_test_packages_exist(self):
        """Ensure all required test packages exist using v1.2.1 schema."""
        # Base packages (no dependencies)
        self.create_test_package("base_pkg_1")
        self.create_test_package("base_pkg_2")

        # Arithmetic package
        self.create_test_package("arithmetic_pkg")

        # Python dependency package
        self.create_test_package("python_dep_pkg", {
            "python": [
                {
                    "name": "requests",
                    "version_constraint": ">=2.25.0",
                    "package_manager": "pip"
                }
            ]
        })

        # Simple dependency package
        self.create_test_package("simple_dep_pkg", {
            "hatch": [
                {
                    "name": "base_pkg_1",
                    "version_constraint": ">=1.0.0"
                }
            ]
        })

        # Complex dependency package
        self.create_test_package("complex_dep_pkg", {
            "hatch": [
                {
                    "name": "base_pkg_1",
                    "version_constraint": ">=1.0.0"
                },
                {
                    "name": "base_pkg_2",
                    "version_constraint": ">=1.0.0"
                }
            ]
        })

        # Circular dependency packages
        self.create_test_package("circular_dep_pkg_1", {
            "hatch": [
                {
                    "name": "circular_dep_pkg_2",
                    "version_constraint": ">=1.0.0"
                }
            ]
        })
        self.create_test_package("circular_dep_pkg_2", {
            "hatch": [
                {
                    "name": "circular_dep_pkg_1",
                    "version_constraint": ">=1.0.0"
                }
            ]
        })

        # Version dependency package
        self.create_test_package("version_dep_pkg", {
            "hatch": [
                {
                    "name": "base_pkg_1",
                    "version_constraint": "==1.0.0"
                }
            ]
        })

        # Missing dependency package (references non-existent package)
        self.create_test_package("missing_dep_pkg", {
            "hatch": [
                {
                    "name": "nonexistent_pkg",
                    "version_constraint": ">=1.0.0"
                }
            ]
        })
    
    def _create_default_config(self, config_name: str):
        """Create a default configuration file."""
        default_configs = {
            "test_settings": {
                "test_timeout": 30,
                "temp_dir_prefix": "hatch_test_",
                "cleanup_temp_dirs": True,
                "mock_external_services": True
            },
            "installer_configs": {
                "python_installer": {
                    "pip_timeout": 60,
                    "use_cache": False
                },
                "docker_installer": {
                    "timeout": 120,
                    "cleanup_containers": True
                }
            }
        }
        
        config = default_configs.get(config_name, {})
        config_path = self.configs_dir / f"{config_name}.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def _create_default_response(self, response_name: str):
        """Create a default response file."""
        default_responses = {
            "registry_responses": {
                "success": {
                    "status": "success",
                    "data": {"packages": []}
                },
                "error": {
                    "status": "error",
                    "message": "Registry not available"
                }
            }
        }
        
        response = default_responses.get(response_name, {})
        response_path = self.responses_dir / f"{response_name}.json"
        with open(response_path, 'w') as f:
            json.dump(response, f, indent=2)


# Global instance for easy access
test_data = TestDataLoader()


# Convenience functions
def load_test_config(config_name: str) -> Dict[str, Any]:
    """Load test configuration."""
    return test_data.load_config(config_name)


def load_mock_response(response_name: str) -> Dict[str, Any]:
    """Load mock response."""
    return test_data.load_response(response_name)


def get_test_packages_dir() -> Path:
    """Get test packages directory."""
    return test_data.get_test_packages_dir()


def create_test_registry() -> Dict[str, Any]:
    """Create test registry with all packages."""
    return test_data.create_test_registry()
