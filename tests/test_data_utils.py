"""Test data utilities for Hatch test suite.

This module provides utilities for loading test data from static test packages.
All dynamic package generation has been removed in favor of static packages.
"""

import json
from pathlib import Path
from typing import Any, Dict


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
    
    def setup(self):
        """Set up test data (placeholder for future setup logic)."""
        # Currently no setup needed as test packages are static
        pass
    
    def cleanup(self):
        """Clean up test data (placeholder for future cleanup logic)."""
        # Currently no cleanup needed as test packages are persistent
        pass
    
    def get_test_packages_dir(self) -> Path:
        """Get the test packages directory path.
        
        Returns:
            Path to the test packages directory
        """
        return self.packages_dir
    
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
