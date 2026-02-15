"""
Tests for MacDitto data models.
"""

import pytest
import json
from macditto.models import (
    Item, BrowserExtension, ShellConfig, SystemPreference, ScanProfile
)


class TestItem:
    """Tests for Item data model."""

    def test_item_creation_with_defaults(self):
        """Should create Item with default values."""
        item = Item(name="Test App")
        assert item.name == "Test App"
        assert item.install_method == "manual"
        assert item.enabled is True
        assert item.in_dock is False
        assert item.start_on_login is False
        assert item.category == "Other"
        assert item.brew_package is None

    def test_item_creation_with_custom_values(self):
        """Should create Item with custom values."""
        item = Item(
            name="Docker Desktop",
            install_method="cask",
            enabled=True,
            in_dock=True,
            start_on_login=False,
            category="Development",
            brew_package="docker"
        )
        assert item.name == "Docker Desktop"
        assert item.install_method == "cask"
        assert item.in_dock is True
        assert item.category == "Development"
        assert item.brew_package == "docker"

    def test_item_to_dict(self):
        """Should convert Item to dictionary."""
        item = Item(
            name="Test",
            install_method="brew",
            category="Development"
        )
        data = item.to_dict()
        assert isinstance(data, dict)
        assert data['name'] == "Test"
        assert data['install_method'] == "brew"
        assert data['category'] == "Development"
        # None values should be omitted
        assert 'brew_package' not in data or data['brew_package'] is None


class TestBrowserExtension:
    """Tests for BrowserExtension data model."""

    def test_browser_extension_creation(self):
        """Should create BrowserExtension."""
        ext = BrowserExtension(
            name="uBlock Origin",
            browser="Chrome",
            extension_id="cjpalhdlnbpafiamejdnhcphjbkeiagm",
            version="1.50.0"
        )
        assert ext.name == "uBlock Origin"
        assert ext.browser == "Chrome"
        assert ext.extension_id == "cjpalhdlnbpafiamejdnhcphjbkeiagm"
        assert ext.enabled is True

    def test_browser_extension_to_dict(self):
        """Should convert BrowserExtension to dictionary."""
        ext = BrowserExtension(
            name="Test Extension",
            browser="Brave",
            extension_id="abc123"
        )
        data = ext.to_dict()
        assert data['name'] == "Test Extension"
        assert data['browser'] == "Brave"
        assert data['extension_id'] == "abc123"


class TestShellConfig:
    """Tests for ShellConfig data model."""

    def test_shell_config_creation(self):
        """Should create ShellConfig."""
        config = ShellConfig(
            filename=".zshrc",
            path="/Users/test/.zshrc",
            content="export PATH=$PATH:/usr/local/bin"
        )
        assert config.filename == ".zshrc"
        assert config.path == "/Users/test/.zshrc"
        assert "export PATH" in config.content
        assert config.backup is True

    def test_shell_config_to_dict(self):
        """Should convert ShellConfig to dictionary."""
        config = ShellConfig(
            filename=".bashrc",
            path="/Users/test/.bashrc",
            content="alias ll='ls -la'"
        )
        data = config.to_dict()
        assert data['filename'] == ".bashrc"
        assert data['content'] == "alias ll='ls -la'"


class TestSystemPreference:
    """Tests for SystemPreference data model."""

    def test_system_preference_creation(self):
        """Should create SystemPreference."""
        pref = SystemPreference(
            domain="com.apple.dock",
            key="autohide",
            value=True,
            value_type="bool",
            description="Dock auto-hide enabled",
            command="defaults write com.apple.dock autohide -bool true"
        )
        assert pref.domain == "com.apple.dock"
        assert pref.key == "autohide"
        assert pref.value is True
        assert pref.value_type == "bool"

    def test_system_preference_to_dict(self):
        """Should convert SystemPreference to dictionary."""
        pref = SystemPreference(
            domain="com.apple.dock",
            key="tilesize",
            value=48,
            value_type="int"
        )
        data = pref.to_dict()
        assert data['domain'] == "com.apple.dock"
        assert data['value'] == 48


class TestScanProfile:
    """Tests for ScanProfile data model."""

    def test_scan_profile_creation(self):
        """Should create ScanProfile with defaults."""
        profile = ScanProfile(
            scan_date="2026-02-15T10:30:00",
            machine_name="Test Mac"
        )
        assert profile.scan_date == "2026-02-15T10:30:00"
        assert profile.machine_name == "Test Mac"
        assert isinstance(profile.homebrew_formulae, list)
        assert len(profile.homebrew_formulae) == 0

    def test_scan_profile_with_data(self):
        """Should create ScanProfile with populated data."""
        item = Item(name="Docker", install_method="cask")
        ext = BrowserExtension(name="uBlock", browser="Chrome", extension_id="abc")

        profile = ScanProfile(
            scan_date="2026-02-15T10:30:00",
            machine_name="Test Mac",
            homebrew_casks=[item],
            browser_extensions=[ext]
        )

        assert len(profile.homebrew_casks) == 1
        assert profile.homebrew_casks[0].name == "Docker"
        assert len(profile.browser_extensions) == 1
        assert profile.browser_extensions[0].name == "uBlock"

    def test_scan_profile_to_dict(self):
        """Should convert ScanProfile to dictionary."""
        item = Item(name="Test", category="Development")
        profile = ScanProfile(
            scan_date="2026-02-15T10:30:00",
            machine_name="Test Mac",
            homebrew_formulae=[item]
        )

        data = profile.to_dict()
        assert isinstance(data, dict)
        assert data['scan_date'] == "2026-02-15T10:30:00"
        assert data['machine_name'] == "Test Mac"
        assert len(data['homebrew_formulae']) == 1
        assert data['homebrew_formulae'][0]['name'] == "Test"

    def test_scan_profile_to_json(self):
        """Should convert ScanProfile to JSON string."""
        profile = ScanProfile(
            scan_date="2026-02-15T10:30:00",
            machine_name="Test Mac"
        )
        json_str = profile.to_json()
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data['machine_name'] == "Test Mac"

    def test_scan_profile_save_and_load(self, tmp_path):
        """Should save and load ScanProfile from file."""
        # Create profile with data
        item = Item(name="Docker", install_method="cask", category="Development")
        profile = ScanProfile(
            scan_date="2026-02-15T10:30:00",
            machine_name="Test Mac",
            homebrew_casks=[item]
        )

        # Save to file
        filepath = tmp_path / "profile.json"
        profile.save(str(filepath))

        # Load from file
        loaded_profile = ScanProfile.load(str(filepath))
        assert loaded_profile.machine_name == "Test Mac"
        assert len(loaded_profile.homebrew_casks) == 1
        assert loaded_profile.homebrew_casks[0].name == "Docker"
        assert loaded_profile.homebrew_casks[0].category == "Development"

    def test_scan_profile_from_dict(self):
        """Should create ScanProfile from dictionary."""
        data = {
            "scan_date": "2026-02-15T10:30:00",
            "machine_name": "Test Mac",
            "homebrew_formulae": [
                {"name": "git", "install_method": "brew", "category": "Development"}
            ],
            "browser_extensions": [
                {"name": "uBlock", "browser": "Chrome", "extension_id": "abc123"}
            ]
        }

        profile = ScanProfile.from_dict(data)
        assert profile.machine_name == "Test Mac"
        assert len(profile.homebrew_formulae) == 1
        assert profile.homebrew_formulae[0].name == "git"
        assert len(profile.browser_extensions) == 1
        assert profile.browser_extensions[0].extension_id == "abc123"
