# sbomify-snapcraft

Generate SBOMs (Software Bill of Materials) from Snapcraft YAML files.

## About

This tool generates SBOMs from `snapcraft.yaml` files, extracting information about source code dependencies that are compiled into snap packages. It is opinionated in favor of **CycloneDX** format and **JSON** output.

### What it does

- Parses `snapcraft.yaml` files to extract dependency information
- Identifies all parts with remote source repositories (git, tarballs, etc.)
- Extracts package names and versions from source URLs, tags, branches, and commits
- Generates a CycloneDX 1.6 SBOM in JSON format

### Important Limitations

This tool is **intentionally incomplete** by design:

- **Only extracts source-level dependencies**: It captures libraries and components that are compiled from source during the snap build process
- **Does not include runtime dependencies**: Stage packages and other runtime dependencies are deliberately excluded
- **Version information is best-effort**: Package versions are inferred from source references (git tags, branches, filenames) and may not reflect the actual built versions

**Technical Note:** This generates a **source SBOM** - documenting what goes into the build, not what comes out. It represents the declared dependencies in the snapcraft.yaml before the build process executes.

**Why these limitations?** Snapcraft uses `stage-packages` to pull in pre-built system packages at build time. The specific versions of these packages depend on the build environment and base image at the time of the build. Since we cannot know which versions will be installed until the snap is actually built, we cannot accurately include them in an SBOM generated from just the `snapcraft.yaml` file.

For a complete SBOM of a snap package (including a build SBOM or deployed SBOM), this tool should be used in conjunction with build-time introspection tools.

## Installation

```bash
uv pip install -e .
```

## Usage

```bash
# Process snapcraft.yaml in current directory (default)
uv run sbomify-snapcraft

# Process a specific snapcraft.yaml file
uv run sbomify-snapcraft path/to/snapcraft.yaml

# Output to a file
uv run sbomify-snapcraft snapcraft.yaml -o output.json

# Verbose mode (shows extracted packages)
uv run sbomify-snapcraft snapcraft.yaml -v

# Show help
uv run sbomify-snapcraft --help
```

## Output Format

Generates CycloneDX 1.6 SBOM in JSON format. Each component includes:

- Package name (extracted from source URL)
- Version (from git tags, branches, commits, or filenames)
- External reference (VCS source URL)
- Component type (library)

## Development

This project uses `uv` for dependency management.

To add dependencies:

```bash
uv add package-name
```

To run the CLI during development:

```bash
uv run sbomify-snapcraft
```

### Testing

Run the test suite:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run pytest --cov=sbomify_snapcraft --cov-report=term-missing
```

The project maintains a minimum test coverage of 80%.
