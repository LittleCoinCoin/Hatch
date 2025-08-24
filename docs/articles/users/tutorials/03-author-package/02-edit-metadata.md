# 02: Edit Metadata

---
**Concepts covered:**

- Hatch package metadata schema structure and validation
- Required and optional metadata fields
- Dependency specification and compatibility constraints
- Package versioning and licensing

**Skills you will practice:**

- Editing the hatch_metadata.json file
- Understanding schema validation requirements
- Configuring dependencies and compatibility settings
- Setting up proper package metadata for distribution

---

This article covers editing the `hatch_metadata.json` file that defines your package's metadata and dependencies.

## Understanding the Metadata Schema

The `hatch_metadata.json` file follows the schema defined in `Hatch-Schemas/package/v1.2.0/hatch_pkg_metadata_schema.json`.

The package's metadata are not critical to the package's functionality but are critical to its distribution and installation by the Hatch ecosystem. For example, [dependencies](#step-3-define-dependencies) information are leveraged during the package's installation to automatically resolve and install any required dependencies. The list of [tools](#step-5-define-tools-and-citations) your package provides is used during package submission to the online registry to confirm the content of your mcp server. Except these, the metadata are not used at runtime simply helps providing information to users and transparency to the community.

## Step 1: Required Fields

Every package must include these fields:

```json
{
  "package_schema_version": "1.2.0",
  "name": "package_name",
  "version": "0.1.0", 
  "entry_point": "hatch_mcp_server_entry.py",
  "description": "Package description",
  "tags": [],
  "author": {
    "name": "Author Name"
  },
  "license": {
    "name": "MIT"
  }
}
```

## Step 2: Configure Package Information

Edit the basic package information:

```json
{
  "package_schema_version": "1.2.0",
  "name": "my_awesome_package",
  "version": "1.0.0",
  "description": "An awesome MCP server package that does amazing things",
  "tags": ["mcp", "server", "automation", "productivity"],
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "contributors": [
    {
      "name": "Contributor Name", 
      "email": "contributor@example.com"
    }
  ],
  "license": {
    "name": "MIT",
    "uri": "https://opensource.org/licenses/MIT"
  },
  "repository": "https://github.com/yourusername/my-awesome-package",
  "documentation": "https://your-docs-site.com",
  "entry_point": "hatch_mcp_server_entry.py"
}
```

## Step 3: Define Dependencies

Configure different types of dependencies:

```json
{
  "dependencies": {
    "hatch": [
      {
        "name": "another_hatch_package",
        "version_constraint": ">=1.0.0"
      }
    ],
    "python": [
      {
        "name": "requests",
        "version_constraint": ">=2.28.0",
        "package_manager": "pip"
      },
      {
        "name": "numpy", 
        "version_constraint": "==1.24.0",
        "package_manager": "pip"
      }
    ],
    "system": [
      {
        "name": "curl",
        "version_constraint": ">=7.0.0",
        "package_manager": "apt"
      }
    ],
    "docker": [
      {
        "name": "redis",
        "version_constraint": ">=7.0.0", 
        "registry": "dockerhub"
      }
    ]
  }
}
```

### Version Constraint Patterns

- `==1.0.0` - Exact version
- `>=1.0.0` - Minimum version
- `<=2.0.0` - Maximum version  
- `!=1.5.0` - Exclude specific version

## Step 4: Set Compatibility Requirements

Define compatibility constraints:

```json
{
  "compatibility": {
    "hatchling": ">=0.1.0",
    "python": ">=3.8"
  }
}
```

## Step 5: Define Tools and Citations

Document the tools your package provides:

```json
{
  "tools": [
    {
      "name": "search_web",
      "description": "Search the web for information"
    },
    {
      "name": "analyze_data", 
      "description": "Analyze data sets and generate reports"
    }
  ],
  "citations": {
    "origin": "Based on the WebSearch project by Example Corp",
    "mcp": "Implements MCP specification version 1.0"
  }
}
```

## Step 6: Validate Metadata Structure

The schema enforces several validation rules:

- **Package names** must match pattern `^[a-z0-9_]+$`
- **Versions** must follow semantic versioning `^\d+(\.\d+)*$`
- **Email addresses** must be valid email format
- **URIs** must be valid URI format
- **Version constraints** must match pattern `^\s*(==|>=|<=|!=)\s*\d+(\.\d+)*$`

**Exercise:**
Create a complete metadata file for a hypothetical "weather-service" package that depends on the requests library and provides weather-related tools.

<details>
<summary>Solution</summary>

```json
{
  "package_schema_version": "1.2.0",
  "name": "weather_service",
  "version": "1.0.0",
  "description": "MCP server for weather information and forecasting",
  "tags": ["weather", "forecast", "api", "mcp"],
  "author": {
    "name": "Weather Developer",
    "email": "dev@weather-service.com"
  },
  "license": {
    "name": "MIT",
    "uri": "https://opensource.org/licenses/MIT"
  },
  "repository": "https://github.com/weather/weather-service",
  "entry_point": "hatch_mcp_server_entry.py",
  "dependencies": {
    "python": [
      {
        "name": "requests",
        "version_constraint": ">=2.28.0",
        "package_manager": "pip"
      }
    ]
  },
  "compatibility": {
    "python": ">=3.8"
  },
  "tools": [
    {
      "name": "get_current_weather",
      "description": "Get current weather for a location"
    },
    {
      "name": "get_forecast",
      "description": "Get weather forecast for a location"
    }
  ],
  "citations": {
    "origin": "Weather data provided by OpenWeather API",
    "mcp": "Implements MCP specification for weather services"
  }
}
```

</details>

> Previous: [Generate Template](01-generate-template.md)  
> Next: [Validate and Install](03-validate-and-install.md)
