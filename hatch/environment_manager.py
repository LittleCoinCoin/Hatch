"""Environment Manager for Hatch package system.

This module provides the core functionality for managing isolated environments
for Hatch packages.
"""
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from hatch_validator.registry.registry_service import RegistryService, RegistryError
from .registry_retriever import RegistryRetriever
from .package_loader import HatchPackageLoader
from .installers.dependency_installation_orchestrator import DependencyInstallerOrchestrator

class HatchEnvironmentError(Exception):
    """Exception raised for environment-related errors."""
    pass


class HatchEnvironmentManager:
    """Manages Hatch environments for package installation and isolation.
    
    This class handles:
    1. Creating and managing isolated environments
    2. Environment lifecycle and state management  
    3. Delegating package installation to the DependencyInstallerOrchestrator
    4. Managing environment metadata and persistence
    """
    def __init__(self, 
                 environments_dir: Optional[Path] = None,
                 cache_ttl: int = 86400,  # Default TTL is 24 hours
                 cache_dir: Optional[Path] = None,
                 simulation_mode: bool = False,
                 local_registry_cache_path: Optional[Path] = None):
        """Initialize the Hatch environment manager.
        
        Args:
            environments_dir (Path, optional): Directory to store environments. Defaults to ~/.hatch/envs.
            cache_ttl (int): Time-to-live for cache in seconds. Defaults to 86400 (24 hours).
            cache_dir (Path, optional): Directory to store local cache files. Defaults to ~/.hatch.
            simulation_mode (bool): Whether to operate in local simulation mode. Defaults to False.
            local_registry_cache_path (Path, optional): Path to local registry file. Defaults to None.
        
        """

        self.logger = logging.getLogger("hatch.environment_manager")
        self.logger.setLevel(logging.INFO)
        # Set up environment directories
        self.environments_dir = environments_dir or (Path.home() / ".hatch" / "envs")
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
        self.retriever = RegistryRetriever(cache_ttl=cache_ttl,
                                      local_cache_dir=cache_dir,
                                      simulation_mode=simulation_mode,
                                      local_registry_cache_path=local_registry_cache_path)
        self.registry_data = self.retriever.get_registry()
        
        # Initialize services for dependency management
        self.registry_service = RegistryService(self.registry_data)
        
        self.dependency_orchestrator = DependencyInstallerOrchestrator(
            package_loader=self.package_loader,
            registry_service=self.registry_service,
            registry_data=self.registry_data
        )

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
                                  version_constraint: Optional[str] = None,
                                  force_download: bool = False,
                                  refresh_registry: bool = False,
                                  auto_approve: bool = False) -> bool:
        """Add a package to an environment.
        
        This method delegates all installation orchestration to the DependencyInstallerOrchestrator
        while maintaining responsibility for environment lifecycle and state management.

        Args:
            package_path_or_name (str): Path to local package or name of remote package.
            env_name (str, optional): Environment to add to. Defaults to current environment.
            version_constraint (str, optional): Version constraint for remote packages. Defaults to None.
            force_download (bool, optional): Force download even if package is cached. When True, 
                bypass the package cache and download directly from the source. Defaults to False.
            refresh_registry (bool, optional): Force refresh of registry data. When True, 
                fetch the latest registry data before resolving dependencies. Defaults to False.
            auto_approve (bool, optional): Skip user consent prompt for automation scenarios. Defaults to False.
            
        Returns:
            bool: True if successful, False otherwise.
        """        
        env_name = env_name or self._current_env_name
        
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        
        # Refresh registry if requested
        if refresh_registry:
            self.refresh_registry(force_refresh=True)
        
        try:
            # Get currently installed packages for filtering
            existing_packages = {}
            for pkg in self._environments[env_name].get("packages", []):
                existing_packages[pkg["name"]] = pkg["version"]
            
            # Delegate installation to orchestrator
            success, installed_packages = self.dependency_orchestrator.install_dependencies(
                package_path_or_name=package_path_or_name,
                env_path=self.get_environment_path(env_name),
                env_name=env_name,
                existing_packages=existing_packages,
                version_constraint=version_constraint,
                force_download=force_download,
                auto_approve=auto_approve
            )
            
            if success:
                # Update environment metadata with installed packages
                for pkg_info in installed_packages:
                    self._add_package_to_env_data(
                        env_name=env_name,
                        package_name=pkg_info["name"],
                        package_version=pkg_info["version"],
                        package_type=pkg_info["type"],
                        source=pkg_info["source"]
                    )
                
                self.logger.info(f"Successfully installed {len(installed_packages)} packages to environment {env_name}")
                return True
            else:
                self.logger.info("Package installation was cancelled or failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add package to environment: {e}")
            return False

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

    def get_servers_entry_points(self, env_name: Optional[str] = None) -> List[str]:
        """
        Get the list of entry points for the MCP servers of each package in an environment.
        
        Args:
            env_name: Environment to get servers from (uses current if None)
            
        Returns:
            List[str]: List of server entry points
        """
        env_name = env_name or self._current_env_name
        if not self.environment_exists(env_name):
            raise HatchEnvironmentError(f"Environment {env_name} does not exist")
        
        ep = []
        for pkg in self._environments[env_name].get("packages", []):
            # Open the package's metadata file
            with open(self.environments_dir / env_name / pkg["name"] / "hatch_metadata.json", 'r') as f:
                hatch_metadata = json.load(f)

            # retrieve entry points
            ep += [(self.environments_dir / env_name / pkg["name"] / hatch_metadata.get("entry_point")).resolve()]

        return ep

    def refresh_registry(self, force_refresh: bool = True) -> None:
        """Refresh the registry data from the source.
        
        This method forces a refresh of the registry data to ensure the environment manager
        has the most recent package information available. After refreshing, it updates the
        orchestrator and associated services to use the new registry data.
        
        Args:
            force_refresh (bool, optional): Force refresh the registry even if cache is valid.
                When True, bypasses all caching mechanisms and fetches directly from source.
                Defaults to True.
                
        Raises:
            Exception: If fetching the registry data fails for any reason.
        """
        self.logger.info("Refreshing registry data...")
        try:
            self.registry_data = self.retriever.get_registry(force_refresh=force_refresh)
            # Update registry service with new registry data
            self.registry_service = RegistryService(self.registry_data)
            
            # Update orchestrator with new registry data
            self.dependency_orchestrator.registry_service = self.registry_service
            self.dependency_orchestrator.registry_data = self.registry_data
            
            self.logger.info("Registry data refreshed successfully")
        except Exception as e:
            self.logger.error(f"Failed to refresh registry data: {e}")
            raise