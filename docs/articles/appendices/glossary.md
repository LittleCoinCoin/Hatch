# Glossary

This glossary defines terms and concepts used throughout the Hatch documentation.

## A

**Auto-approve**
: CLI flag (`--auto-approve`) that automatically approves dependency installations without user prompts, useful for automation scenarios.

## C

**Cache TTL**
: Time-to-live for cached registry data, configurable via `--cache-ttl` flag. Default is 86400 seconds (24 hours).

**Conda**
: Python package and environment management system used by Hatch for creating isolated Python environments.

**Current Environment**
: The active Hatch environment that commands operate on by default. Set using `hatch env use <name>`.

## D

**Dependency**
: A package or resource required by another package. Hatch supports multiple dependency types: Hatch packages, Python packages, system packages, and Docker images.

**Dependency Installation Orchestrator**
: Component in `hatch/installers/dependency_installation_orchestrator.py` that coordinates the installation of multiple dependency types.

**Docker Dependency**
: A Docker image required by a Hatch package, managed by the Docker installer.

## E

**Entry Point**
: The main file that serves as the executable entry point for a Hatch package, typically `hatch_mcp_server_entry.py`.

**Environment**
: An isolated workspace for managing packages and their dependencies. Hatch environments can optionally include Python environments.

**Environment Manager**
: Core component in `hatch/environment_manager.py` that handles environment lifecycle and management operations.

## F

**FastMCP**
: A Python framework for building Model Context Protocol servers, used as the base for Hatch package MCP server implementations.

**Force Download**
: CLI flag (`--force-download`) that forces package download even if the package is already cached locally.

## G

**Global Options**
: CLI options available for all commands, including `--envs-dir`, `--cache-ttl`, and `--cache-dir`.

## H

**Hatch**
: Package manager for Model Context Protocol (MCP) servers that provides environment isolation and dependency management.

**Hatch Compliant**
: Indicates whether a package follows Hatch packaging standards and metadata requirements.

**Hatch Dependency**
: Another Hatch package required as a dependency, managed by the Hatch installer.

**Hatch Environment**
: An isolated environment managed by Hatch for organizing packages and dependencies.

**Hatch MCP Server Wrapper**
: Integration component (`hatch_mcp_server`) that bridges Hatch packages with MCP server functionality.

**Hatch Package**
: A package that follows Hatch conventions and includes `hatch_metadata.json` with required metadata fields.

**Hatchling**
: Related project in the Hatch ecosystem that provides additional functionality and tooling.

## I

**Installation Context**
: Object that manages state and context information during package installation processes.

**Installer Base**
: Abstract base class in `hatch/installers/installer_base.py` that defines the interface for all installer types.

## M

**Mamba**
: Fast, drop-in replacement for conda package manager. Hatch prefers mamba when available for better performance.

**MCP**
: Model Context Protocol - a standard for building AI-powered tools and integrations.

**MCP Server**
: A server implementation that follows the Model Context Protocol standard, typically providing tools and resources for AI applications.

**Metadata**
: Package information stored in `hatch_metadata.json` that defines package properties, dependencies, and compatibility requirements.

## P

**Package**
: A distributable unit of code that provides MCP server functionality. In Hatch, packages follow specific structure and metadata requirements.

**Package Loader**
: Component in `hatch/package_loader.py` that loads and validates packages from local directories.

**Package Schema Version**
: Version of the metadata schema used by a package, currently "1.2.0".

**Python Dependency**
: A Python package installed via pip, managed by the Python installer.

**Python Environment**
: A conda/mamba environment containing a specific Python version and packages, optionally created within Hatch environments.

**Python Environment Manager**
: Component in `hatch/python_environment_manager.py` that manages Python environments within Hatch environments wrapping around conda/mamba in order to associate python environments with Hatch environments.

## R

**Refresh Registry**
: CLI flag (`--refresh-registry`) that forces refresh of registry data, bypassing cache.

**Registry**
: Central repository for discovering and downloading Hatch packages.

**Registry Explorer**
: Component in `hatch/registry_explorer.py` that provides package discovery and search capabilities.

**Registry Retriever**
: Component in `hatch/registry_retriever.py` that handles package downloads and caching from the registry.

## S

**Schema**
: JSON schema definition that validates package metadata structure. Cracking Shells defines and uses schemas for its package ecosystem. It is hosted on a [dedicated repository](https://github.com/CrackingShells/Hatch-Schemas).

**Semantic Versioning**
: Version numbering scheme using MAJOR.MINOR.PATCH format (e.g., 1.2.0).

**System Dependency**
: A system package installed via OS package managers like apt, managed by the system installer.

## T

**Template Generator**
: Component in `hatch/template_generator.py` that creates new package templates with standard structure and files.

**Tool**
: A function provided by an MCP server package, defined in the package metadata and exposed through the MCP interface.

## V

**Validation**
: Process of checking package structure and metadata against Hatch requirements and schema definitions.

**Version Constraint**
: Specification of acceptable version ranges for dependencies using operators like `>=`, `==`, `<=`, `!=`.

## W

**Workspace**
: Development environment containing multiple related projects and packages, such as the Hatch multi-project workspace.
