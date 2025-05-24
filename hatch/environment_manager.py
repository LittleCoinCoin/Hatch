"""
Environment Manager for Hatch package system.

This module provides the core functionality for managing isolated environments
for Hatch packages.
"""
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from hatch_validator import HatchPackageValidator
from .registry_retriever import RegistryRetriever
from .package_loader import HatchPackageLoader, PackageLoaderError
from .registry_explorer import find_package, find_package_version, get_package_release_url


class HatchEnvironmentError(Exception):
    """Exception raised for environment-related errors."""
    pass


class HatchEnvironmentManager:
    """
    Manages Hatch environments for package installation and isolation.
    
    This class handles:
    1. Creating and managing isolated environments
    2. Adding packages to environments
    3. Resolving and managing dependencies using a DependencyResolver
    4. Installing packages with the HatchPackageLoader
    """
    def __init__(self, 
                 cache_ttl: int = 86400,  # Default TTL is 24 hours
                 cache_dir: Optional[Path] = None,
                 simulation_mode: bool = False,
                 local_registry_cache_path: Optional[Path] = None):
        """Initialize the Hatch environment manager.
        
        Args:
            cache_ttl: Time-to-live for cache in seconds
            cache_dir: Directory to store local cache files (default: ~/.hatch)
            simulation_mode: Whether to operate in local simulation mode
            local_registry_cache_path: Path to local registry file (for simulation mode)
        
        """

        self.logger = logging.getLogger("hatch.environment_manager")
        self.logger.setLevel(logging.INFO)
        
        # Set up environment directories
        self.environments_dir = Path.home() / ".hatch" / "envs"
        self.environments_dir.mkdir(exist_ok=True)
        
        self.environments_file = self.environments_dir / "environments.json"
        self.current_env_file = self.environments_dir / "current_env"
        
        # Initialize files if they don't exist
        if not self.environments_file.exists():
            self._initialize_environments_file()
        
        if not self.current_env_file.exists():
            self._initialize_current_env_file()

        # Load environments into cache
        self._environments = self._load_environments()
        self._current_env_name = self._load_current_env_name()
        
        # Initialize dependencies
        self.package_loader = HatchPackageLoader(cache_dir=cache_dir)

        # Get dependency resolver from imported module
        retriever = RegistryRetriever(cache_ttl=cache_ttl,
                                      local_cache_dir=cache_dir,
                                      simulation_mode=simulation_mode,
                                      local_registry_cache_path=local_registry_cache_path)
        self.registry_data = retriever.get_registry()
        self.package_validator = HatchPackageValidator(registry_data=self.registry_data)
        self.dependency_resolver = self.package_validator.dependency_resolver

    def _initialize_environments_file(self):
        """Create the initial environments file with default environment."""
        default_environments = {
            "default": {
                "name": "default",
                "description": "Default environment",
                "created_at": datetime.datetime.now().isoformat(),
                "packages": []
            }
        }
        
        with open(self.environments_file, 'w') as f:
            json.dump(default_environments, f, indent=2)
        
        self.logger.info("Initialized environments file with default environment")
    
    def _initialize_current_env_file(self):
        """Create the current environment file pointing to the default environment."""
        with open(self.current_env_file, 'w') as f:
            f.write("default")
        
        self.logger.info("Initialized current environment to default")
    
    def _load_environments(self) -> Dict:
        """Load environments from the environments file."""
        try:
            with open(self.environments_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.error(f"Failed to load environments: {e}")
            self._initialize_environments_file()
            return {"default": {"name": "default", "description": "Default environment", 
                    "created_at": datetime.datetime.now().isoformat(), "packages": []}}
    
    def _load_current_env_name(self) -> str:
        """Load current environment name from disk."""
        try:
            with open(self.current_env_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            self._initialize_current_env_file()
            return "default"
    
    def get_environments(self) -> Dict:
        """Get environments from cache."""
        return self._environments
    
    def reload_environments(self):
        """Reload environments from disk."""
        self._environments = self._load_environments()
        self._current_env_name = self._load_current_env_name()
        self.logger.info("Reloaded environments from disk")
    
    def _save_environments(self):
        """Save environments to the environments file."""
        try:
            with open(self.environments_file, 'w') as f:
                json.dump(self._environments, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save environments: {e}")
            raise HatchEnvironmentError(f"Failed to save environments: {e}")
    
    def get_current_environment(self) -> str:
        """Get the name of the current environment from cache."""
        return self._current_env_name
    
    def get_current_environment_data(self) -> Dict:
        """Get the data for the current environment."""
        return self._environments[self._current_env_name]
    
    def set_current_environment(self, env_name: str) -> bool:
        """
        Set the current environment.
        
        Args:
            env_name: Name of the environment to set as current
            
        Returns:
            bool: True if successful, False if environment doesn't exist
        """
        # Check if environment exists
        if env_name not in self._environments:
            self.logger.error(f"Environment does not exist: {env_name}")
            return False
        
        # Set current environment
        try:
            with open(self.current_env_file, 'w') as f:
                f.write(env_name)
            
            # Update cache
            self._current_env_name = env_name
            
            self.logger.info(f"Current environment set to: {env_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set current environment: {e}")
            return False
    
    def list_environments(self) -> List[Dict]:
        """
        List all available environments.
        
        Returns:
            List[Dict]: List of environment information dictionaries
        """
        result = []
        for name, env_data in self._environments.items():
            env_info = env_data.copy()
            env_info["is_current"] = (name == self._current_env_name)
            result.append(env_info)
        
        return result
    
    def create_environment(self, name: str, description: str = "") -> bool:
        """
        Create a new environment.
        
        Args:
            name: Name of the environment
            description: Description of the environment
            
        Returns:
            bool: True if created successfully, False if environment already exists
        """
        # Allow alphanumeric characters and underscores
        if not name or not all(c.isalnum() or c == '_' for c in name):
            self.logger.error("Environment name must be alphanumeric or underscore")
            return False
        
        # Check if environment already exists
        if name in self._environments:
            self.logger.warning(f"Environment already exists: {name}")
            return False
        
        # Create new environment
        self._environments[name] = {
            "name": name,
            "description": description,
            "created_at": datetime.datetime.now().isoformat(),
            "packages": []
        }
        
        self._save_environments()
        self.logger.info(f"Created environment: {name}")
        return True
    
    def remove_environment(self, name: str) -> bool:
        """
        Remove an environment.
        
        Args:
            name: Name of the environment to remove
            
        Returns:
            bool: True if removed successfully, False otherwise
        """
        # Cannot remove default environment
        if name == "default":
            self.logger.error("Cannot remove default environment")
            return False
        
        # Check if environment exists
        if name not in self._environments:
            self.logger.warning(f"Environment does not exist: {name}")
            return False
        
        # If removing current environment, switch to default
        if name == self._current_env_name:
            self.set_current_environment("default")
        
        # Remove environment
        del self._environments[name]
        
        # Save environments and update cache
        self._save_environments()
        self.logger.info(f"Removed environment: {name}")
        return True
    
    def environment_exists(self, name: str) -> bool:
        """
        Check if an environment exists.
        
        Args:
            name: Name of the environment to check
            
        Returns:
            bool: True if environment exists, False otherwise
        """
        return name in self._environments
    
    def add_package_to_environment(self, package_path_or_name: str, 
                                  env_name: Optional[str] = None, 
                                  version_constraint: Optional[str] = None) -> bool:
        """
        Add a package to an environment.
        
        Args:
            package_path_or_name: Path to local package or name of remote package
            env_name: Environment to add to (uses current if None)
            version_constraint: Version constraint for remote packages
            
        Returns:
            bool: True if successful, False otherwise
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        # Check if package is local or remote
        package_path = Path(package_path_or_name)
        is_local_package = package_path.exists() and package_path.is_dir()

        local_deps, remote_deps = [], []
        if is_local_package:
            # Get the hatch_dependencies from the local pkg's metadata
            with open(package_path / "hatch_metadata.json", 'r') as f:
                hatch_metadata = json.load(f)
            package_name = hatch_metadata.get("name", Path(package_path).name)
            package_version = hatch_metadata.get("version", "0.0.0")
            hatch_dependencies = hatch_metadata.get("hatch_dependencies", [])
            local_deps, remote_deps = self._get_deps_from_all_local_packages(hatch_dependencies)

        else:
            # For remote packages, there can only be remote dependencies
            package_name = package_path_or_name
            if not version_constraint:
                # Find package in registry data
                package_registry_data = find_package(self.registry_data, package_name)
                if not package_registry_data:
                    self.logger.error(f"Package {package_name} not found in registry")
                    return False
                # Find the information about the package version    
                package_version_data = find_package_version(package_registry_data, version_constraint)
                if not package_version_data:
                    self.logger.error(f"Package {package_name} with version constraint {version_constraint} not found in registry")
                    return False
                else:
                    package_version = package_version_data.get("version")

            remote_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                package_name, package_version).get("dependencies", [])
                
        # and the package we're trying to install
        current_dependencies = []
        
        # Get currently installed packages
        installed_packages = {}
        for pkg in self._environments[env_name].get("packages", []):
            installed_packages[pkg["name"]] = pkg["version"]
            
            # For each installed package, get its dependencies to build the dependency graph
            if pkg["type"] == "local":
                # For local packages, use metadata file to get dependencies
                pkg_install_path = self.get_environment_path(env_name) / pkg["name"]
                if (pkg_install_path / "hatch_metadata.json").exists():
                    with open(pkg_install_path / "hatch_metadata.json", 'r') as f:
                        pkg_metadata = json.load(f)
                    pkg_deps = pkg_metadata.get("hatch_dependencies", [])
                    
                    # Transform the dependencies to correct format
                    processed_deps = []
                    for dep in pkg_deps:
                        if dep.get("name"):  # Make sure the dependency has a name
                            processed_deps.append(dep.get("name"))
                    
                    current_dependencies.append({"name": pkg["name"], "dependencies": processed_deps})
            else:
                # For remote packages, use the registry data
                pkg_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                    pkg["name"], pkg["version"]).get("dependencies", [])
                
                # Transform the dependencies to correct format
                processed_deps = []
                for dep in pkg_deps:
                    if dep.get("name"):  # Make sure the dependency has a name
                        processed_deps.append(dep.get("name"))
                
                current_dependencies.append({"name": pkg["name"], "dependencies": processed_deps})
        
        # Add the new package to check if it would create a circular dependency
        if is_local_package:
            hatch_deps = hatch_metadata.get("hatch_dependencies", [])
            processed_deps = []
            for dep in hatch_deps:
                if dep.get("name"):  # Make sure the dependency has a name
                    processed_deps.append(dep.get("name"))
                    
            current_dependencies.append({
                "name": package_name,
                "dependencies": processed_deps
            })
        else:
            pkg_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                package_name, package_version).get("dependencies", [])
            
            processed_deps = []
            for dep in pkg_deps:
                if dep.get("name"):  # Make sure the dependency has a name
                    processed_deps.append(dep.get("name"))
                    
            current_dependencies.append({
                "name": package_name,
                "dependencies": processed_deps
            })
        
        self.logger.debug(f"Checking for circular dependencies in: {current_dependencies}")
        
        # Check for circular dependencies
        has_cycles, cycles = self.package_validator.dependency_resolver.detect_dependency_cycles(
            current_dependencies)
            
        if has_cycles:
            self.logger.error(f"Circular dependency detected: {cycles}")
            return False

        # Find missing dependencies
        local_missing_deps = self._filter_for_missing_dependencies(local_deps, env_name)
        remote_missing_deps = self._filter_for_missing_dependencies(remote_deps, env_name)

        # Install missing dependencies
        ## Delegate to package loader
        for dep in local_missing_deps:
            try:
                self.package_loader.install_local_package(
                    dep["path"],
                    self.get_environment_path(env_name),
                    dep["name"]
                )
                with open(dep["path"] / "hatch_metadata.json", 'r') as f:
                    hatch_metadata = json.load(f)
                self._add_package_to_env_data(env_name, dep["name"], hatch_metadata.get("version"), "local", "local")
            except PackageLoaderError as e:
                self.logger.error(f"Failed to install local package {dep['name']}: {e}")
                return False
        for dep in remote_missing_deps:
            try:
                # First, download the package to cache
                package_registry_data = find_package(self.registry_data, dep['name'])     
                self.logger.debug(f"Package registry data: {json.dumps(package_registry_data, indent=2)}")           
                package_url, package_version = get_package_release_url(package_registry_data, dep["version_constraint"])
                self.package_loader.install_remote_package(package_url,
                                                            dep["name"],
                                                            package_version,
                                                            self.get_environment_path(env_name))
                self._add_package_to_env_data(env_name, dep["name"], package_version, "remote", "registry")
            except PackageLoaderError as e:
                self.logger.error(f"Failed to install remote package {dep['name']}: {e}")
                return False

        # Install the main package and add it to environment data
        try:
            if is_local_package:
                # Install the local package
                self.package_loader.install_local_package(
                    package_path,
                    self.get_environment_path(env_name),
                    Path(package_path).name
                )
                # Read metadata to get name and version
                with open(package_path / "hatch_metadata.json", 'r') as f:
                    package_metadata = json.load(f)
                package_name = package_metadata.get("name", Path(package_path).name)
                package_version = package_metadata.get("version", "0.0.0")
                self._add_package_to_env_data(env_name, package_name, package_version, "local", "local")
            else:                # Remote package
                package_registry_data = find_package(self.registry_data, package_path_or_name)
                if not package_registry_data:
                    self.logger.error(f"Package {package_path_or_name} not found in registry")
                    return False

                package_url, package_version = get_package_release_url(package_registry_data, version_constraint)
                if not package_url:
                    self.logger.error(f"Could not find release URL for package {package_path_or_name} with version constraint {version_constraint}")
                    return False
                    
                self.package_loader.install_remote_package(
                    package_url,
                    package_path_or_name,
                    package_version,
                    self.get_environment_path(env_name)
                )
                self._add_package_to_env_data(env_name, package_path_or_name, package_version, "remote", "registry")
        except PackageLoaderError as e:
            self.logger.error(f"Failed to install package {package_path_or_name}: {e}")
            return False

        return True

    def _get_deps_from_all_local_packages(self, hatch_dependencies: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Retrieves the local and remote dependencies from the hatch_dependencies list of a package.

        Args:
            hatch_dependencies: List of dependencies from the package's metadata
        Returns:
            Tuple of local and remote dependencies
        """
        deps_queue = hatch_dependencies.copy()
        local_deps = []
        remote_deps_queue = []
        
        while deps_queue:
            dep = deps_queue.pop(0)
            if dep.get("type").get("type") == "local":
                local_deps += [{"name": dep.get("name"), "path": dep.get("type").get("path")}]
                deps_queue += local_deps[-1].get("hatch_dependencies", [])
            else:
                remote_deps_queue.append(dep)

        remote_deps = []
        while remote_deps_queue:
            dep = remote_deps_queue.pop(0)
            remote_deps += [{"name": dep.get("name"), "version_constraint": dep.get("version_constraint")}]
            new_deps = self.package_validator.dependency_resolver.get_full_package_dependencies(
                dep.get("name"), dep.get("version_constraint"))
            remote_deps_queue += new_deps.get("dependencies", [])

        return local_deps, remote_deps

    def _filter_for_missing_dependencies(self, dependencies: List[Dict], env_name: str) -> List[Dict]:
        """Determine which dependencies are not installed in the environment."""
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        # Get currently installed packages
        installed_packages = {}
        for pkg in self._environments[env_name].get("packages", []):
            installed_packages[pkg["name"]] = pkg["version"]
        
        # Find missing dependencies
        missing_deps = []
        for dep in dependencies:
            dep_name = dep.get("name")
            if dep_name not in installed_packages:
                missing_deps.append(dep)
                continue
            
            # Check version constraints
            constraint = dep.get("version_constraint")
            if constraint and not self.package_validator.dependency_resolver.is_version_compatible(
                    installed_packages[dep_name], constraint):
                missing_deps.append(dep)
        
        return missing_deps
    
    def _add_package_to_env_data(self, env_name: str, package_name: str, 
                               package_version: str, package_type: str, 
                               source: str) -> None:
        """Update environment data with package information."""
        if env_name not in self._environments:
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        # Check if package already exists
        for i, pkg in enumerate(self._environments[env_name].get("packages", [])):
            if pkg.get("name") == package_name:
                # Replace existing package entry
                self._environments[env_name]["packages"][i] = {
                    "name": package_name,
                    "version": package_version,
                    "type": package_type,
                    "source": source,
                    "installed_at": datetime.datetime.now().isoformat()
                }
                self._save_environments()
                return
        
        # if it doesn't exist add new package entry
        self._environments[env_name]["packages"] += [{
            "name": package_name,
            "version": package_version,
            "type": package_type,
            "source": source,
            "installed_at": datetime.datetime.now().isoformat()
        }]

        self._save_environments()
    
    def get_environment_path(self, env_name: str) -> Path:
        """
        Get the path to the environment directory.
        
        Args:
            env_name: Name of the environment
            
        Returns:
            Path: Path to the environment directory
            
        Raises:
            HatchEnvironmentError: If environment doesn't exist
        """
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        env_path = self.environments_dir / env_name
        env_path.mkdir(exist_ok=True)
        return env_path
    
    def list_packages(self, env_name: Optional[str] = None) -> List[Dict]:
        """
        List all packages installed in an environment.
        
        Args:
            env_name: Name of the environment (uses current if None)
            
        Returns:
            List[Dict]: List of package information dictionaries
            
        Raises:
            HatchEnvironmentError: If environment doesn't exist
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        packages = []
        for pkg in self._environments[env_name].get("packages", []):
            # Add full package info including paths
            pkg_info = pkg.copy()
            pkg_info["path"] = str(self.get_environment_path(env_name) / pkg["name"])
            # Check if the package is Hatch compliant (has hatch_metadata.json)
            pkg_path = self.get_environment_path(env_name) / pkg["name"]
            pkg_info["hatch_compliant"] = (pkg_path / "hatch_metadata.json").exists()
            
            # Add source information
            pkg_info["source"] = {
                "uri": pkg.get("source", "unknown"),
                "path": str(pkg_path)
            }
            
            packages.append(pkg_info)
        
        return packages
    
    def remove_package(self, package_name: str, env_name: Optional[str] = None) -> bool:
        """
        Remove a package from an environment.
        
        Args:
            package_name: Name of the package to remove
            env_name: Environment to remove from (uses current if None)
            
        Returns:
            bool: True if successful, False otherwise
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        
        # Check if package exists in environment
        env_packages = self._environments[env_name].get("packages", [])
        pkg_index = None
        for i, pkg in enumerate(env_packages):
            if pkg.get("name") == package_name:
                pkg_index = i
                break
        
        if pkg_index is None:
            self.logger.warning(f"Package {package_name} not found in environment {env_name}")
            return False
        
        # Remove package from filesystem
        pkg_path = self.get_environment_path(env_name) / package_name
        try:
            import shutil
            if pkg_path.exists():
                shutil.rmtree(pkg_path)
        except Exception as e:
            self.logger.error(f"Failed to remove package files for {package_name}: {e}")
            return False
        
        # Remove package from environment data
        env_packages.pop(pkg_index)
        self._save_environments()
        
        self.logger.info(f"Removed package {package_name} from environment {env_name}")
        return True
