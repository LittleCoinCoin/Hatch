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
        cache_ttl: int = 86400,  # Default TTL is 24 hours
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
    
    def get_registry(self, force_refresh: bool = False) -> Dict[str, Any]:
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
            
        # Check if local cache is not outdated and
        if not force_refresh and not self.is_cache_outdated():
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
            # Note that in case of simulation mode AND default cache path,
            # we are rewriting the same file with the same content
            self._write_local_cache(registry_data)
            
            # Update in-memory cache
            self._registry_cache = registry_data
            self._last_fetch_time = current_time
            
            return registry_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch registry: {e}")
            raise e
    
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
    
    def is_cache_outdated(self) -> bool:
        """
        Check if the cached registry is outdated (not from today's UTC date).
        
        Returns:
            bool: True if cache is outdated, False if cache is current
        """
        if not self.registry_cache_path.exists():
            return False
        
        # Get today's date in UTC
        today_utc = datetime.datetime.now(datetime.timezone.utc).date()
        
        # Get cache file's modification date in UTC
        cache_mtime = datetime.datetime.fromtimestamp(
            self.registry_cache_path.stat().st_mtime, 
            tz=datetime.timezone.utc
        ).date()
        
        # Cache is outdated if it's not from today
        return cache_mtime < today_utc

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    retriever = RegistryRetriever()
    registry = retriever.get_registry()
    print(f"Found {len(registry.get('repositories', []))} repositories")
    print(f"Registry last updated: {registry.get('last_updated')}")