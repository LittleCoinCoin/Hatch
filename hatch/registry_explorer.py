"""
Utilities for exploring a Hatch package registry (see hatch_all_pkg_metadata_schema.json).
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet, InvalidSpecifier

def find_repository(registry: Dict[str, Any], repo_name: str) -> Optional[Dict[str, Any]]:
    """
    Find a repository by name.
    """
    for repo in registry.get("repositories", []):
        if repo.get("name") == repo_name:
            return repo
    return None

def list_repositories(registry: Dict[str, Any]) -> List[str]:
    """
    List all repository names in the registry.
    """
    return [repo.get("name") for repo in registry.get("repositories", [])]

def find_package(registry: Dict[str, Any], package_name: str, repo_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a package by name, optionally within a specific repository.
    """
    repos = registry.get("repositories", [])
    if repo_name:
        repos = [r for r in repos if r.get("name") == repo_name]
    for repo in repos:
        for pkg in repo.get("packages", []):
            if pkg.get("name") == package_name:
                return pkg
    return None

def list_packages(registry: Dict[str, Any], repo_name: Optional[str] = None) -> List[str]:
    """
    List all package names, optionally within a specific repository.
    """
    packages = []
    repos = registry.get("repositories", [])
    if repo_name:
        repos = [r for r in repos if r.get("name") == repo_name]
    for repo in repos:
        for pkg in repo.get("packages", []):
            packages.append(pkg.get("name"))
    return packages

def get_latest_version(pkg: Dict[str, Any]) -> Optional[str]:
    """
    Get the latest version string for a package dict.
    """
    return pkg.get("latest_version")

def _match_version_constraint(version: str, constraint: str) -> bool:
    """
    Check if a version string matches a constraint (e.g., '>=1.2.0').
    Uses the 'packaging' library for robust version comparison.
    If a simple version like "1.0.0" is passed as constraint, it's treated as "==1.0.0".
    """
    try:
        v = Version(version)
        
        # Convert the constraint to a proper SpecifierSet if it doesn't have an operator
        if constraint and not any(constraint.startswith(op) for op in ['==', '!=', '<=', '>=', '<', '>']):
            constraint = f"=={constraint}"
            
        # Accept constraints like '==1.2.3', '>=1.0.0', etc.
        spec = SpecifierSet(constraint)
        return v in spec
    except (InvalidVersion, InvalidSpecifier):
        # If we can't parse versions, fall back to string comparison
        return version == constraint

def find_package_version(pkg: Dict[str, Any], version_constraint: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Find a version dict for a package, optionally matching a version constraint.
    If no constraint is given, returns the latest version.
    """
    versions = pkg.get("versions", [])
    if not versions:
        return None
    if not version_constraint:
        # Return the version dict matching latest_version
        latest = pkg.get("latest_version")
        for v in versions:
            if v.get("version") == latest:
                return v
        # fallback: return the highest version
        try:
            return max(versions, key=lambda x: Version(x.get("version", "0")))
        except Exception:
            return versions[-1]    # Try to find a version matching the constraint
    try:
        sorted_versions = sorted(versions, key=lambda x: Version(x.get("version", "0")), reverse=True)
    except Exception:
         sorted_versions = versions
        
    # # First, try to find an exact version match
    # for v in sorted_versions:
    #     if v.get("version") == version_constraint:
    #         return v
    
    # If no exact match, try parsing as a constraint
    for v in sorted_versions:
        if _match_version_constraint(v.get("version", ""), version_constraint):
            return v
    return None

def get_package_release_url(pkg: Dict[str, Any], version_constraint: Optional[str] = None) -> Optional[str]:
    """
    Get the release URI for a package version matching the constraint (or latest).
    """
    if pkg is None:
        return None
        
    vdict = find_package_version(pkg, version_constraint)
    if vdict:
        return vdict.get("release_uri")
    return None
