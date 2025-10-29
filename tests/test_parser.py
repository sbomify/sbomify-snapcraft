"""Tests for the snapcraft parser."""

import pytest
from pathlib import Path
from sbomify_snapcraft.parser import SnapcraftParser


class TestSnapcraftParser:
    """Test the SnapcraftParser class."""

    @pytest.fixture
    def test_yaml_path(self):
        """Path to test snapcraft.yaml fixture."""
        return Path(__file__).parent / 'fixtures' / 'test_snapcraft.yaml'

    @pytest.fixture
    def parser(self, test_yaml_path):
        """Create a parser instance with test data."""
        return SnapcraftParser(test_yaml_path)

    def test_parse_snapcraft_file(self, parser):
        """Test parsing a snapcraft.yaml file."""
        data = parser.parse()
        assert data is not None
        assert data['name'] == 'example-app'
        assert 'parts' in data

    def test_get_snap_name(self, parser):
        """Test extracting snap name."""
        parser.parse()
        assert parser.get_snap_name() == 'example-app'

    def test_get_parts_with_source(self, parser):
        """Test extracting parts with source."""
        parser.parse()
        parts = parser.get_parts_with_source()

        # Should only include remote sources (not local-part)
        assert len(parts) == 6
        part_names = [p['name'] for p in parts]
        assert 'local-part' not in part_names
        assert 'lib-alpha' in part_names

    def test_extract_package_name_from_github(self):
        """Test extracting package name from GitHub URL."""
        name = SnapcraftParser.extract_package_name_from_source(
            'https://github.com/example/lib-alpha.git',
            'fallback'
        )
        assert name == 'lib-alpha'

    def test_extract_package_name_from_tarball(self):
        """Test extracting package name from tarball URL."""
        name = SnapcraftParser.extract_package_name_from_source(
            'https://example.com/downloads/lib-delta-3.1.4.tar.xz',
            'fallback'
        )
        assert name == 'lib-delta'

    def test_extract_package_name_removes_src_suffix(self):
        """Test that -src suffix is removed from package names."""
        name = SnapcraftParser.extract_package_name_from_source(
            'https://example.com/archive/lib-epsilon-src-5.6.7.tar.gz',
            'fallback'
        )
        assert name == 'lib-epsilon'

    def test_extract_package_name_removes_platform_identifiers(self):
        """Test that platform identifiers are removed."""
        name = SnapcraftParser.extract_package_name_from_source(
            'https://example.com/releases/tool-zeta-v1.9.2-x86_64-unknown-linux-musl.tar.gz',
            'fallback'
        )
        assert name == 'tool-zeta'

    def test_extract_package_name_local_source(self):
        """Test that local sources use fallback name."""
        name = SnapcraftParser.extract_package_name_from_source('.', 'fallback')
        assert name == 'fallback'

    def test_extract_version_from_tag(self):
        """Test extracting version from git tag."""
        part_info = {
            'source_tag': 'v2.4.8',
            'source': 'https://github.com/example/lib-alpha.git'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == '2.4.8'

    def test_extract_version_from_tag_without_v(self):
        """Test extracting version from git tag without v prefix."""
        part_info = {
            'source_tag': '1.2.3',
            'source': 'https://github.com/example/lib.git'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == '1.2.3'

    def test_extract_version_from_branch(self):
        """Test extracting version from git branch."""
        part_info = {
            'source_branch': 'n7.2.3',
            'source': 'https://github.com/example/lib-beta.git'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == 'n7.2.3'

    def test_extract_version_from_commit(self):
        """Test extracting version from git commit (shortened)."""
        part_info = {
            'source_commit': 'abc1234567890def1234567890abcdef12345678',
            'source': 'https://github.com/example/lib-gamma.git'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == 'abc1234'

    def test_extract_version_from_url_filename(self):
        """Test extracting version from URL filename."""
        part_info = {
            'source': 'https://example.com/downloads/lib-delta-3.1.4.tar.xz'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == '3.1.4'

    def test_extract_version_from_url_with_v_prefix(self):
        """Test version extraction removes v prefix from URLs."""
        part_info = {
            'source': 'https://example.com/releases/tool-v1.9.2.tar.gz'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == '1.9.2'

    def test_version_priority_tag_over_url(self):
        """Test that tag version takes priority over URL version."""
        part_info = {
            'source_tag': 'v5.0.0',
            'source': 'https://example.com/lib-1.0.0.tar.gz'
        }
        version = SnapcraftParser.extract_version_from_part(part_info)
        assert version == '5.0.0'

    def test_get_parts_with_name_and_version(self, parser):
        """Test extracting parts with enriched name and version."""
        parser.parse()
        parts = parser.get_parts_with_name_and_version()

        # Find specific parts
        lib_alpha = next(p for p in parts if p['name'] == 'lib-alpha')
        assert lib_alpha['package_name'] == 'lib-alpha'
        assert lib_alpha['version'] == '2.4.8'

        lib_epsilon = next(p for p in parts if p['name'] == 'lib-epsilon')
        assert lib_epsilon['package_name'] == 'lib-epsilon'  # -src removed
        assert lib_epsilon['version'] == '5.6.7'

        tool_zeta = next(p for p in parts if p['name'] == 'tool-zeta')
        assert tool_zeta['package_name'] == 'tool-zeta'  # platform removed
        # Version extraction from complex filenames may include some platform info
        assert tool_zeta['version'].startswith('1.9.2')

    def test_is_remote_source(self):
        """Test remote source detection."""
        assert SnapcraftParser._is_remote_source('https://github.com/test/test.git')
        assert SnapcraftParser._is_remote_source('http://example.com/file.tar.gz')
        assert SnapcraftParser._is_remote_source('git@github.com:user/repo.git')
        assert not SnapcraftParser._is_remote_source('.')
        assert not SnapcraftParser._is_remote_source('..')
        assert not SnapcraftParser._is_remote_source('./local/path')

