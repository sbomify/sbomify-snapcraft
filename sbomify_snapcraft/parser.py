"""Parse snapcraft.yaml files."""

import yaml
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse


class SnapcraftParser:
    """Parse snapcraft.yaml files and extract component information."""

    def __init__(self, snapcraft_file: Path):
        """Initialize the parser with a snapcraft.yaml file.

        Args:
            snapcraft_file: Path to the snapcraft.yaml file
        """
        self.snapcraft_file = snapcraft_file
        self.data: Dict = {}

    def parse(self) -> Dict:
        """Parse the snapcraft.yaml file.

        Returns:
            Dict: Parsed YAML data
        """
        with open(self.snapcraft_file, 'r') as f:
            self.data = yaml.safe_load(f)
        return self.data

    def get_parts_with_source(self) -> List[Dict]:
        """Extract all parts that have a 'source' key.

        Returns:
            List[Dict]: List of parts with source information
        """
        if not self.data:
            self.parse()

        parts = self.data.get('parts', {})
        parts_with_source = []

        for part_name, part_data in parts.items():
            if isinstance(part_data, dict) and 'source' in part_data:
                source = part_data['source']

                # Skip local sources - only include remote URLs
                if not self._is_remote_source(source):
                    continue

                part_info = {
                    'name': part_name,
                    'source': source,
                    'source_type': part_data.get('source-type'),
                    'source_tag': part_data.get('source-tag'),
                    'source_branch': part_data.get('source-branch'),
                    'source_commit': part_data.get('source-commit'),
                    'source_depth': part_data.get('source-depth'),
                    'plugin': part_data.get('plugin'),
                }
                parts_with_source.append(part_info)

        return parts_with_source

    @staticmethod
    def _is_remote_source(source: str) -> bool:
        """Check if a source is a remote URL.

        Args:
            source: Source string to check

        Returns:
            bool: True if source is a remote URL, False otherwise
        """
        if not source:
            return False

        # Check if it's a remote URL
        return source.startswith(('http://', 'https://', 'git://', 'git@', 'ftp://', 'ftps://'))

    def get_snap_name(self) -> Optional[str]:
        """Get the snap name from the snapcraft.yaml.

        Returns:
            Optional[str]: The snap name, or None if not found
        """
        if not self.data:
            self.parse()
        return self.data.get('name')

    def get_snap_version(self) -> Optional[str]:
        """Get the snap version from the snapcraft.yaml.

        Returns:
            Optional[str]: The snap version, or None if not found
        """
        if not self.data:
            self.parse()
        return self.data.get('version')

    @staticmethod
    def extract_package_name_from_source(source: str, part_name: str) -> str:
        """Extract package name from source URL or use part name as fallback.

        Args:
            source: Source URL or path
            part_name: Name of the part (fallback)

        Returns:
            str: Extracted package name
        """
        # Handle local sources
        if source in ['.', '..'] or not source.startswith(('http://', 'https://', 'git://', 'git@')):
            return part_name

        try:
            # Parse URL
            if source.startswith('git@'):
                # Handle git@github.com:user/repo.git format
                match = re.search(r'git@[^:]+:([^/]+)/([^/\.]+)', source)
                if match:
                    return match.group(2)
            else:
                parsed = urlparse(source)
                path = parsed.path

                # Remove .git extension
                path = re.sub(r'\.git$', '', path)

                # Get the last part of the path (repository name or filename)
                parts = path.strip('/').split('/')
                if parts:
                    name = parts[-1]

                    # Clean up file extensions
                    name = re.sub(r'\.(tar|zip|tgz|tbz2|txz|gz|bz2|xz).*$', '', name)

                    # Extract base package name from patterns like:
                    # - package-v1.2.3-arch-platform
                    # - package-1.2.3
                    # - package_v1.2.3
                    # - package-src-1.2.3
                    # Match: package name before version pattern or platform identifiers

                    # First, remove common source indicators
                    name = re.sub(r'[-_](src|source|sources)(?=[-_]|$)', '', name, flags=re.IGNORECASE)

                    # Try to match common patterns and extract just the package name
                    # Pattern: name-v?version or name-platform-arch
                    match = re.match(r'^([a-zA-Z][\w-]*?)(?:-v?\d+[\d\.].*)?(?:-(?:x86_64|aarch64|arm|i686|linux|windows|darwin|macos|unknown|musl|gnu).*)?$', name)
                    if match:
                        return match.group(1)

                    # If no match, try simpler pattern: just remove version numbers
                    match = re.match(r'^([a-zA-Z][\w-]*?)(?:[-_]v?\d+[\d\.].*)?$', name)
                    if match:
                        return match.group(1)

                    return name
        except Exception:
            pass

        # Fallback to part name
        return part_name

    @staticmethod
    def extract_version_from_part(part_info: Dict) -> Optional[str]:
        """Extract version from part information.

        Priority:
        1. source-tag (preferred - usually contains version)
        2. source-branch (if it looks like a version)
        3. source-commit (shortened to 7 chars)
        4. Extract from source URL/filename

        Args:
            part_info: Dictionary containing part information

        Returns:
            Optional[str]: Extracted version or None
        """
        # Priority 1: source-tag
        if part_info.get('source_tag'):
            tag = part_info['source_tag']
            # Strip 'v' or 'V' prefix only if followed by a digit (semantic version)
            # Don't strip if it's a git hash that happens to start with 'v'
            version = re.sub(r'^[vV](?=\d)', '', tag)
            # Remove file extensions that might have leaked in
            version = re.sub(r'\.(tar|gz|bz2|xz|zip).*$', '', version)
            return version

        # Priority 2: source-branch (if it looks like a version)
        if part_info.get('source_branch'):
            branch = part_info['source_branch']
            # Check if branch looks like a version (contains numbers)
            if re.search(r'\d', branch):
                # Strip 'v' prefix only if followed by a digit
                cleaned = re.sub(r'^[vV](?=\d)', '', branch)
                return cleaned

        # Priority 3: source-commit (short form)
        if part_info.get('source_commit'):
            commit = part_info['source_commit']
            # Return first 7 characters of commit hash
            return commit[:7] if len(commit) >= 7 else commit

        # Priority 4: Try to extract from source URL
        source = part_info.get('source', '')
        if source:
            # Try to find version patterns in the URL
            # Prefer filename over path by searching from the end
            # Split URL to get filename
            url_parts = source.split('/')
            filename = url_parts[-1] if url_parts else source

            # First try to extract from filename (most specific)
            version_match = re.search(r'[/-]v?(\d+(?:\.\d+)+(?:[.-][\w]+)?)', filename)
            if version_match:
                version = version_match.group(1)
                # Clean up file extensions and normalize (remove v prefix only if followed by digit)
                version = re.sub(r'\.(tar|gz|bz2|xz|zip).*$', '', version)
                version = re.sub(r'^[vV](?=\d)', '', version)
                return version

            # If not found in filename, try the full URL
            version_match = re.search(r'[/-]v?(\d+(?:\.\d+)+(?:[.-][\w]+)?)', source)
            if version_match:
                version = version_match.group(1)
                # Clean up file extensions and normalize (remove v prefix only if followed by digit)
                version = re.sub(r'\.(tar|gz|bz2|xz|zip).*$', '', version)
                version = re.sub(r'^[vV](?=\d)', '', version)
                return version

        return None

    def get_parts_with_name_and_version(self) -> List[Dict]:
        """Extract all parts with source, name, and version information.

        Returns:
            List[Dict]: List of parts with extracted name and version
        """
        parts_with_source = self.get_parts_with_source()

        enriched_parts = []
        for part in parts_with_source:
            package_name = self.extract_package_name_from_source(
                part['source'],
                part['name']
            )
            version = self.extract_version_from_part(part)

            enriched_part = {
                **part,
                'package_name': package_name,
                'version': version
            }
            enriched_parts.append(enriched_part)

        return enriched_parts

