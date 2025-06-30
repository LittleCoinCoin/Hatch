"""Python Environment Manager for cross-platform conda/mamba environment management.

This module provides the core functionality for managing Python environments using
conda/mamba, with support for local installation under Hatch environment directories
and cross-platform compatibility.
"""

import json
import logging
import platform
import shutil
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class PythonEnvironmentError(Exception):
    """Exception raised for Python environment-related errors."""
    pass


class PythonEnvironmentManager:
    """Manages Python environments using conda/mamba for cross-platform isolation.
    
    This class handles:
    1. Creating and managing conda/mamba environments locally under Hatch environment directories
    2. Python version management and executable path resolution
    3. Cross-platform conda/mamba detection and validation
    4. Environment lifecycle operations (create, remove, info)
    5. Integration with InstallationContext for Python executable configuration
    """
    
    def __init__(self, environments_dir: Optional[Path] = None):
        """Initialize the Python environment manager.
        
        Args:
            environments_dir (Path, optional): Directory where Hatch environments are stored.
                Defaults to ~/.hatch/envs.
        """
        self.logger = logging.getLogger("hatch.python_environment_manager")
        self.logger.setLevel(logging.DEBUG)
        
        # Set up environment directories
        self.environments_dir = environments_dir or (Path.home() / ".hatch" / "envs")
        
        # Detect available conda/mamba
        self.conda_executable = None
        self.mamba_executable = None
        self._detect_conda_mamba()
        
        self.logger.info(f"Python environment manager initialized with environments_dir: {self.environments_dir}")
        if self.mamba_executable:
            self.logger.info(f"Using mamba: {self.mamba_executable}")
        elif self.conda_executable:
            self.logger.info(f"Using conda: {self.conda_executable}")
        else:
            self.logger.warning("Neither conda nor mamba found - Python environment management will be limited")

    def _detect_manager(self, manager: str) -> Optional[str]:
        """Detect the given manager ('mamba' or 'conda') executable on the system.

        This function searches for the specified package manager in common installation paths
        and checks if it is executable.

        Args:
            manager (str): The name of the package manager to detect ('mamba' or 'conda').

        Returns:
            Optional[str]: The path to the detected executable, or None if not found.
        """
        def find_in_common_paths(names):
            paths = []
            if platform.system() == "Windows":
                candidates = [
                    os.path.expandvars(r"%USERPROFILE%\miniconda3\Scripts"),
                    os.path.expandvars(r"%USERPROFILE%\Anaconda3\Scripts"),
                    r"C:\ProgramData\miniconda3\Scripts",
                    r"C:\ProgramData\Anaconda3\Scripts",
                ]
            else:
                candidates = [
                    os.path.expanduser("~/miniconda3/bin"),
                    os.path.expanduser("~/anaconda3/bin"),
                    "/opt/conda/bin",
                ]
            for base in candidates:
                for name in names:
                    exe = os.path.join(base, name)
                    if os.path.isfile(exe) and os.access(exe, os.X_OK):
                        paths.append(exe)
            return paths

        if platform.system() == "Windows":
            exe_name = f"{manager}.exe"
        else:
            exe_name = manager

        # Try environment variable first
        env_var = os.environ.get(f"{manager.upper()}_EXE")
        paths = [env_var] if env_var else []
        paths += [shutil.which(exe_name)]
        paths += find_in_common_paths([exe_name])
        paths = [p for p in paths if p]

        for path in paths:
            self.logger.debug(f"Trying to detect {manager} at: {path}")
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.logger.debug(f"Detected {manager} at: {path}")
                    return path
            except Exception as e:
                self.logger.warning(f"{manager.capitalize()} not found or not working at {path}: {e}")
        return None

    def _detect_conda_mamba(self) -> None:
        """Detect available conda/mamba executables on the system.

        Tries to find mamba first (preferred), then conda as fallback.
        Sets self.mamba_executable and self.conda_executable based on availability.
        """
        self.mamba_executable = self._detect_manager("mamba")
        self.conda_executable = self._detect_manager("conda")

    # def _validate_conda_installation(self) -> bool:
    #     """Validate that conda/mamba installation is functional.
        
    #     Returns:
    #         bool: True if conda or mamba is available and functional, False otherwise.
    #     """
    #     if not (self.conda_executable or self.mamba_executable):
    #         return False
        
    #     # Use mamba if available, otherwise conda
    #     executable = self.get_preferred_executable()
        
    #     try:
    #         # Test basic functionality
    #         result = subprocess.run(
    #             [executable, "info", "--json"], 
    #             capture_output=True, 
    #             text=True, 
    #             timeout=30
    #         )
    #         if result.returncode == 0:
    #             # Try to parse the JSON to ensure it's valid
    #             json.loads(result.stdout)
    #             return True
    #     except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
    #         self.logger.error(f"Failed to validate conda/mamba installation: {result.stderr if 'result' in locals() else 'Unknown error'}")
    #     except Exception as e:
    #         self.logger.error(f"Unexpected error validating conda/mamba installation: {e}")

    #     self.logger.error("Conda/mamba installation validation failed")
    #     return False

    def is_available(self) -> bool:
        """Check if Python environment management is available.
        
        Returns:
            bool: True if conda/mamba is available and functional, False otherwise.
        """
        if self.get_preferred_executable():
            return True
        return False

    def get_preferred_executable(self) -> Optional[str]:
        """Get the preferred conda/mamba executable.
        
        Returns:
            str: Path to mamba (preferred) or conda executable, None if neither available.
        """
        return self.mamba_executable or self.conda_executable

    def _get_conda_env_name(self, env_name: str) -> str:
        """Get the conda environment name for a Hatch environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            str: Conda environment name following the hatch_<env_name> pattern.
        """
        return f"hatch_{env_name}"

    def _get_conda_env_prefix(self, env_name: str) -> Path:
        """Get the local conda environment prefix path.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            Path: Local path where the conda environment should be installed.
        """
        return self.environments_dir / env_name / "python_env"

    def create_python_environment(self, env_name: str, python_version: Optional[str] = None, 
                                 force: bool = False) -> bool:
        """Create a Python environment using conda/mamba.
        
        Creates a conda environment locally under the Hatch environment directory
        with the specified Python version.
        
        Args:
            env_name (str): Hatch environment name.
            python_version (str, optional): Python version to install (e.g., "3.11", "3.12").
                If None, uses the default Python version from conda.
            force (bool, optional): Whether to force recreation if environment exists.
                Defaults to False.
                
        Returns:
            bool: True if environment was created successfully, False otherwise.
            
        Raises:
            PythonEnvironmentError: If conda/mamba is not available or creation fails.
        """
        if not self.is_available():
            raise PythonEnvironmentError("Neither conda nor mamba is available for Python environment management")
        
        executable = self.get_preferred_executable()
        env_prefix = self._get_conda_env_prefix(env_name)
        
        # Check if environment already exists
        if self._conda_env_exists(env_name) and not force:
            self.logger.warning(f"Python environment already exists for {env_name}")
            return True
        
        # Remove existing environment if force is True
        if force and self._conda_env_exists(env_name):
            self.logger.info(f"Removing existing Python environment for {env_name}")
            self.remove_python_environment(env_name)
        
        # Build conda create command
        cmd = [executable, "create", "--yes", "--prefix", str(env_prefix)]
        
        if python_version:
            cmd.extend(["python=" + python_version])
        else:
            cmd.append("python")
        
        try:
            self.logger.info(f"Creating Python environment for {env_name} at {env_prefix}")
            if python_version:
                self.logger.info(f"Using Python version: {python_version}")
            
            result = subprocess.run(
                cmd,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully created Python environment for {env_name}")
                return True
            else:
                error_msg = f"Failed to create Python environment (see terminal output)"
                self.logger.error(error_msg)
                raise PythonEnvironmentError(error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout creating Python environment for {env_name}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error creating Python environment: {e}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)

    def _conda_env_exists(self, env_name: str) -> bool:
        """Check if a conda environment exists for the given Hatch environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            bool: True if the conda environment exists, False otherwise.
        """
        env_prefix = self._get_conda_env_prefix(env_name)
        python_executable = self._get_python_executable_path(env_name)
        
        # Check if the environment directory and Python executable exist
        return env_prefix.exists() and python_executable.exists()

    def _get_python_executable_path(self, env_name: str) -> Path:
        """Get the Python executable path for a given environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            Path: Path to the Python executable in the environment.
        """
        env_prefix = self._get_conda_env_prefix(env_name)
        
        if platform.system() == "Windows":
            return env_prefix / "python.exe"
        else:
            return env_prefix / "bin" / "python"

    def get_python_executable(self, env_name: str) -> Optional[str]:
        """Get the Python executable path for an environment if it exists.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            str: Path to Python executable if environment exists, None otherwise.
        """
        if not self._conda_env_exists(env_name):
            return None
        
        python_path = self._get_python_executable_path(env_name)
        return str(python_path) if python_path.exists() else None

    def remove_python_environment(self, env_name: str) -> bool:
        """Remove a Python environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            bool: True if environment was removed successfully, False otherwise.
            
        Raises:
            PythonEnvironmentError: If conda/mamba is not available or removal fails.
        """
        if not self.is_available():
            raise PythonEnvironmentError("Neither conda nor mamba is available for Python environment management")
        
        if not self._conda_env_exists(env_name):
            self.logger.warning(f"Python environment does not exist for {env_name}")
            return True
        
        executable = self.get_preferred_executable()
        env_prefix = self._get_conda_env_prefix(env_name)
        
        try:
            self.logger.info(f"Removing Python environment for {env_name}")
            
            # Use conda/mamba remove with --prefix
            # Show output in terminal by not capturing output
            result = subprocess.run(
                [executable, "env", "remove", "--yes", "--prefix", str(env_prefix)],
                timeout=120  # 2 minutes timeout
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully removed Python environment for {env_name}")
                
                # Clean up any remaining directory structure
                if env_prefix.exists():
                    try:
                        shutil.rmtree(env_prefix)
                    except OSError as e:
                        self.logger.warning(f"Could not fully clean up environment directory: {e}")
                
                return True
            else:
                error_msg = f"Failed to remove Python environment: (see terminal output)"
                self.logger.error(error_msg)
                raise PythonEnvironmentError(error_msg)
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout removing Python environment for {env_name}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error removing Python environment: {e}"
            self.logger.error(error_msg)
            raise PythonEnvironmentError(error_msg)

    def get_environment_info(self, env_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a Python environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            dict: Environment information including Python version, packages, etc.
                  None if environment doesn't exist.
        """
        if not self._conda_env_exists(env_name):
            return None
        
        executable = self.get_preferred_executable()
        env_prefix = self._get_conda_env_prefix(env_name)
        python_executable = self._get_python_executable_path(env_name)
        
        info = {
            "environment_name": env_name,
            "conda_env_name": self._get_conda_env_name(env_name),
            "environment_path": str(env_prefix),
            "python_executable": str(python_executable),
            "python_version": self.get_python_version(env_name),
            "exists": True,
            "platform": platform.system()
        }
        
        # Get conda environment info
        if self.is_available():
            try:
                result = subprocess.run(
                    [executable, "list", "--prefix", str(env_prefix), "--json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    packages = json.loads(result.stdout)
                    info["packages"] = packages
                    info["package_count"] = len(packages)
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError):
                info["packages"] = []
                info["package_count"] = 0
        
        return info

    def list_environments(self) -> List[str]:
        """List all Python environments managed by this manager.
        
        Returns:
            list: List of environment names that have Python environments.
        """
        environments = []
        
        if not self.environments_dir.exists():
            return environments
        
        for env_dir in self.environments_dir.iterdir():
            if env_dir.is_dir():
                env_name = env_dir.name
                if self._conda_env_exists(env_name):
                    environments.append(env_name)
        
        return environments

    def get_python_version(self, env_name: str) -> Optional[str]:
        """Get the Python version for an environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            str: Python version if environment exists, None otherwise.
        """
        python_executable = self.get_python_executable(env_name)
        if not python_executable:
            return None
        
        try:
            result = subprocess.run(
                [python_executable, "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Parse version from "Python X.Y.Z" format
                version_line = result.stdout.strip()
                if version_line.startswith("Python "):
                    return version_line[7:]  # Remove "Python " prefix
                return version_line
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        
        return None

    def activate_environment(self, env_name: str) -> Optional[Dict[str, str]]:
        """Get environment variables needed to activate a Python environment.
        
        This method returns the environment variables that should be set
        to properly activate the Python environment, but doesn't actually
        modify the current process environment.
        
        Args:
            env_name (str): Hatch environment name.
            
        Returns:
            dict: Environment variables to set for activation, None if env doesn't exist.
        """
        if not self._conda_env_exists(env_name):
            return None
        
        env_prefix = self._get_conda_env_prefix(env_name)
        python_executable = self._get_python_executable_path(env_name)
        
        env_vars = {}
        
        # Set CONDA_PREFIX and CONDA_DEFAULT_ENV
        env_vars["CONDA_PREFIX"] = str(env_prefix)
        env_vars["CONDA_DEFAULT_ENV"] = str(env_prefix)
        
        # Update PATH to include environment's bin/Scripts directory
        if platform.system() == "Windows":
            scripts_dir = env_prefix / "Scripts"
            library_bin = env_prefix / "Library" / "bin"
            bin_paths = [str(env_prefix), str(scripts_dir), str(library_bin)]
        else:
            bin_dir = env_prefix / "bin"
            bin_paths = [str(bin_dir)]
        
        # Get current PATH and prepend environment paths
        current_path = os.environ.get("PATH", "")
        new_path = os.pathsep.join(bin_paths + [current_path])
        env_vars["PATH"] = new_path
        
        # Set PYTHON environment variable
        env_vars["PYTHON"] = str(python_executable)
        
        return env_vars

    def get_manager_info(self) -> Dict[str, Any]:
        """Get information about the Python environment manager capabilities.
        
        Returns:
            dict: Manager information including available executables and status.
        """
        return {
            "conda_executable": self.conda_executable,
            "mamba_executable": self.mamba_executable,
            "preferred_manager": self.mamba_executable if self.mamba_executable else self.conda_executable,
            "is_available": self.is_available(),
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
    
    def get_environment_diagnostics(self, env_name: str) -> Dict[str, Any]:
        """Get detailed diagnostics for a specific Python environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            dict: Detailed diagnostics information.
        """
        diagnostics = {
            "environment_name": env_name,
            "conda_env_name": f"hatch-{env_name}",
            "exists": False,
            "conda_available": self.is_available(),
            "manager_executable": self.mamba_executable or self.conda_executable,
            "platform": platform.system()
        }
        
        # Check if environment exists
        if self.environment_exists(env_name):
            diagnostics["exists"] = True
            
            # Get Python executable
            python_exec = self.get_python_executable(env_name)
            diagnostics["python_executable"] = python_exec
            diagnostics["python_accessible"] = python_exec is not None
            
            # Get Python version
            if python_exec:
                python_version = self.get_python_version(env_name)
                diagnostics["python_version"] = python_version
                diagnostics["python_version_accessible"] = python_version is not None
                
                # Check if executable actually works
                try:
                    result = subprocess.run(
                        [python_exec, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    diagnostics["python_executable_works"] = result.returncode == 0
                    diagnostics["python_version_output"] = result.stdout.strip()
                except Exception as e:
                    diagnostics["python_executable_works"] = False
                    diagnostics["python_executable_error"] = str(e)
            
            # Get environment path
            env_path = self.get_environment_path(env_name)
            diagnostics["environment_path"] = str(env_path) if env_path else None
            diagnostics["environment_path_exists"] = env_path.exists() if env_path else False
            
        return diagnostics
    
    def get_manager_diagnostics(self) -> Dict[str, Any]:
        """Get general diagnostics for the Python environment manager.
        
        Returns:
            dict: General manager diagnostics.
        """
        diagnostics = {
            "conda_executable": self.conda_executable,
            "mamba_executable": self.mamba_executable,
            "conda_available": self.conda_executable is not None,
            "mamba_available": self.mamba_executable is not None,
            "any_manager_available": self.is_available(),
            "preferred_manager": self.mamba_executable if self.mamba_executable else self.conda_executable,
            "platform": platform.system(),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "environments_dir": str(self.environments_dir)
        }
        
        # Test conda/mamba executables
        for manager_name, executable in [("conda", self.conda_executable), ("mamba", self.mamba_executable)]:
            if executable:
                try:
                    result = subprocess.run(
                        [executable, "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    diagnostics[f"{manager_name}_works"] = result.returncode == 0
                    diagnostics[f"{manager_name}_version"] = result.stdout.strip()
                except Exception as e:
                    diagnostics[f"{manager_name}_works"] = False
                    diagnostics[f"{manager_name}_error"] = str(e)
        
        return diagnostics
    
    def launch_shell(self, env_name: str, cmd: Optional[str] = None) -> bool:
        """Launch a Python shell or execute a command in the environment.
        
        Args:
            env_name (str): Environment name.
            cmd (str, optional): Command to execute. If None, launches interactive shell.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.environment_exists(env_name):
            self.logger.error(f"Environment {env_name} does not exist")
            return False
        
        python_exec = self.get_python_executable(env_name)
        if not python_exec:
            self.logger.error(f"Python executable not found for environment {env_name}")
            return False
        
        try:
            if cmd:
                # Execute specific command
                self.logger.info(f"Executing command in {env_name}: {cmd}")
                result = subprocess.run(
                    [python_exec, "-c", cmd],
                    cwd=os.getcwd()
                )
                return result.returncode == 0
            else:
                # Launch interactive shell
                self.logger.info(f"Launching Python shell for environment {env_name}")
                self.logger.info(f"Python executable: {python_exec}")
                
                # On Windows, we need to activate the conda environment first
                if platform.system() == "Windows":
                    activate_cmd = f"{self.get_preferred_executable()} activate {self._get_conda_env_prefix(env_name)} && python"
                    result = subprocess.run(
                        ["cmd", "/c", activate_cmd],
                        cwd=os.getcwd()
                    )
                else:
                    # On Unix-like systems, we can directly use the Python executable
                    result = subprocess.run(
                        [python_exec],
                        cwd=os.getcwd()
                    )
                
                return result.returncode == 0
                
        except Exception as e:
            self.logger.error(f"Failed to launch shell for {env_name}: {e}")
            return False

    def environment_exists(self, env_name: str) -> bool:
        """Check if a Python environment exists.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            bool: True if environment exists, False otherwise.
        """
        return self._conda_env_exists(env_name)
    
    def get_environment_path(self, env_name: str) -> Optional[Path]:
        """Get the file system path for a Python environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            Path: Environment path or None if not found.
        """
        if not self.environment_exists(env_name):
            return None
            
        return self._get_conda_env_prefix(env_name)
        """Check if a Python environment exists.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            bool: True if environment exists, False otherwise.
        """
        return self._conda_env_exists(env_name)
    
    def get_environment_path(self, env_name: str) -> Optional[Path]:
        """Get the file system path for a Python environment.
        
        Args:
            env_name (str): Environment name.
            
        Returns:
            Path: Environment path or None if not found.
        """
        if not self.environment_exists(env_name):
            return None
            
        return self._get_conda_env_prefix(env_name)
