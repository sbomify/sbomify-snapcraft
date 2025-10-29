"""Command-line interface for sbomify-snapcraft."""

import click
import sys
from pathlib import Path

from sbomify_snapcraft.parser import SnapcraftParser
from sbomify_snapcraft.sbom_generator import SBOMGenerator


@click.command()
@click.argument(
    'snapcraft_file',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
    default='snapcraft.yaml'
)
@click.option(
    '--output', '-o',
    type=click.Path(dir_okay=False, path_type=Path),
    help='Output file path for the SBOM JSON (default: stdout)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.version_option(version='0.1.0', prog_name='sbomify-snapcraft')
def main(snapcraft_file, output, verbose):
    """Convert a Snapcraft YAML file to SBOM format (JSON).

    By default, reads from 'snapcraft.yaml' in the current directory
    and outputs JSON to stdout.
    """
    try:
        if verbose:
            click.echo(f"Processing: {snapcraft_file}", err=True)
            if output:
                click.echo(f"Output file: {output}", err=True)
            else:
                click.echo("Output: stdout", err=True)

        # Parse snapcraft.yaml
        parser = SnapcraftParser(snapcraft_file)
        parser.parse()

        # Get snap information
        snap_name = parser.get_snap_name()
        if verbose and snap_name:
            click.echo(f"Snap name: {snap_name}", err=True)

        # Get all parts with source, name, and version
        parts_with_source = parser.get_parts_with_name_and_version()

        if verbose:
            click.echo(f"\nFound {len(parts_with_source)} parts with source:\n", err=True)
            for part in parts_with_source:
                click.echo(f"Part: {part['name']}", err=True)
                click.echo(f"  Package Name: {part['package_name']}", err=True)
                if part['version']:
                    click.echo(f"  Version: {part['version']}", err=True)
                else:
                    click.echo(f"  Version: (not detected)", err=True)
                click.echo(f"  Source: {part['source']}", err=True)
                if part['source_type']:
                    click.echo(f"  Type: {part['source_type']}", err=True)
                if part['source_tag']:
                    click.echo(f"  Tag: {part['source_tag']}", err=True)
                if part['source_branch']:
                    click.echo(f"  Branch: {part['source_branch']}", err=True)
                if part['source_commit']:
                    click.echo(f"  Commit: {part['source_commit']}", err=True)
                click.echo("", err=True)

        # Create SBOM generator
        generator = SBOMGenerator(snap_name=snap_name)

        # Add all components from parts
        generator.add_components_from_parts(parts_with_source)

        if verbose:
            click.echo(f"Added {len(parts_with_source)} components to SBOM", err=True)

        # Generate output
        output_path = str(output) if output else None
        generator.generate(output_file=output_path)

        if verbose:
            click.echo("✓ SBOM generated successfully!", err=True)

    except FileNotFoundError as e:
        click.echo(f"Error: File not found - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

