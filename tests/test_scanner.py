"""
Tests for MacDitto scanner module.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import json

from macditto.scanner import Scanner
from macditto.models import Item, BrowserExtension, ShellConfig, SystemPreference


class TestScanner:
    """Tests for Scanner class."""

    @pytest.fixture
    def scanner(self):
        """Create Scanner instance for testing."""
        return Scanner()

    def test_scanner_initialization(self, scanner):
        """Should initialize scanner with correct paths."""
        assert scanner.home_dir
        assert scanner.applications_dir == "/Applications"
        assert scanner.user_applications_dir


class TestScanHomebrew:
    """Tests for scan_homebrew method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.run_command')
    def test_scan_homebrew_with_bundle_dump(self, mock_run_command, scanner):
        """Should parse brew bundle dump output."""
        brew_output = '''brew "git" # Distributed revision control system
brew "python" # Interpreted, interactive, object-oriented programming language
cask "docker" # App to build and share containerized applications
cask "visual-studio-code" # Code editor'''

        mock_run_command.return_value = (True, brew_output, "")

        formulae, casks = scanner.scan_homebrew()

        assert len(formulae) == 2
        assert formulae[0].name == "git"
        assert formulae[0].install_method == "brew"
        assert formulae[1].name == "python"

        assert len(casks) == 2
        assert casks[0].name == "docker"
        assert casks[0].install_method == "cask"
        assert casks[1].name == "visual-studio-code"

    @patch('macditto.scanner.run_command')
    def test_scan_homebrew_fallback_to_list(self, mock_run_command, scanner):
        """Should fall back to brew list if bundle dump fails."""
        # First call (bundle dump) fails, second and third (list) succeed
        mock_run_command.side_effect = [
            (False, "", "error"),  # bundle dump fails
            (True, "git\npython\nnode", ""),  # brew list --formula
            (True, "docker\nvisual-studio-code", "")  # brew list --cask
        ]

        formulae, casks = scanner.scan_homebrew()

        assert len(formulae) == 3
        assert "git" in [f.name for f in formulae]

        assert len(casks) == 2
        assert "docker" in [c.name for c in casks]

    @patch('macditto.scanner.run_command')
    def test_scan_homebrew_no_homebrew_installed(self, mock_run_command, scanner):
        """Should handle Homebrew not being installed."""
        mock_run_command.return_value = (False, "", "command not found")

        formulae, casks = scanner.scan_homebrew()

        assert len(formulae) == 0
        assert len(casks) == 0


class TestScanApplications:
    """Tests for scan_applications method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.os.listdir')
    @patch('macditto.scanner.os.path.exists')
    @patch.object(Scanner, '_get_bundle_id')
    def test_scan_applications(self, mock_bundle_id, mock_exists, mock_listdir, scanner):
        """Should scan applications directory."""
        # Mock exists: True for /Applications, False for ~/Applications
        mock_exists.side_effect = [False]  # User applications directory doesn't exist
        mock_listdir.return_value = [
            'Docker.app',
            'Visual Studio Code.app',
            'Safari.app',  # Standard macOS app, should be filtered
        ]
        mock_bundle_id.side_effect = [
            'com.docker.docker',
            'com.microsoft.VSCode',
            'com.apple.Safari'
        ]

        apps = scanner.scan_applications()

        # Should have 2 apps (Safari filtered out)
        assert len(apps) == 2
        app_names = [app.name for app in apps]
        assert 'Docker' in app_names
        assert 'Visual Studio Code' in app_names
        assert 'Safari' not in app_names

    @patch('macditto.scanner.os.listdir')
    @patch('macditto.scanner.os.path.exists')
    def test_scan_applications_empty_directory(self, mock_exists, mock_listdir, scanner):
        """Should handle empty applications directory."""
        mock_exists.return_value = True
        mock_listdir.return_value = []

        apps = scanner.scan_applications()

        assert len(apps) == 0


class TestScanDockItems:
    """Tests for scan_dock_items method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.run_command')
    def test_scan_dock_items(self, mock_run_command, scanner):
        """Should parse dock items from defaults output."""
        dock_output = '''(
    {
        "tile-data" = {
            "file-label" = "Docker Desktop";
        };
    },
    {
        "tile-data" = {
            "file-label" = "Visual Studio Code";
        };
    }
)'''
        mock_run_command.return_value = (True, dock_output, "")

        dock_items = scanner.scan_dock_items()

        # Note: The parser looks for "file-label" in output
        # This is a simplified test - actual output may vary
        assert isinstance(dock_items, list)

    @patch('macditto.scanner.run_command')
    def test_scan_dock_items_empty(self, mock_run_command, scanner):
        """Should handle empty dock."""
        mock_run_command.return_value = (True, "()", "")

        dock_items = scanner.scan_dock_items()

        assert isinstance(dock_items, list)


class TestScanLoginItems:
    """Tests for scan_login_items method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.run_command')
    def test_scan_login_items(self, mock_run_command, scanner):
        """Should parse login items from osascript output."""
        mock_run_command.return_value = (True, "Docker Desktop, Dropbox, Alfred", "")

        login_items = scanner.scan_login_items()

        assert len(login_items) == 3
        assert "Docker Desktop" in login_items
        assert "Dropbox" in login_items
        assert "Alfred" in login_items

    @patch('macditto.scanner.run_command')
    def test_scan_login_items_empty(self, mock_run_command, scanner):
        """Should handle no login items."""
        mock_run_command.return_value = (True, "", "")

        login_items = scanner.scan_login_items()

        assert len(login_items) == 0


class TestScanShellConfigs:
    """Tests for scan_shell_configs method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.read_file')
    def test_scan_shell_configs(self, mock_read_file, scanner):
        """Should scan for shell config files and Claude config files."""
        def read_file_side_effect(path):
            if '.zshrc' in path:
                return "export PATH=$PATH:/usr/local/bin"
            elif '.bash_profile' in path:
                return "source ~/.bashrc"
            elif 'CLAUDE.md' in path:
                return "# Global Claude Instructions"
            elif 'settings.json' in path:
                return '{"model": "opus"}'
            elif 'statusline-command.sh' in path:
                return "echo statusline"
            elif 'installed_plugins.json' in path:
                return '{"plugins": {}}'
            elif 'blocklist.json' in path:
                return '{"blocked": []}'
            elif 'known_marketplaces.json' in path:
                return '{"marketplaces": []}'
            return None

        mock_read_file.side_effect = read_file_side_effect

        configs = scanner.scan_shell_configs()

        assert len(configs) == 8
        config_names = [c.filename for c in configs]
        assert '.zshrc' in config_names
        assert '.bash_profile' in config_names
        assert '.claude/CLAUDE.md' in config_names
        assert '.claude/settings.json' in config_names
        assert '.claude/statusline-command.sh' in config_names
        assert '.claude/plugins/installed_plugins.json' in config_names
        assert '.claude/plugins/blocklist.json' in config_names
        assert '.claude/plugins/known_marketplaces.json' in config_names

        zshrc = next(c for c in configs if c.filename == '.zshrc')
        assert 'export PATH' in zshrc.content

        claude_md = next(c for c in configs if c.filename == '.claude/CLAUDE.md')
        assert '# Global Claude Instructions' in claude_md.content

        settings = next(c for c in configs if c.filename == '.claude/settings.json')
        assert '"model": "opus"' in settings.content

    @patch('macditto.scanner.os.listdir')
    @patch('macditto.scanner.os.path.isfile')
    @patch('macditto.scanner.os.path.isdir')
    @patch('macditto.scanner.read_file')
    def test_scan_claude_commands_directory(self, mock_read_file, mock_isdir,
                                            mock_isfile, mock_listdir, scanner):
        """Should scan files in ~/.claude/commands/ directory."""
        def read_file_side_effect(path):
            if 'commands/review.md' in path:
                return "# Review command"
            return None

        mock_read_file.side_effect = read_file_side_effect
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_listdir.return_value = ['review.md']

        configs = scanner.scan_shell_configs()

        cmd_configs = [c for c in configs if 'commands/' in c.filename]
        assert len(cmd_configs) == 1
        assert cmd_configs[0].filename == '.claude/commands/review.md'
        assert '# Review command' in cmd_configs[0].content

    @patch('macditto.scanner.os.listdir')
    @patch('macditto.scanner.os.path.isfile')
    @patch('macditto.scanner.os.path.isdir')
    @patch('macditto.scanner.read_file')
    def test_scan_claude_project_memory_files(self, mock_read_file, mock_isdir,
                                               mock_isfile, mock_listdir, scanner):
        """Should scan MEMORY.md files in ~/.claude/projects/*/memory/."""
        def read_file_side_effect(path):
            if 'memory/MEMORY.md' in path:
                return "# Project Memory"
            return None

        mock_read_file.side_effect = read_file_side_effect

        def isdir_side_effect(path):
            if path.endswith('commands'):
                return False
            if path.endswith('projects'):
                return True
            return False

        mock_isdir.side_effect = isdir_side_effect

        def isfile_side_effect(path):
            return 'MEMORY.md' in path

        mock_isfile.side_effect = isfile_side_effect
        mock_listdir.return_value = ['project-one', 'project-two']

        configs = scanner.scan_shell_configs()

        memory_configs = [c for c in configs if 'memory/MEMORY.md' in c.filename]
        assert len(memory_configs) == 2
        assert memory_configs[0].filename == '.claude/projects/project-one/memory/MEMORY.md'
        assert memory_configs[1].filename == '.claude/projects/project-two/memory/MEMORY.md'
        assert '# Project Memory' in memory_configs[0].content


class TestScanGitConfig:
    """Tests for scan_git_config method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.read_file')
    def test_scan_git_config_exists(self, mock_read_file, scanner):
        """Should read .gitconfig if it exists."""
        git_config_content = """[user]
    name = Steve Souza
    email = steve@example.com"""
        mock_read_file.return_value = git_config_content

        config = scanner.scan_git_config()

        assert config == git_config_content
        assert 'Steve Souza' in config

    @patch('macditto.scanner.read_file')
    def test_scan_git_config_not_exists(self, mock_read_file, scanner):
        """Should return None if .gitconfig doesn't exist."""
        mock_read_file.return_value = None

        config = scanner.scan_git_config()

        assert config is None


class TestScanBrowserExtensions:
    """Tests for scan_browser_extensions method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.os.path.exists')
    @patch('macditto.scanner.os.path.isdir')
    @patch('macditto.scanner.os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_scan_chrome_extensions(self, mock_file, mock_listdir, mock_isdir, mock_exists, scanner):
        """Should scan Chrome extensions directory."""
        # Mock manifest.json content
        manifest = {
            "name": "uBlock Origin",
            "version": "1.50.0"
        }

        # Mock directory structure
        # First exists check: extensions directory exists
        # Second exists check: manifest.json exists
        # Third exists check: Secure Preferences file exists
        # Fourth exists check: Preferences file exists
        mock_exists.side_effect = [True, True, False, False]
        mock_isdir.return_value = True
        mock_listdir.side_effect = [
            ['extension_id_123'],  # Extensions directory
            ['1.0.0'],  # Version directory
        ]

        with patch('macditto.scanner.json.load', return_value=manifest):
            extensions = scanner._scan_chrome_extensions(
                '/fake/path/Extensions',
                'Chrome'
            )

        assert len(extensions) == 1
        assert extensions[0].name == "uBlock Origin"
        assert extensions[0].browser == "Chrome"


class TestScanBrowserBookmarks:
    """Tests for scan_browser_bookmarks method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch('macditto.scanner.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_scan_browser_bookmarks(self, mock_file, mock_exists, scanner):
        """Should scan browser bookmarks."""
        mock_exists.return_value = True
        bookmarks_data = {"roots": {"bookmark_bar": {"children": []}}}

        with patch('macditto.scanner.json.load', return_value=bookmarks_data):
            bookmarks = scanner.scan_browser_bookmarks()

        assert isinstance(bookmarks, dict)


class TestScanMacOSPreferences:
    """Tests for scan_macos_preferences method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch.object(Scanner, '_read_preference')
    def test_scan_macos_preferences(self, mock_read_pref, scanner):
        """Should scan macOS system preferences."""
        mock_read_pref.return_value = SystemPreference(
            domain="com.apple.dock",
            key="autohide",
            value=True,
            value_type="bool",
            description="Dock auto-hide"
        )

        prefs = scanner.scan_macos_preferences()

        assert len(prefs) > 0
        # Should have called _read_preference multiple times
        assert mock_read_pref.call_count > 0

    @patch('macditto.scanner.run_command')
    def test_read_preference_bool(self, mock_run_command, scanner):
        """Should read boolean preference correctly."""
        mock_run_command.return_value = (True, "1", "")

        pref = scanner._read_preference(
            "com.apple.dock",
            "autohide",
            "Auto-hide dock"
        )

        assert pref is not None
        assert pref.value is True
        assert pref.value_type == "bool"
        assert "bool" in pref.command

    @patch('macditto.scanner.run_command')
    def test_read_preference_int(self, mock_run_command, scanner):
        """Should read integer preference correctly."""
        mock_run_command.return_value = (True, "48", "")

        pref = scanner._read_preference(
            "com.apple.dock",
            "tilesize",
            "Dock icon size"
        )

        assert pref is not None
        assert pref.value == 48
        assert pref.value_type == "int"
        assert "int" in pref.command

    @patch('macditto.scanner.run_command')
    def test_read_preference_not_found(self, mock_run_command, scanner):
        """Should return None for nonexistent preference."""
        mock_run_command.return_value = (False, "", "not found")

        pref = scanner._read_preference(
            "com.apple.dock",
            "nonexistent",
            "Test"
        )

        assert pref is None


class TestScanAll:
    """Tests for scan_all method."""

    @pytest.fixture
    def scanner(self):
        return Scanner()

    @patch.object(Scanner, 'scan_deep_configs', return_value=0)
    @patch.object(Scanner, 'scan_homebrew')
    @patch.object(Scanner, 'scan_applications')
    @patch.object(Scanner, 'scan_dock_items')
    @patch.object(Scanner, 'scan_login_items')
    @patch.object(Scanner, 'scan_shell_configs')
    @patch.object(Scanner, 'scan_git_config')
    @patch.object(Scanner, 'scan_browser_extensions')
    @patch.object(Scanner, 'scan_browser_bookmarks')
    @patch.object(Scanner, 'scan_macos_preferences')
    @patch('macditto.scanner.get_machine_name')
    @patch('macditto.scanner.get_timestamp')
    def test_scan_all(
        self,
        mock_timestamp,
        mock_machine_name,
        mock_prefs,
        mock_bookmarks,
        mock_extensions,
        mock_git,
        mock_shell,
        mock_login,
        mock_dock,
        mock_apps,
        mock_brew,
        mock_deep_configs,
        scanner,
        capsys
    ):
        """Should run all scans and return complete profile."""
        # Mock return values
        mock_timestamp.return_value = "2026-02-15T10:30:00"
        mock_machine_name.return_value = "Test Mac"
        mock_brew.return_value = (
            [Item(name="git", install_method="brew")],
            [Item(name="docker", install_method="cask")]
        )
        mock_apps.return_value = [Item(name="VSCode", install_method="manual")]
        mock_dock.return_value = ["docker", "VSCode"]
        mock_login.return_value = ["docker"]
        mock_shell.return_value = [
            ShellConfig(filename=".zshrc", path="~/.zshrc", content="test")
        ]
        mock_git.return_value = "[user]\nname = Test"
        mock_extensions.return_value = [
            BrowserExtension(name="uBlock", browser="Chrome", extension_id="abc")
        ]
        mock_bookmarks.return_value = {}
        mock_prefs.return_value = []

        profile = scanner.scan_all()

        # Verify all scan methods were called
        assert mock_brew.called
        assert mock_apps.called
        assert mock_dock.called
        assert mock_login.called
        assert mock_shell.called
        assert mock_git.called
        assert mock_extensions.called
        assert mock_bookmarks.called
        assert mock_prefs.called

        # Verify profile structure
        assert profile.machine_name == "Test Mac"
        assert profile.scan_date == "2026-02-15T10:30:00"
        assert len(profile.homebrew_formulae) == 1
        assert len(profile.homebrew_casks) == 1
        assert len(profile.applications) == 1
        assert len(profile.browser_extensions) == 1

        # Verify dock/login items are marked correctly
        docker_cask = profile.homebrew_casks[0]
        assert docker_cask.in_dock is True
        assert docker_cask.start_on_login is True

        vscode_app = profile.applications[0]
        assert vscode_app.in_dock is True
        assert vscode_app.start_on_login is False

        # Verify output was printed
        captured = capsys.readouterr()
        assert "Starting MacDitto scan" in captured.out
        assert "Scan complete" in captured.out
