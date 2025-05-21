#!/usr/bin/env python3
import os
import json
import logging
import requests
import hashlib
import time
import datetime  # Add missing import for datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
from urllib.parse import urlparse

class RegistryRetriever:
    """
    Class to retrieve and manage the Hatch package registry.
    Provides caching at file system level and in-memory level.
    Works in both local simulation and online GitHub environments.
    """
    
    def __init__(
        self, 
        cache_ttl: int = 3600,  # 1 hour cache TTL by default
        local_cache_dir: Optional[Path] = None,
        simulation_mode: bool = False,  # Set to True when running in local simulation mode
        local_registry_cache_path: Optional[Path] = None
    ):
        """
        Initialize the registry retriever.
        
        Args:
            local_cache_dir: Directory to store local cache files (default: ~/.hatch, the registry will be in ~/.hatch/registry)
            cache_ttl: Time-to-live for cache in seconds
            simulation_mode: Whether to operate in local simulation mode. Can be useful during development or debugging.
            local_registry_cache_path: Path to local registry file (for simulation mode)
        """
        self.logger = logging.getLogger('hatch.registry_retriever')
        self.cache_ttl = cache_ttl
        self.simulation_mode = simulation_mode
        
        # Initialize cache directory
        self.cache_dir = local_cache_dir or Path.home() / ".hatch"
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Set up registry source based on mode
        if simulation_mode:
            # Local simulation mode - use local registry file
            self.registry_cache_path = local_registry_cache_path or self.cache_dir / "registry" / "hatch_packages_registry.json"
                
            # Use file:// URL format for local files
            self.registry_url = f"file://{str(self.registry_cache_path.absolute())}"
            self.logger.info(f"Operating in simulation mode with registry at: {self.registry_cache_path}")
        else:
            # Online mode - use GitHub URL
            # get UTC date string for the registry
            ydm = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            self.registry_url = f"https://github.com/CrackingShells/Hatch-Registry/releases/download/{ydm}/hatch_packages_registry.json"
            self.logger.info(f"Operating in online mode with registry at: {self.registry_url}")
        
        # Generate cache filename based on URL hash
        self.registry_cache_path = self.cache_dir / "registry" / "hatch_packages_registry.json"
        
        # In-memory cache
        self._registry_cache = None
        self._last_fetch_time = 0
    
    def _is_cache_valid(self) -> bool:
        """Check if the local cache file is valid and not expired."""
        if not self.registry_cache_path.exists():
            return False
            
        # Check file modification time
        mtime = self.registry_cache_path.stat().st_mtime
        if time.time() - mtime > self.cache_ttl:
            return False
            
        return True
    
    def _read_local_cache(self) -> Dict[str, Any]:
        """Read the registry from local cache file."""
        try:
            with open(self.registry_cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.warning(f"Failed to read local cache: {e}")
            return {}
    
    def _write_local_cache(self, registry_data: Dict[str, Any]) -> None:
        """Write the registry data to local cache file."""
        try:
            with open(self.registry_cache_path, 'w') as f:
                json.dump(registry_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write local cache: {e}")
    
    def _fetch_local_registry(self) -> Dict[str, Any]:
        """Fetch registry data from local file (simulation mode)"""
        try:
            if not self.registry_cache_path.exists():
                self.logger.warning(f"Local registry file does not exist: {self.registry_cache_path}")
                return self._get_empty_registry()
            
            with open(self.registry_cache_path, 'r') as f:
                registry_data = json.load(f)
                return registry_data
        except Exception as e:
            self.logger.error(f"Failed to read local registry file: {e}")
            return self._get_empty_registry()
    
    def _fetch_remote_registry(self) -> Dict[str, Any]:
        """Fetch registry data from remote URL (online mode)"""
        try:
            self.logger.info(f"Fetching registry from {self.registry_url}")
            response = requests.get(self.registry_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to fetch remote registry: {e}")
            return self._get_empty_registry()
    
    def _get_empty_registry(self) -> Dict[str, Any]:
        """Return an empty registry template"""
        return {
            "registry_schema_version": "1.0.0",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "artifact_base_url": "https://artifacts.crackingshells.org/packages",
            "repositories": [],
            "stats": {
                "total_packages": 0,
                "total_versions": 0,
                "total_artifacts": 0
            }
        }
    
    def fetch_registry(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch the registry file.
        
        Args:
            force_refresh: Force refresh the registry even if cache is valid
            
        Returns:
            Dict containing the registry data
        """
        current_time = time.time()
        
        # Check if in-memory cache is valid
        if (not force_refresh and 
            self._registry_cache is not None and 
            current_time - self._last_fetch_time < self.cache_ttl):
            self.logger.debug("Using in-memory cache")
            return self._registry_cache
            
        # Check if local cache is valid
        if not force_refresh and self._is_cache_valid():
            self.logger.debug("Using local cache file")
            registry_data = self._read_local_cache()
            
            # Update in-memory cache
            self._registry_cache = registry_data
            self._last_fetch_time = current_time
            
            return registry_data
            
        # Fetch from source based on mode
        try:
            if self.simulation_mode:
                registry_data = self._fetch_local_registry()
            else:
                registry_data = self._fetch_remote_registry()
            
            # Update local cache
            self._write_local_cache(registry_data)
            
            # Update in-memory cache
            self._registry_cache = registry_data
            self._last_fetch_time = current_time
            
            return registry_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch registry: {e}")
            
            # Fallback to local cache if it exists
            if self.registry_cache_path.exists():
                self.logger.warning("Falling back to local cache")
                return self._read_local_cache()
                
            # Return empty registry as last resort
            return self._get_empty_registry()
    
    def get_registry(self) -> Dict[str, Any]:
        """
        Get the registry data, preferably from cache.
        
        Returns:
            Dict containing the registry data
        """
        return self.fetch_registry(force_refresh=False)
    
    def find_package(self, package_name: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Find a package in the registry by name.
        
        Args:
            package_name: Name of the package to find
            
        Returns:
            Tuple of (repository dict, package dict) if found, else (None, None)
        """
        registry = self.get_registry()
        
        for repo in registry.get("repositories", []):
            for pkg in repo.get("packages", []):
                if pkg.get("name") == package_name:
                    return repo, pkg
                    
        return None, None
    
    def get_latest_version(self, package_name: str) -> Optional[str]:
        """
        Get the latest version of a package.
        
        Args:
            package_name: Name of the package
            
        Returns:
            String with latest version or None if not found
        """
        _, package = self.find_package(package_name)
        if package:
            return package.get("latest_version")
        return None
    
    def invalidate_cache(self) -> None:
        """Invalidate both the local file cache and in-memory cache."""
        self._registry_cache = None
        self._last_fetch_time = 0
        
        if self.registry_cache_path.exists():
            try:
                self.registry_cache_path.unlink()
                self.logger.debug("Cache file removed")
            except Exception as e:
                self.logger.error(f"Failed to remove cache file: {e}")

    def get_registry_metadata(self) -> Dict[str, Any]:
        """
        Get lightweight metadata about the registry without downloading the entire registry.
        This can be used to check if a local cache is outdated.
        
        Returns:
            Dict with metadata including:
                - last_updated: timestamp of last registry update
                - version: registry schema version
                - stats: registry statistics
        """
        if self.simulation_mode:
            # In simulation mode, just read the metadata from the local file
            try:
                with open(self.registry_cache_path, 'r') as f:
                    data = json.load(f)
                    return {
                        "last_updated": data.get("last_updated"),
                        "version": data.get("registry_schema_version", "1.0.0"),
                        "stats": data.get("stats", {})
                    }
            except Exception as e:
                self.logger.error(f"Failed to read registry metadata: {e}")
                return {
                    "last_updated": None,
                    "version": None,
                    "stats": {}
                }
        else:
            # In online mode, try to fetch only the metadata via HEAD request
            try:
                response = requests.head(self.registry_url, timeout=10)
                
                # Check if the server provides a last-modified header
                last_modified = response.headers.get('Last-Modified')
                
                if last_modified:
                    return {
                        "last_updated": last_modified,
                        "version": None,  # Can't get this from headers
                        "stats": {}       # Can't get this from headers
                    }
                else:
                    # If no last-modified header, we'll have to fetch the whole registry
                    # but just return the metadata fields
                    registry = self.get_registry()
                    return {
                        "last_updated": registry.get("last_updated"),
                        "version": registry.get("registry_schema_version"),
                        "stats": registry.get("stats", {})
                    }
            except Exception as e:
                self.logger.error(f"Failed to fetch registry metadata: {e}")
                return {
                    "last_updated": None,
                    "version": None,
                    "stats": {}
                }
    
    def is_cache_outdated(self) -> bool:
        """
        Check if the cached registry is outdated compared to the remote/source registry.
        
        Returns:
            bool: True if cache is outdated or couldn't be checked, False if cache is current
        """
        # If cache doesn't exist, it's outdated
        if not self._is_cache_valid():
            return True
            
        try:
            # Get metadata about the source registry
            source_meta = self.get_registry_metadata()
            source_last_updated = source_meta.get("last_updated")
            
            if not source_last_updated:
                # If we couldn't get the source last updated time, assume outdated
                return True
                
            # Load cache metadata
            cache_data = self._read_local_cache()
            cache_last_updated = cache_data.get("last_updated")
            
            if not cache_last_updated:
                return True
                
            # Parse timestamps and compare
            try:
                # Handle different timestamp formats
                if 'T' in source_last_updated:
                    source_time = datetime.datetime.fromisoformat(source_last_updated.replace('Z', '+00:00'))
                else:
                    source_time = datetime.datetime.strptime(source_last_updated, "%a, %d %b %Y %H:%M:%S %Z")
                    
                if 'T' in cache_last_updated:
                    cache_time = datetime.datetime.fromisoformat(cache_last_updated.replace('Z', '+00:00'))
                else:
                    cache_time = datetime.datetime.strptime(cache_last_updated, "%a, %d %b %Y %H:%M:%S %Z")
                
                return source_time > cache_time
            except (ValueError, TypeError) as e:
                self.logger.warning(f"Error parsing timestamps: {e}")
                return True  # Assume outdated if we can't parse dates
                
        except Exception as e:
            self.logger.error(f"Error checking if cache is outdated: {e}")
            return True  # Assume outdated on error

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = RegistryRetriever()
    registry = retriever.get_registry()
    print(f"Found {len(registry.get('repositories', []))} repositories")
    print(f"Registry last updated: {registry.get('last_updated')}")