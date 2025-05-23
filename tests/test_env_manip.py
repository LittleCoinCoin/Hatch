import sys
import json
import unittest
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path for direct testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from hatch.package_environments import HatchEnvironmentManager
from hatch.registry_retriever import RegistryRetriever
from hatch_registry import RegistryUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hatch.environment_tests")


class PackageEnvironmentTests(unittest.TestCase):
    """Tests for the package environment management functionality."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a temporary directory for test environments
        self.temp_dir = tempfile.mkdtemp()
        
        # Path to Hatching-Dev packages
        self.hatch_dev_path = Path(__file__).parent.parent.parent / "Hatching-Dev"
        self.assertTrue(self.hatch_dev_path.exists(), 
                        f"Hatching-Dev directory not found at {self.hatch_dev_path}")
        
        # Create a sample registry that includes Hatching-Dev packages
        self._create_sample_registry()
        self.test_registry = RegistryUpdater(self.registry_path)
        
        # Override environment paths to use our test directory
        env_dir = Path(self.temp_dir) / "envs"
        env_dir.mkdir(exist_ok=True)
        
        # Create environment manager for testing with isolated test directories
        self.env_manager = HatchEnvironmentManager(simulation_mode=True, local_registry_cache_path=self.registry_path)
        
        # Override environment paths
        self.env_manager.environments_dir = env_dir
        self.env_manager.environments_file = env_dir / "environments.json"
        self.env_manager.current_env_file = env_dir / "current_env"
        
        # Initialize environment files with clean state
        self.env_manager._initialize_environments_file()
        self.env_manager._initialize_current_env_file()
        
        # Reload environments to ensure clean state
        self.env_manager.reload_environments()
        
    def _create_sample_registry(self):
        """Create a sample registry with Hatching-Dev packages"""
        # Basic registry structure
        test_registry = {
            "registry_schema_version": "1.1.0",
            "last_updated": datetime.now().isoformat(),
            "repositories": [
                {
                    "name": "test-repo",
                    "url": "file:///hatching-dev",
                    "last_indexed": datetime.now().isoformat(),
                    "packages": []
                }
            ],
            "stats": {
                "total_packages": 0,
                "total_versions": 0
            }
        }

        registry_dir = Path(self.temp_dir) / "registry"
        registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = registry_dir / "hatch_packages_registry.json"

        with open(self.registry_path, "w") as f: 
            json.dump(test_registry, f, indent=2)
        logger.info(f"Sample registry created at {self.registry_path}")
        
    def tearDown(self):
        """Clean up test environment after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_create_environment(self):
        """Test creating an environment."""
        result = self.env_manager.create_environment("test_env", "Test environment")
        self.assertTrue(result, "Failed to create environment")
        
        # Verify environment exists
        self.assertTrue(self.env_manager.environment_exists("test_env"), "Environment doesn't exist after creation")
        
        # Verify environment data
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")
        self.assertEqual(env_data["name"], "test_env")
        self.assertEqual(env_data["description"], "Test environment")
        self.assertIn("created_at", env_data)
        self.assertIn("packages", env_data)
        self.assertEqual(len(env_data["packages"]), 0)
    
    def test_remove_environment(self):
        """Test removing an environment."""
        # First create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        self.assertTrue(self.env_manager.environment_exists("test_env"))
        
        # Then remove it
        result = self.env_manager.remove_environment("test_env")
        self.assertTrue(result, "Failed to remove environment")
        
        # Verify environment no longer exists
        self.assertFalse(self.env_manager.environment_exists("test_env"), "Environment still exists after removal")
    
    def test_set_current_environment(self):
        """Test setting the current environment."""
        # First create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        # Set it as current
        result = self.env_manager.set_current_environment("test_env")
        self.assertTrue(result, "Failed to set current environment")
        
        # Verify it's the current environment
        current_env = self.env_manager.get_current_environment()
        self.assertEqual(current_env, "test_env", "Current environment not set correctly")
    
    def test_add_local_package(self):
        """Test adding a local package to an environment."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        # Use arithmetic_pkg from Hatching-Dev
        pkg_path = self.hatch_dev_path / "arithmetic_pkg"
        self.assertTrue(pkg_path.exists(), f"Test package not found: {pkg_path}")
        
        # Add package to environment
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),  # Convert to string to handle Path objects
            "test_env"
        )
        
        self.assertTrue(result, "Failed to add local package to environment")
        
        # Verify package was added to environment data
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")
        
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 1, "Package not added to environment data")
        
        pkg_data = packages[0]
        self.assertIn("name", pkg_data, "Package data missing name")
        self.assertIn("version", pkg_data, "Package data missing version")
        self.assertIn("type", pkg_data, "Package data missing type")
        self.assertEqual(pkg_data["type"], "local", "Package type not set to local")
    
    def test_add_package_with_dependencies(self):
        """Test adding a package with dependencies to an environment."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        # First add the base package that is a dependency
        base_pkg_path = self.hatch_dev_path / "base_pkg_1"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env"
        )
        self.assertTrue(result, "Failed to add base package to environment")
            
        # Then add the package with dependencies
        pkg_path = self.hatch_dev_path / "simple_dep_pkg"
        self.assertTrue(pkg_path.exists(), f"Dependent package not found: {pkg_path}")
        
        # Add package to environment
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env"
        )
        
        self.assertTrue(result, "Failed to add package with dependencies")
        
        # Verify both packages are in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")
        
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 2, "Not all packages were added to environment")
        
        # Check that both packages are in the environment data
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("base_pkg_1", package_names, "Base package missing from environment")
        self.assertIn("simple_dep_pkg", package_names, "Dependent package missing from environment")
    
    def test_add_complex_dependencies(self):
        """Test adding a package with complex dependencies."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        
        # First add all the base packages that are dependencies
        for base_pkg in ["base_pkg_1", "base_pkg_2", "python_dep_pkg"]:
            pkg_path = self.hatch_dev_path / base_pkg
            self.assertTrue(pkg_path.exists(), f"Base package not found: {pkg_path}")
            
            result = self.env_manager.add_package_to_environment(
                str(pkg_path),
                "test_env"
            )
            self.assertTrue(result, f"Failed to add base package: {base_pkg}")
        
        # Now add the complex dependency package
        complex_pkg_path = self.hatch_dev_path / "complex_dep_pkg"
        self.assertTrue(complex_pkg_path.exists(), f"Complex package not found: {complex_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(complex_pkg_path),
            "test_env"
        )
        
        # This should succeed because all dependencies are satisfied
        self.assertTrue(result, "Failed to add package with complex dependencies")
        
        # Verify all packages are in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        self.assertIsNotNone(env_data, "Environment data not found")
        
        packages = env_data.get("packages", [])
        
        # Check all expected packages are there
        expected_packages = ["base_pkg_1", "base_pkg_2", "python_dep_pkg", "complex_dep_pkg"]
        package_names = [pkg["name"] for pkg in packages]
        
        for pkg_name in expected_packages:
            self.assertIn(pkg_name, package_names, f"Package {pkg_name} missing from environment")

if __name__ == "__main__":
    unittest.main()
