"""
Tests for MacDitto utility functions.
"""

import pytest
from unittest.mock import patch, MagicMock
from macditto.utils import (
    get_home_directory, run_command, detect_category, is_standard_macos_app,
    get_machine_name, file_exists, read_file, get_timestamp
)


class TestGetHomeDirectory:
    """Tests for get_home_directory function."""

    def test_returns_expanded_path(self):
        """Should return expanded home directory path."""
        home = get_home_directory()
        assert home
        assert not home.startswith('~')
        assert '/' in home


class TestRunCommand:
    """Tests for run_command function."""

    def test_successful_command(self):
        """Should execute command successfully and return output."""
        success, stdout, stderr = run_command(['echo', 'hello'])
        assert success is True
        assert 'hello' in stdout
        assert stderr == ''

    def test_failed_command(self):
        """Should handle command failure gracefully."""
        success, stdout, stderr = run_command(['false'])
        assert success is False

    def test_nonexistent_command(self):
        """Should handle nonexistent command gracefully."""
        success, stdout, stderr = run_command(['nonexistent_command_xyz'])
        assert success is False
        assert 'not found' in stderr.lower()

    def test_command_timeout(self):
        """Should timeout long-running commands."""
        success, stdout, stderr = run_command(['sleep', '5'], timeout=1)
        assert success is False
        assert 'timed out' in stderr.lower()


class TestDetectCategory:
    """Tests for detect_category function."""

    def test_development_tools(self):
        """Should categorize development tools correctly."""
        assert detect_category('IntelliJ IDEA') == 'Development'
        assert detect_category('Docker Desktop') == 'Development'
        assert detect_category('Visual Studio Code') == 'Development'
        assert detect_category('python') == 'Development'
        assert detect_category('node') == 'Development'
        assert detect_category('git') == 'Development'

    def test_productivity_apps(self):
        """Should categorize productivity apps correctly."""
        assert detect_category('Evernote') == 'Productivity'
        assert detect_category('Notion') == 'Productivity'
        assert detect_category('Proton Mail') == 'Productivity'

    def test_media_tools(self):
        """Should categorize media tools correctly."""
        assert detect_category('DaVinci Resolve') == 'Media'
        assert detect_category('Spotify') == 'Media'
        assert detect_category('Audacity') == 'Media'
        assert detect_category('ffmpeg') == 'Media'

    def test_communication_apps(self):
        """Should categorize communication apps correctly."""
        assert detect_category('Signal') == 'Communication'
        assert detect_category('Zoom') == 'Communication'
        assert detect_category('Slack') == 'Communication'

    def test_browsers(self):
        """Should categorize browsers correctly."""
        assert detect_category('Brave Browser') == 'Browsers'
        assert detect_category('Google Chrome') == 'Browsers'
        assert detect_category('Firefox') == 'Browsers'

    def test_security_apps(self):
        """Should categorize security apps correctly."""
        assert detect_category('Surfshark') == 'Security/Privacy'
        assert detect_category('1Password') == 'Security/Privacy'
        assert detect_category('gnupg') == 'Security/Privacy'

    def test_ai_tools(self):
        """Should categorize AI tools correctly."""
        assert detect_category('Claude Code') == 'AI/ML'
        assert detect_category('Whisper') == 'AI/ML'
        assert detect_category('ChatGPT') == 'AI/ML'

    def test_utilities(self):
        """Should categorize utilities correctly."""
        assert detect_category('CleanMyMac') == 'Utilities'
        assert detect_category('Rectangle') == 'Utilities'
        assert detect_category('wget') == 'Utilities'

    def test_unknown_app(self):
        """Should return 'Other' for unknown apps."""
        assert detect_category('Unknown App XYZ') == 'Other'


class TestIsStandardMacOSApp:
    """Tests for is_standard_macos_app function."""

    def test_standard_system_apps(self):
        """Should identify standard system apps."""
        assert is_standard_macos_app('Safari') is True
        assert is_standard_macos_app('Mail') is True
        assert is_standard_macos_app('Finder') is True
        assert is_standard_macos_app('Calendar') is True

    def test_standard_iwork_apps(self):
        """Should identify iWork apps as standard."""
        assert is_standard_macos_app('Keynote') is True
        assert is_standard_macos_app('Numbers') is True
        assert is_standard_macos_app('Pages') is True

    def test_standard_ilife_apps(self):
        """Should identify iLife apps as standard."""
        assert is_standard_macos_app('GarageBand') is True
        assert is_standard_macos_app('iMovie') is True

    def test_apple_bundle_id(self):
        """Should identify apps by Apple bundle ID."""
        assert is_standard_macos_app('SomeApp', 'com.apple.Safari') is True
        assert is_standard_macos_app('AnotherApp', 'com.apple.mail') is True

    def test_third_party_apps(self):
        """Should not flag third-party apps as standard."""
        assert is_standard_macos_app('Brave Browser') is False
        assert is_standard_macos_app('Visual Studio Code') is False
        assert is_standard_macos_app('Docker', 'com.docker.docker') is False


class TestGetMachineName:
    """Tests for get_machine_name function."""

    @patch('macditto.utils.run_command')
    def test_gets_computer_name(self, mock_run_command):
        """Should get computer name from scutil."""
        mock_run_command.return_value = (True, "Steve's MacBook Air\n", "")
        name = get_machine_name()
        assert name == "Steve's MacBook Air"
        mock_run_command.assert_called_once_with(['scutil', '--get', 'ComputerName'])

    @patch('macditto.utils.run_command')
    @patch('macditto.utils.platform')
    def test_fallback_to_hostname(self, mock_platform, mock_run_command):
        """Should fall back to hostname if scutil fails."""
        mock_run_command.return_value = (False, "", "error")
        mock_platform.node.return_value = "hostname.local"
        name = get_machine_name()
        assert name == "hostname.local"


class TestFileExists:
    """Tests for file_exists function."""

    def test_existing_file(self, tmp_path):
        """Should return True for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert file_exists(str(test_file)) is True

    def test_nonexistent_file(self, tmp_path):
        """Should return False for nonexistent file."""
        assert file_exists(str(tmp_path / "nonexistent.txt")) is False


class TestReadFile:
    """Tests for read_file function."""

    def test_read_existing_file(self, tmp_path):
        """Should read file contents."""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content)
        assert read_file(str(test_file)) == content

    def test_read_nonexistent_file(self, tmp_path):
        """Should return None for nonexistent file."""
        assert read_file(str(tmp_path / "nonexistent.txt")) is None


class TestGetTimestamp:
    """Tests for get_timestamp function."""

    def test_returns_iso_format(self):
        """Should return ISO 8601 formatted timestamp."""
        timestamp = get_timestamp()
        assert timestamp
        assert 'T' in timestamp
        # Should match format: 2026-02-15T10:30:00
        parts = timestamp.split('T')
        assert len(parts) == 2
        date_parts = parts[0].split('-')
        assert len(date_parts) == 3
        time_parts = parts[1].split(':')
        assert len(time_parts) == 3
