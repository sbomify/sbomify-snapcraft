"""Tests for the CLI."""

import pytest
import json
from pathlib import Path
from click.testing import CliRunner
from sbomify_snapcraft.cli import main


class TestCLI:
    """Test the command-line interface."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def test_yaml_path(self):
        """Path to test snapcraft.yaml fixture."""
        return Path(__file__).parent / 'fixtures' / 'test_snapcraft.yaml'

    def test_help(self, runner):
        """Test --help flag."""
        result = runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert 'Convert a Snapcraft YAML file to SBOM format' in result.output

    def test_version(self, runner):
        """Test --version flag."""
        result = runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert 'sbomify-snapcraft' in result.output

    def test_generate_sbom_to_stdout(self, runner, test_yaml_path):
        """Test generating SBOM to stdout."""
        result = runner.invoke(main, [str(test_yaml_path)])
        assert result.exit_code == 0

        # Parse output as JSON
        data = json.loads(result.output)
        assert data['bomFormat'] == 'CycloneDX'
        assert data['specVersion'] == '1.6'
        assert 'components' in data
        assert len(data['components']) > 0

    def test_generate_sbom_to_file(self, runner, test_yaml_path, tmp_path):
        """Test generating SBOM to a file."""
        output_file = tmp_path / 'test_output.json'
        result = runner.invoke(main, [str(test_yaml_path), '-o', str(output_file)])
        assert result.exit_code == 0

        # Verify file was created
        assert output_file.exists()

        # Parse file content
        with open(output_file) as f:
            data = json.load(f)

        assert data['bomFormat'] == 'CycloneDX'
        assert len(data['components']) > 0

    def test_verbose_mode(self, runner, test_yaml_path):
        """Test verbose output mode."""
        result = runner.invoke(main, [str(test_yaml_path), '-v'])
        assert result.exit_code == 0
        assert 'Processing:' in result.output or 'Processing:' in result.stderr

    def test_nonexistent_file(self, runner):
        """Test with non-existent file."""
        result = runner.invoke(main, ['nonexistent.yaml'])
        assert result.exit_code != 0
        assert 'Error' in result.output or 'does not exist' in result.output.lower()

    def test_metadata_includes_tool_info(self, runner, test_yaml_path):
        """Test that generated SBOM includes tool metadata."""
        result = runner.invoke(main, [str(test_yaml_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        assert 'metadata' in data
        assert 'tools' in data['metadata']
        assert len(data['metadata']['tools']) > 0
        assert data['metadata']['tools'][0]['name'] == 'sbomify-snapcraft'

    def test_components_have_external_references(self, runner, test_yaml_path):
        """Test that components have external references (VCS)."""
        result = runner.invoke(main, [str(test_yaml_path)])
        assert result.exit_code == 0

        data = json.loads(result.output)
        components = data['components']

        # At least some components should have external references
        components_with_refs = [c for c in components if 'externalReferences' in c]
        assert len(components_with_refs) > 0

        # Check first component with ref
        ref = components_with_refs[0]['externalReferences'][0]
        assert ref['type'] == 'vcs'
        assert 'url' in ref

