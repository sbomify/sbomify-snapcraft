"""SBOM generation using CycloneDX."""

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model import ExternalReference, ExternalReferenceType, XsUri
from cyclonedx.model.contact import OrganizationalEntity
from cyclonedx.model.tool import Tool
from cyclonedx.output.json import JsonV1Dot6
from typing import Optional, Dict, List
from pathlib import Path
import sys
import tomllib


class SBOMGenerator:
    """Generate CycloneDX SBOM from snapcraft data."""

    def __init__(self, snap_name: Optional[str] = None):
        """Initialize the SBOM generator.

        Args:
            snap_name: Name of the snap package (optional)
        """
        self.bom = Bom()
        self.snap_name = snap_name
        self._setup_metadata()

    def _setup_metadata(self) -> None:
        """Setup SBOM metadata including tool and organization information."""
        # Get version and company from pyproject.toml
        version, company = self._get_project_info()

        # Create tool information
        tool = Tool(
            vendor=company,
            name='sbomify-snapcraft',
            version=version
        )

        # Add tool to metadata
        self.bom.metadata.tools.tools.add(tool)

        # Set the supplier/manufacturer
        supplier = OrganizationalEntity(
            name=company
        )
        self.bom.metadata.supplier = supplier

    @staticmethod
    def _get_project_info() -> tuple[str, str]:
        """Get version and company from pyproject.toml.

        Returns:
            tuple: (version, company) from pyproject.toml, or defaults if not found
        """
        version = 'unknown'
        company = 'Unknown'

        try:
            # Find pyproject.toml relative to this file
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            pyproject_path = project_root / 'pyproject.toml'

            if pyproject_path.exists():
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                    version = data.get('project', {}).get('version', 'unknown')
                    company = data.get('tool', {}).get('sbomify', {}).get('company', 'Unknown')
        except Exception:
            pass

        return version, company

    def create_empty_sbom(self) -> Bom:
        """Create an empty SBOM with basic metadata.

        Returns:
            Bom: An empty CycloneDX BOM object
        """
        return self.bom

    def add_component(self, name: str, version: str, component_type: ComponentType = ComponentType.APPLICATION) -> None:
        """Add a component to the SBOM.

        Args:
            name: Component name
            version: Component version
            component_type: Type of component (default: APPLICATION)
        """
        component = Component(
            name=name,
            version=version,
            type=component_type
        )
        self.bom.components.add(component)

    def add_component_from_part(self, part_info: Dict) -> None:
        """Add a component to the SBOM from snapcraft part information.

        Args:
            part_info: Dictionary containing part information including:
                - package_name: Package name
                - version: Package version
                - source: Source URL
                - source_type: Type of source (git, etc.)
                - source_tag: Git tag
                - source_branch: Git branch
                - source_commit: Git commit hash
        """
        package_name = part_info.get('package_name')
        version = part_info.get('version') or 'unknown'

        if not package_name:
            return

        # Create the component
        component = Component(
            name=package_name,
            version=version,
            type=ComponentType.LIBRARY  # External dependencies are typically libraries
        )

        # Add external references
        external_refs = []

        # Add VCS reference if source is available
        source = part_info.get('source')
        if source:
            try:
                vcs_ref = ExternalReference(
                    type=ExternalReferenceType.VCS,
                    url=XsUri(source)
                )
                external_refs.append(vcs_ref)
            except Exception:
                pass  # Skip invalid URLs

        if external_refs:
            component.external_references = external_refs

        self.bom.components.add(component)

    def add_components_from_parts(self, parts: List[Dict]) -> None:
        """Add multiple components from a list of snapcraft parts.

        Args:
            parts: List of part information dictionaries
        """
        for part in parts:
            self.add_component_from_part(part)

    def generate(self, output_file: Optional[str] = None) -> None:
        """Generate and output the SBOM in JSON format.

        Args:
            output_file: Path to output file, or None for stdout
        """
        outputter = JsonV1Dot6(self.bom)
        output = outputter.output_as_string()

        if output_file:
            with open(output_file, 'w') as f:
                f.write(output)
        else:
            sys.stdout.write(output)
            sys.stdout.write('\n')

