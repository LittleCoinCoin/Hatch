# CI/CD Integration Troubleshooting

This guide helps resolve common issues when using Hatch in Continuous Integration/Continuous Deployment (CI/CD) pipelines and other automated environments.

## Common CI/CD Issues

### Package Installation Hangs in Pipelines

**Problem:** Hatch package installation commands hang indefinitely in CI/CD pipelines, causing builds to timeout.

**Cause:** Hatch prompts for user consent before installing dependencies, but CI/CD environments cannot provide interactive input.

**Solution:** Use one of the following approaches to enable automatic approval:

#### Option 1: Environment Variable (Recommended)
Set the `HATCH_AUTO_APPROVE` environment variable in your CI/CD configuration:

```yaml
# GitHub Actions example
env:
  HATCH_AUTO_APPROVE: "1"

# GitLab CI example
variables:
  HATCH_AUTO_APPROVE: "true"

# Jenkins pipeline example
environment {
  HATCH_AUTO_APPROVE = "yes"
}
```

#### Option 2: CLI Flag
Add the `--auto-approve` flag to your package installation commands:

```bash
hatch package add my_package --auto-approve
hatch package add registry_package --version 1.0.0 --auto-approve
```

#### Option 3: Automatic Detection
Hatch automatically detects non-TTY environments and skips user prompts. This works out-of-the-box in most CI/CD systems without additional configuration.

### Environment Variable Values

The `HATCH_AUTO_APPROVE` environment variable accepts the following values (case-insensitive):
- `1`
- `true` 
- `yes`

Any other value will be ignored, and normal prompting behavior will occur in TTY environments.

## CI/CD Platform Examples

### GitHub Actions

```yaml
name: Build and Test
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      HATCH_AUTO_APPROVE: "1"
    
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install Hatch
      run: pip install hatch
    
    - name: Install dependencies
      run: hatch package add ./my_package
```

### GitLab CI

```yaml
variables:
  HATCH_AUTO_APPROVE: "true"

test:
  image: python:3.9
  script:
    - pip install hatch
    - hatch env create test-env
    - hatch package add ./my_package --env test-env
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any
    environment {
        HATCH_AUTO_APPROVE = "yes"
    }
    stages {
        stage('Install Dependencies') {
            steps {
                sh 'pip install hatch'
                sh 'hatch package add ./my_package'
            }
        }
    }
}
```

### Docker Builds

```dockerfile
FROM python:3.9

# Set environment variable for non-interactive installation
ENV HATCH_AUTO_APPROVE=1

# Install Hatch
RUN pip install hatch

# Copy and install your package
COPY . /app
WORKDIR /app
RUN hatch package add ./my_package
```

## Troubleshooting Steps

If you're still experiencing issues:

1. **Verify Environment Detection:**
   Check if your CI/CD environment is properly detected as non-TTY:
   ```bash
   python -c "import sys; print('TTY:', sys.stdin.isatty())"
   ```
   This should print `TTY: False` in CI/CD environments.

2. **Test Environment Variable:**
   Verify the environment variable is set correctly:
   ```bash
   echo "HATCH_AUTO_APPROVE: $HATCH_AUTO_APPROVE"
   ```

3. **Enable Verbose Logging:**
   Add verbose logging to see what Hatch is doing:
   ```bash
   hatch package add ./my_package --verbose
   ```

4. **Check for Blocking Input:**
   If the process still hangs, check for other interactive prompts in your package installation process.

## Best Practices

1. **Use Environment Variables:** Set `HATCH_AUTO_APPROVE=1` in your CI/CD environment variables for consistent behavior across all commands.

2. **Test Locally:** Test your CI/CD configuration locally using tools like `act` (for GitHub Actions) or Docker to simulate the CI environment.

3. **Timeout Protection:** Set reasonable timeouts in your CI/CD configuration to prevent indefinite hanging:
   ```yaml
   # GitHub Actions
   timeout-minutes: 10
   
   # GitLab CI
   timeout: 10m
   ```

4. **Explicit Dependencies:** Consider using explicit dependency lists in your CI/CD scripts to make builds more predictable and faster.

## Related Documentation

- [CLI Reference - Environment Variables](../CLIReference.md#environment-variables)
- [CLI Reference - Package Add Command](../CLIReference.md#hatch-package-add)
- [Getting Started Guide](../GettingStarted.md)
