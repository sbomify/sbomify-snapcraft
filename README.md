# sbomify-snapcraft

Convert Snapcraft YAML files to SBOM (Software Bill of Materials) format in CycloneDX JSON.

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

# Output to a file (outputs JSON)
uv run sbomify-snapcraft snapcraft.yaml -o output.json

# Verbose mode
uv run sbomify-snapcraft snapcraft.yaml -v

# Show help
uv run sbomify-snapcraft --help
```

## Output Format

The tool generates CycloneDX 1.6 SBOM in JSON format. By default, output is sent to stdout, but can be written to a file using the `-o` option.

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

