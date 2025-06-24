#!/usr/bin/env python3
import sys
import unittest
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("environment_test_results.log")
    ]
)
logger = logging.getLogger("hatch.test_runner")

if __name__ == "__main__":
    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    if len(sys.argv) > 1 and sys.argv[1] == "--env-only":
        # Run only environment tests
        logger.info("Running environment tests only...")
        test_suite = test_loader.loadTestsFromName("test_env_manip.PackageEnvironmentTests")
    elif len(sys.argv) > 1 and sys.argv[1] == "--remote-only":
        # Run only remote integration tests
        logger.info("Running remote integration tests only...")
        test_suite = test_loader.loadTestsFromName("test_registry_retriever.RegistryRetrieverTests")
        test_suite = test_loader.loadTestsFromName("test_online_package_loader.OnlinePackageLoaderTests")

    elif len(sys.argv) > 1 and sys.argv[1] == "--registry-online":
        # Run only registry online mode tests
        logger.info("Running registry retriever online mode tests...")
        test_suite = test_loader.loadTestsFromName("test_registry_retriever.RegistryRetrieverTests")
    elif len(sys.argv) > 1 and sys.argv[1] == "--package-online":
        # Run only package loader online mode tests
        logger.info("Running package loader online mode tests...")
        test_suite = test_loader.loadTestsFromName("test_online_package_loader.OnlinePackageLoaderTests")
    elif len(sys.argv) > 1 and sys.argv[1] == "--installer-only":
        # Run only installer interface tests
        logger.info("Running installer interface tests only...")
        test_suite = test_loader.loadTestsFromName("test_installer_base.BaseInstallerTests")
    elif len(sys.argv) > 1 and sys.argv[1] == "--hatch-installer-only":
        # Run only HatchInstaller tests
        logger.info("Running HatchInstaller tests only...")
        test_suite = test_loader.loadTestsFromName("test_hatch_installer.TestHatchInstaller")
    elif len(sys.argv) > 1 and sys.argv[1] == "--python-installer-only":
        # Run only PythonInstaller tests
        logger.info("Running PythonInstaller tests only...")
        test_mocking = test_loader.loadTestsFromName("test_python_installer.TestPythonInstaller")
        test_integration = test_loader.loadTestsFromName("test_python_installer.TestPythonInstallerIntegration")
        test_suite = unittest.TestSuite([test_mocking, test_integration])
    elif len(sys.argv) > 1 and sys.argv[1] == "--all-installers":
        # Run all installer tests
        logger.info("Running all installer tests...")
        hatch_tests = test_loader.loadTestsFromName("test_hatch_installer.TestHatchInstaller")
        python_tests_mocking = test_loader.loadTestsFromName("test_python_installer.TestPythonInstaller")
        python_tests_integration = test_loader.loadTestsFromName("test_python_installer.TestPythonInstallerIntegration")

        # Add future installer tests here as needed

        test_suite = unittest.TestSuite([hatch_tests, python_tests_mocking, python_tests_integration])
    else:
        # Run all tests
        logger.info("Running all package environment tests...")
        test_suite = test_loader.discover('.', pattern='test_*.py')

    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Log test results summary
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    
    # Exit with appropriate status code
    sys.exit(not result.wasSuccessful())
