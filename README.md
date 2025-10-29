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

Each component includes:
- Package name (extracted from source URL)
- Version (from git tags, branches, commits, or filenames)
- External reference (VCS source URL)
- Component type (library)

## Example: Telegram Desktop

Using the [Telegram Desktop snapcraft.yaml](https://raw.githubusercontent.com/telegramdesktop/tdesktop/refs/heads/dev/snap/snapcraft.yaml) as a real-world example:

```bash
# Download the snapcraft.yaml
curl -o telegram.yaml https://raw.githubusercontent.com/telegramdesktop/tdesktop/refs/heads/dev/snap/snapcraft.yaml

# Generate SBOM
uv run sbomify-snapcraft telegram.yaml -o telegram-sbom.json

# View with verbose output to see what was extracted
uv run sbomify-snapcraft telegram.yaml -v
```

**Example output (abbreviated):**
```
Snap name: telegram-desktop

Found 12 parts with source:

Part: patches
  Package Name: patches
  Version: 0b68b11
  Source: https://github.com/desktop-app/patches.git

Part: ada
  Package Name: ada
  Version: 3.2.4
  Source: https://github.com/ada-url/ada.git

Part: avif
  Package Name: libavif
  Version: 1.3.0
  Source: https://github.com/AOMediaCodec/libavif.git

Part: ffmpeg
  Package Name: FFmpeg
  Version: n6.1.1
  Source: https://github.com/FFmpeg/FFmpeg.git

Part: qt
  Package Name: qt5
  Version: 6.10.0
  Source: https://github.com/qt/qt5.git

... (7 more components)
```

**Generated SBOM includes:**
- 12 source dependencies compiled from Git repositories
- Package names extracted from repository URLs
- Versions from git tags (`v3.2.4` → `3.2.4`), branches (`n6.1.1`), or commit hashes (`0b68b11`)
- VCS external references pointing to source repositories
- Metadata: tool information (sbomify-snapcraft), supplier, timestamp

**Not included (by design):**
- The `stage-packages` (gstreamer1.0-fdkaac, libgeoclue-2-0, etc.) - pre-built system packages whose versions depend on build environment
- The `build-packages` (clang, libboost-regex-dev, etc.) - build-time only dependencies
- The local `telegram` part with `source: .` - local source code being packaged

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

