"""
Test script to verify wobble migration is working correctly.
"""
import unittest
import sys
from pathlib import Path

from wobble.decorators import regression_test, integration_test, slow_test

# Add parent directory to path for direct testing
# Import path management removed - using test_data_utils for test dependencies

# Import test data utilities
from test_data_utils import test_data

class TestWobbleMigration(unittest.TestCase):
    """Test suite to verify wobble migration functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for migration testing."""
        cls.test_data_loader = test_data
        cls.test_data_loader.setup()

    @classmethod
    def tearDownClass(cls):
        """Clean up test data after testing."""
        cls.test_data_loader.cleanup()
    @regression_test
    def test_test_data_creation(self):
        """Test that test data packages are created correctly."""
        # Verify test packages directory exists
        self.assertTrue(self.test_data_loader.packages_dir.exists())
        
        # Verify specific test packages exist
        expected_packages = [
            "base_pkg_1", "base_pkg_2", "arithmetic_pkg",
            "python_dep_pkg", "simple_dep_pkg", "complex_dep_pkg"
        ]
        
        for package_name in expected_packages:
            package_dir = self.test_data_loader.packages_dir / package_name
            self.assertTrue(package_dir.exists(), f"Package {package_name} should exist")
            
            # Verify metadata file exists
            metadata_file = package_dir / "hatch_metadata.json"
            self.assertTrue(metadata_file.exists(), f"Metadata file for {package_name} should exist")
    @regression_test
    def test_wobble_decorators_import(self):
        """Test that wobble decorators can be imported successfully."""
        # This test verifies that wobble is properly installed and accessible
        from wobble.decorators import regression_test, integration_test
        
        # Verify decorators are callable
        self.assertTrue(callable(regression_test))
        self.assertTrue(callable(integration_test))
    @regression_test
    def test_package_metadata_schema_compliance(self):
        """Test that generated packages comply with Hatch schema v1.2.1."""
        import json
        
        # Test a simple package
        package_dir = self.test_data_loader.packages_dir / "base_pkg_1"
        metadata_file = package_dir / "hatch_metadata.json"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Verify required fields for v1.2.1 schema
        required_fields = [
            "package_schema_version", "name", "version", "entry_point",
            "description", "tags", "author", "license"
        ]
        
        for field in required_fields:
            self.assertIn(field, metadata, f"Required field '{field}' missing from metadata")
        
        # Verify schema version
        self.assertEqual(metadata["package_schema_version"], "1.2.1")
        
        # Verify entry point structure for v1.2.1
        self.assertIn("mcp_server", metadata["entry_point"])
        self.assertIn("hatch_mcp_server", metadata["entry_point"])

if __name__ == "__main__":
    unittest.main()
