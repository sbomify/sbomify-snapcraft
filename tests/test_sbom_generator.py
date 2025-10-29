"""Tests for the SBOM generator."""

import pytest
import json
from pathlib import Path
from sbomify_snapcraft.sbom_generator import SBOMGenerator
from cyclonedx.model.component import ComponentType


class TestSBOMGenerator:
    """Test the SBOMGenerator class."""
    
    def test_init_creates_bom(self):
        """Test that initialization creates a BOM."""
        generator = SBOMGenerator()
        assert generator.bom is not None
    
    def test_metadata_includes_tool(self):
        """Test that metadata includes tool information."""
        generator = SBOMGenerator()
        assert len(generator.bom.metadata.tools.tools) > 0
        
        tool = list(generator.bom.metadata.tools.tools)[0]
        assert tool.name == 'sbomify-snapcraft'
        assert tool.vendor is not None
        assert tool.version is not None
    
    def test_metadata_includes_supplier(self):
        """Test that metadata includes supplier."""
        generator = SBOMGenerator()
        assert generator.bom.metadata.supplier is not None
        assert generator.bom.metadata.supplier.name is not None
    
    def test_add_component(self):
        """Test adding a simple component."""
        generator = SBOMGenerator()
        generator.add_component('test-lib', '1.0.0', ComponentType.LIBRARY)
        
        assert len(generator.bom.components) == 1
        component = list(generator.bom.components)[0]
        assert component.name == 'test-lib'
        assert component.version == '1.0.0'
        assert component.type == ComponentType.LIBRARY
    
    def test_add_component_from_part(self):
        """Test adding a component from part information."""
        generator = SBOMGenerator()
        part_info = {
            'name': 'lib-alpha',
            'package_name': 'lib-alpha',
            'version': '2.4.8',
            'source': 'https://github.com/example/lib-alpha.git',
            'source_tag': 'v2.4.8',
            'plugin': 'cmake'
        }
        
        generator.add_component_from_part(part_info)
        
        assert len(generator.bom.components) == 1
        component = list(generator.bom.components)[0]
        assert component.name == 'lib-alpha'
        assert component.version == '2.4.8'
        assert component.type == ComponentType.LIBRARY
    
    def test_add_component_with_external_reference(self):
        """Test that external reference (VCS) is added."""
        generator = SBOMGenerator()
        part_info = {
            'name': 'lib-beta',
            'package_name': 'lib-beta',
            'version': '3.0.0',
            'source': 'https://github.com/example/lib-beta.git'
        }
        
        generator.add_component_from_part(part_info)
        
        component = list(generator.bom.components)[0]
        assert component.external_references is not None
        assert len(component.external_references) > 0
        
        ext_ref = list(component.external_references)[0]
        assert str(ext_ref.url) == 'https://github.com/example/lib-beta.git'
    
    def test_add_components_from_parts(self):
        """Test adding multiple components at once."""
        generator = SBOMGenerator()
        parts = [
            {
                'name': 'lib-alpha',
                'package_name': 'lib-alpha',
                'version': '1.0.0',
                'source': 'https://github.com/example/lib-alpha.git'
            },
            {
                'name': 'lib-beta',
                'package_name': 'lib-beta',
                'version': '2.0.0',
                'source': 'https://github.com/example/lib-beta.git'
            }
        ]
        
        generator.add_components_from_parts(parts)
        
        assert len(generator.bom.components) == 2
        names = {c.name for c in generator.bom.components}
        assert 'lib-alpha' in names
        assert 'lib-beta' in names
    
    def test_generate_output(self, tmp_path):
        """Test generating SBOM output to file."""
        generator = SBOMGenerator()
        generator.add_component('test-lib', '1.0.0', ComponentType.LIBRARY)
        
        output_file = tmp_path / 'test_sbom.json'
        generator.generate(output_file=str(output_file))
        
        assert output_file.exists()
        
        # Verify it's valid JSON
        with open(output_file) as f:
            data = json.load(f)
        
        assert data['bomFormat'] == 'CycloneDX'
        assert data['specVersion'] == '1.6'
        assert 'components' in data
        assert len(data['components']) == 1
        assert data['components'][0]['name'] == 'test-lib'
    
    def test_component_without_version(self):
        """Test that components without version are handled."""
        generator = SBOMGenerator()
        part_info = {
            'name': 'lib-gamma',
            'package_name': 'lib-gamma',
            'version': None,
            'source': 'https://github.com/example/lib-gamma.git'
        }
        
        generator.add_component_from_part(part_info)
        
        component = list(generator.bom.components)[0]
        assert component.name == 'lib-gamma'
        assert component.version == 'unknown'

