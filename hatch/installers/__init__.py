"""Installer framework for Hatch dependency management.

This package provides a robust, extensible installer interface and concrete
implementations for different dependency types including Hatch packages,
Python packages, system packages, and Docker containers.
"""

from .installer_base import DependencyInstaller, InstallationError, InstallationContext
from .registry import InstallerRegistry, installer_registry

__all__ = [
    "DependencyInstaller",
    "InstallationError", 
    "InstallationContext",
    "InstallerRegistry",
    "installer_registry"
]
