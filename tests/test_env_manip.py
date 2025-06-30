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

from hatch.environment_manager import HatchEnvironmentManager
from hatch.installers.docker_installer import DOCKER_DAEMON_AVAILABLE

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
        
        # Override environment paths to use our test directory
        env_dir = Path(self.temp_dir) / "envs"
        env_dir.mkdir(exist_ok=True)
        
        # Create environment manager for testing with isolated test directories
        self.env_manager = HatchEnvironmentManager(
            environments_dir=env_dir,
            simulation_mode=True,
            local_registry_cache_path=self.registry_path)
        
        # Reload environments to ensure clean state
        self.env_manager.reload_environments()
        
    def _create_sample_registry(self):
        """Create a sample registry with Hatching-Dev packages using real metadata."""
        now = datetime.now().isoformat()
        registry = {
            "registry_schema_version": "1.1.0",
            "last_updated": now,
            "repositories": [
                {
                    "name": "test-repo",
                    "url": f"file://{self.hatch_dev_path}",
                    "last_indexed": now,
                    "packages": []
                }
            ],
            "stats": {
                "total_packages": 0,
                "total_versions": 0
            }
        }
        pkg_names = [
            "arithmetic_pkg", "base_pkg_1", "base_pkg_2", "python_dep_pkg",
            "circular_dep_pkg_1", "circular_dep_pkg_2", "complex_dep_pkg", "simple_dep_pkg"
        ]
        for pkg_name in pkg_names:
            pkg_path = self.hatch_dev_path / pkg_name
            if pkg_path.exists():
                metadata_path = pkg_path / "hatch_metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                        pkg_entry = {
                            "name": metadata.get("name", pkg_name),
                            "description": metadata.get("description", ""),
                            "tags": metadata.get("tags", []),
                            "latest_version": metadata.get("version", "1.0.0"),
                            "versions": [
                                {
                                    "version": metadata.get("version", "1.0.0"),
                                    "release_uri": f"file://{pkg_path}",
                                    "author": {
                                        "GitHubID": metadata.get("author", {}).get("name", "test_user"),
                                        "email": metadata.get("author", {}).get("email", "test@example.com")
                                    },
                                    "added_date": now,
                                    "hatch_dependencies_added": [
                                        {
                                            "name": dep["name"],
                                            "version_constraint": dep.get("version_constraint", "")
                                        } for dep in metadata.get("hatch_dependencies", [])
                                    ],
                                    "python_dependencies_added": [
                                        {
                                            "name": dep["name"],
                                            "version_constraint": dep.get("version_constraint", ""),
                                            "package_manager": dep.get("package_manager", "pip")
                                        } for dep in metadata.get("python_dependencies", [])
                                    ],
                                    "hatch_dependencies_removed": [],
                                    "hatch_dependencies_modified": [],
                                    "python_dependencies_removed": [],
                                    "python_dependencies_modified": [],
                                    "compatibility_changes": {}
                                }
                            ]
                        }
                        registry["repositories"][0]["packages"].append(pkg_entry)
                    except Exception as e:
                        logger.error(f"Failed to load metadata for {pkg_name}: {e}")
                        raise e
        # Update stats
        registry["stats"]["total_packages"] = len(registry["repositories"][0]["packages"])
        registry["stats"]["total_versions"] = sum(len(pkg["versions"]) for pkg in registry["repositories"][0]["packages"])
        registry_dir = Path(self.temp_dir) / "registry"
        registry_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = registry_dir / "hatch_packages_registry.json"
        with open(self.registry_path, "w") as f:
            json.dump(registry, f, indent=2)
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
        self.env_manager.set_current_environment("test_env")
        
        # Use arithmetic_pkg from Hatching-Dev
        pkg_path = self.hatch_dev_path / "arithmetic_pkg"
        self.assertTrue(pkg_path.exists(), f"Test package not found: {pkg_path}")
        
        # Add package to environment
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),  # Convert to string to handle Path objects
            "test_env",
            auto_approve=True  # Auto-approve for testing
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
        self.assertIn("source", pkg_data, "Package data missing source")
    
    def test_add_package_with_dependencies(self):
        """Test adding a package with dependencies to an environment."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")

        # First add the base package that is a dependency
        base_pkg_path = self.hatch_dev_path / "base_pkg_1"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")
            
        # Then add the package with dependencies
        pkg_path = self.hatch_dev_path / "simple_dep_pkg"
        self.assertTrue(pkg_path.exists(), f"Dependent package not found: {pkg_path}")
        
        # Add package to environment
        result = self.env_manager.add_package_to_environment(
            str(pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
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
    
    def test_add_package_with_some_dependencies_already_present(self):
        """Test adding a package where some dependencies are already present and others are not."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # First add only one of the dependencies that complex_dep_pkg needs
        base_pkg_path = self.hatch_dev_path / "base_pkg_1"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")
        
        # Verify base_pkg_1 is in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 1, "Base package not added correctly")
        self.assertEqual(packages[0]["name"], "base_pkg_1", "Wrong package added")
        
        # Now add complex_dep_pkg which depends on base_pkg_1, base_pkg_2
        # base_pkg_1 should be satisfied, base_pkg_2 should need installation
        complex_pkg_path = self.hatch_dev_path / "complex_dep_pkg"
        self.assertTrue(complex_pkg_path.exists(), f"Complex package not found: {complex_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(complex_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with mixed dependency states")
        
        # Verify all required packages are now in the environment
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])

        # Should have base_pkg_1 (already present), base_pkg_2, and complex_dep_pkg
        expected_packages = ["base_pkg_1", "base_pkg_2", "complex_dep_pkg"]
        package_names = [pkg["name"] for pkg in packages]
        
        for pkg_name in expected_packages:
            self.assertIn(pkg_name, package_names, f"Package {pkg_name} missing from environment")
    
    def test_add_package_with_all_dependencies_already_present(self):
        """Test adding a package where all dependencies are already present."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # First add all dependencies that simple_dep_pkg needs
        base_pkg_path = self.hatch_dev_path / "base_pkg_1"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")
        
        # Verify base package is installed
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        self.assertEqual(len(packages), 1, "Base package not added correctly")
        
        # Now add simple_dep_pkg which only depends on base_pkg_1 (which is already present)
        simple_pkg_path = self.hatch_dev_path / "simple_dep_pkg"
        self.assertTrue(simple_pkg_path.exists(), f"Simple package not found: {simple_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(simple_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with all dependencies satisfied")
        
        # Verify both packages are in the environment - no new dependencies should be added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        
        # Should have base_pkg_1 (already present) and simple_dep_pkg (newly added)
        expected_packages = ["base_pkg_1", "simple_dep_pkg"]
        package_names = [pkg["name"] for pkg in packages]
        
        self.assertEqual(len(packages), 2, "Unexpected number of packages in environment")
        for pkg_name in expected_packages:
            self.assertIn(pkg_name, package_names, f"Package {pkg_name} missing from environment")
    
    def test_add_package_with_version_constraint_satisfaction(self):
        """Test adding a package with version constraints where dependencies are satisfied."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")

        # Add base_pkg_1 with a specific version
        base_pkg_path = self.hatch_dev_path / "base_pkg_1"
        self.assertTrue(base_pkg_path.exists(), f"Base package not found: {base_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(base_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        self.assertTrue(result, "Failed to add base package to environment")
        
        # Look for a package that has version constraints to test against
        # For now, we'll simulate this by trying to add another package that depends on base_pkg_1
        simple_pkg_path = self.hatch_dev_path / "simple_dep_pkg"
        self.assertTrue(simple_pkg_path.exists(), f"Simple package not found: {simple_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(simple_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with version constraint dependencies")
        
        # Verify packages are correctly installed
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        
        self.assertIn("base_pkg_1", package_names, "Base package missing from environment")
        self.assertIn("simple_dep_pkg", package_names, "Dependent package missing from environment")
    
    def test_add_package_with_mixed_dependency_types(self):
        """Test adding a package with mixed hatch and python dependencies."""
        # Create an environment
        self.env_manager.create_environment("test_env", "Test environment")
        self.env_manager.set_current_environment("test_env")
        
        # Add a package that has both hatch and python dependencies
        python_dep_pkg_path = self.hatch_dev_path / "python_dep_pkg"
        self.assertTrue(python_dep_pkg_path.exists(), f"Python dependency package not found: {python_dep_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(python_dep_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with mixed dependency types")
        
        # Verify package was added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        
        self.assertIn("python_dep_pkg", package_names, "Package with mixed dependencies missing from environment")
        
        # Now add a package that depends on the python_dep_pkg (should be satisfied)
        # and also depends on other packages (should need installation)
        complex_pkg_path = self.hatch_dev_path / "complex_dep_pkg"
        self.assertTrue(complex_pkg_path.exists(), f"Complex package not found: {complex_pkg_path}")
        
        result = self.env_manager.add_package_to_environment(
            str(complex_pkg_path),
            "test_env",
            auto_approve=True  # Auto-approve for testing
        )
        
        self.assertTrue(result, "Failed to add package with mixed satisfied/unsatisfied dependencies")
        
        # Verify all expected packages are present
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        
        # Should have python_dep_pkg (already present) plus any other dependencies of complex_dep_pkg
        self.assertIn("python_dep_pkg", package_names, "Originally installed package missing")
        self.assertIn("complex_dep_pkg", package_names, "New package missing from environment")

        # Python dep package has a dep to request. This should be satisfied in the python environment
        python_env_info = self.env_manager.python_env_manager.get_environment_info("test_env")
        packages = python_env_info.get("packages", [])
        self.assertIsNotNone(packages, "Python environment packages not found")
        self.assertGreater(len(packages), 0, "No packages found in Python environment")
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("requests", package_names, f"Expected 'requests' package not found in Python environment: {packages}")

    @unittest.skipIf(sys.platform.startswith("win"), "System dependency test skipped on Windows")
    def test_add_package_with_system_dependency(self):
        """Test adding a package with a system dependency."""
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # Add a package that declares a system dependency (e.g., 'curl')
        system_dep_pkg_path = self.hatch_dev_path / "system_dep_pkg"
        self.assertTrue(system_dep_pkg_path.exists(), f"System dependency package not found: {system_dep_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(system_dep_pkg_path),
            "test_env",
            auto_approve=True
        )
        self.assertTrue(result, "Failed to add package with system dependency")

        # Verify package was added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("system_dep_pkg", package_names, "System dependency package missing from environment")

    # Skip if Docker is not available
    @unittest.skipUnless(DOCKER_DAEMON_AVAILABLE, "Docker dependency test skipped due to Docker not being available")
    def test_add_package_with_docker_dependency(self):
        """Test adding a package with a docker dependency."""
        self.env_manager.create_environment("test_env", "Test environment", create_python_env=False)
        self.env_manager.set_current_environment("test_env")
        # Add a package that declares a docker dependency (e.g., 'redis:latest')
        docker_dep_pkg_path = self.hatch_dev_path / "docker_dep_pkg"
        self.assertTrue(docker_dep_pkg_path.exists(), f"Docker dependency package not found: {docker_dep_pkg_path}")

        result = self.env_manager.add_package_to_environment(
            str(docker_dep_pkg_path),
            "test_env",
            auto_approve=True
        )
        self.assertTrue(result, "Failed to add package with docker dependency")

        # Verify package was added
        env_data = self.env_manager.get_environments().get("test_env")
        packages = env_data.get("packages", [])
        package_names = [pkg["name"] for pkg in packages]
        self.assertIn("docker_dep_pkg", package_names, "Docker dependency package missing from environment")

if __name__ == "__main__":
    unittest.main()
