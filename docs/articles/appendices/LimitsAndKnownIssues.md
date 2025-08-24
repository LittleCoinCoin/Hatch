# Limits and Known Issues

This appendix documents current limitations and known issues in Hatch v0.4.2, organized by impact severity and architectural domain.

## Critical Limitations (High Impact)

### Non-Interactive Environment Handling

**Issue**: The dependency installation orchestrator can block indefinitely in non-TTY environments.

**Code Location**: `hatch/installers/dependency_installation_orchestrator.py:501` (`_request_user_consent`)

**Symptoms**:

- Hangs in CI/CD pipelines when TTY is unavailable
- Docker container execution may hang indefinitely
- Programmatic integration requires foreknowledge of `--auto-approve` parameter

**Workaround**: Use `--auto-approve` flag for automated scenarios

```bash
hatch package add my-package --auto-approve
```

**Root Cause**: Blocking `input()` call without TTY detection or environment variable fallback mechanisms.

### System Package Version Constraint Simplification

**Issue**: Complex version constraints for system packages are reduced to "install latest" with only warning messages.

**Code Location**: `hatch/installers/system_installer.py:332-365` (`_build_apt_command`)

**Symptoms**:

- Version constraint `>=1.2.0` becomes "install latest"
- No validation that installed version satisfies original constraint
- Silent constraint violations in production environments

**Workaround**: Use exact version constraints (`==1.2.0`) for critical system dependencies

**Root Cause**: Simplified apt command building that only handles exact version matching.

### Concurrent Access Race Conditions

**Issue**: Plain file I/O operations without atomic writes or file locking can lead to corrupted state.

**Code Locations**:

- `hatch/environment_manager.py:85-90`
- `hatch/package_loader.py:80-85`

**Symptoms**:

- Corrupted `environments.json` when multiple Hatch instances run
- Package cache corruption during concurrent downloads
- Lost environment configuration in multi-user scenarios

**Workaround**: Avoid running multiple Hatch operations simultaneously

**Root Cause**: Non-atomic file operations for critical state files.

## Significant Limitations (Medium Impact)

### Registry Fetch Fragility

**Issue**: Registry fetching uses date-based URL construction with limited fallback robustness.

**Code Location**: `hatch/registry_retriever.py:45-65`

**Symptoms**:

- Package discovery breaks when registry publishing is delayed
- Poor error messages during network connectivity issues
- Development workflow disruption during registry maintenance

**Workaround**: Use local packages (`hatch package add ./local-package`) when registry is unavailable

**Root Cause**: Registry URL construction assumes daily publishing schedule without robust fallback strategies.

### Package Integrity Verification Gap

**Issue**: Downloaded packages are not cryptographically verified for integrity.

**Code Location**: `hatch/package_loader.py:75-125` (`download_package`)

**Symptoms**:

- No detection of package tampering in hostile networks
- Corrupted downloads may be interpreted as valid packages
- No audit trail for package provenance

**Workaround**: Manually verify package sources and use trusted networks

**Root Cause**: Missing checksum validation and signature verification during package download.

### Cross-Platform Python Environment Detection

**Issue**: Hard-coded path assumptions limit Python environment detection across different platforms and installations.

**Code Location**: `hatch/python_environment_manager.py:85-120` (`_detect_conda_mamba`)

**Symptoms**:

- Inconsistent behavior across different conda installations
- Silent feature degradation when Python environments unavailable
- User confusion about Python integration capabilities

**Workaround**: Ensure conda/mamba are in system PATH or use explicit paths

**Root Cause**: Platform-specific path assumptions and limited environment variable checking.

### Error Recovery and Rollback Gaps

**Issue**: Limited transactional semantics during multi-dependency installation.

**Code Location**: `hatch/installers/dependency_installation_orchestrator.py:550-580` (`_execute_install_plan`)

**Symptoms**:

- Environments left in inconsistent states after failed installs
- Manual cleanup required for partial installation failures
- Difficult recovery from complex dependency conflicts

**Workaround**: Create environment snapshots before major installations; remove and recreate environments if corrupted

**Root Cause**: Sequential installation without comprehensive rollback mechanisms.

## Moderate Limitations (Development Impact)

### Limited Observability and Progress Reporting

**Issue**: Minimal structured logging and progress feedback during operations. Typically intermediate installation steps rely on the individual installer's (i.e. pip, apt, etc.), but orchestrator lacks end-to-end visibility.

**Code Locations**: Logging scattered across multiple modules

**Symptoms**:

- Difficult debugging of installation failures
- Poor user experience during long-running operations
- Limited integration with monitoring systems

**Workaround**: Increase logging verbosity and monitor log files

**Root Cause**: Progress callbacks exist but are sparsely implemented across the codebase.

### Template Generation Assumptions

**Issue**: Templates assume specific MCP server structure and dependencies.

**Code Location**: `hatch/template_generator.py:130-140`

**Symptoms**:

- Template lock-in for specific MCP server patterns
- Reduced flexibility for alternative MCP frameworks
- Potential incompatibility with future MCP specifications

**Workaround**: Manually modify generated templates for custom requirements

**Root Cause**: Hard-coded assumptions about entry points and MCP wrapper dependencies.

### Dependency Graph Resolution Edge Cases

**Issue**: Limited handling of circular dependencies and complex version constraints.

**Code Location**: `hatch/installers/dependency_installation_orchestrator.py:290-320`

**Symptoms**:

- Potential infinite loops during dependency resolution
- Unclear error messages for complex dependency conflicts
- Unexpected behavior with deeply nested dependency trees

**Workaround**: Simplify dependency structures and avoid circular dependencies

**Root Cause**: Dependency graph builder lacks edge case handling for complex scenarios.

## Minor Limitations (Quality of Life)

### Security Context Management

**Issue**: System package installation assumes `sudo` availability without proper validation.

**Code Location**: `hatch/installers/system_installer.py:365-380`

**Symptoms**:

- Poor error messages when privilege escalation fails
- No pre-validation of system package manager availability

**Workaround**: Ensure proper sudo configuration and system package manager access

### Simulation and Dry-Run Gaps

**Issue**: Inconsistent simulation mode implementation across installers.

**Code Locations**: Various installer modules

**Symptoms**:

- No unified dry-run capability across all dependency types
- Limited preview capabilities for complex installation plans

**Workaround**: Test installations in isolated environments first

### Cache Management Strategy

**Issue**: Basic TTL-based caching without intelligent invalidation or size limits.

**Code Locations**:

- `hatch/package_loader.py:40-50`
- `hatch/registry_retriever.py:35-45`

**Symptoms**:

- Fixed 24-hour TTL regardless of registry update frequency
- No automatic cache cleanup for disk space management
- Force refresh only available at operation level

**Workaround**: Manually clear cache directory when needed:

```bash
rm -rf ~/.hatch/cache/*
```

### External Dependency Coupling

**Issue**: Validator dependency fetched via git URL with network requirements.

**Code Location**: `pyproject.toml:24`

**Details**: `hatch_validator @ git+https://github.com/CrackingShells/Hatch-Validator.git@v0.6.3`

**Symptoms**:

- Build-time network access required
- Dependency on repository and tag availability

**Workaround**: Ensure network access during installation or consider local installation methods

### Documentation and Schema Evolution

**Issue**: Limited handling of package schema version transitions.

**Code Locations**: Template generation and package validation flows

**Symptoms**:

- Templates generate current schema version only
- No migration tools for package schema updates
- Version compatibility checking incomplete

**Workaround**: Manually update package metadata when schema versions change

## Impact Classification

| Severity | Automation | Reliability | Development |
|----------|------------|-------------|-------------|
| **Critical** | Non-interactive handling | Concurrent access, System constraints | - |
| **Significant** | Registry fragility, Error recovery | Package integrity, Python detection | - |
| **Moderate** | - | - | Observability, Templates, Dependency resolution |
| **Minor** | Simulation gaps | Security context, Cache strategy | External coupling, Schema evolution |

## Recommended Mitigation Strategies

### For Production Use

1. **Always use `--auto-approve`** for automated deployments
2. **Avoid concurrent operations** until race conditions are resolved
3. **Use exact version constraints** for system packages when possible
4. **Implement external monitoring** for installation operations
5. **Regularly backup environment configurations**

### For Development

1. **Test in isolated environments** before production deployment
2. **Monitor cache disk usage** and clean manually when needed
3. **Use local packages** when registry is unreliable
4. **Simplify dependency structures** to avoid resolution edge cases

### For Cross-Platform Deployment

1. **Ensure conda/mamba in PATH** on all target systems
2. **Test Python environment detection** on each platform
3. **Validate system package managers** before deployment
4. **Document platform-specific requirements**

## Future Improvements

The Hatch team is aware of these limitations and they are prioritized for future releases:

**Phase 1 (Stability)**: Address concurrent access, non-interactive handling, and error recovery
**Phase 2 (Security)**: Implement package integrity verification and security context validation
**Phase 3 (Robustness)**: Improve cross-platform consistency and system package handling
**Phase 4 (Quality)**: Enhance observability, caching, and template flexibility

For the most current status of these issues, check the project's issue tracker and release notes.
