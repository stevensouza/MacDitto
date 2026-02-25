"""
Data models for MacDitto scan profiles and configuration items.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class Item:
    """
    Represents a single software item, application, or configuration.

    Attributes:
        name: Display name of the item
        install_method: How to install (brew, cask, app_store, manual, mas)
        enabled: Whether user wants this installed on target machine
        in_dock: Whether item appears in Dock
        start_on_login: Whether item starts automatically on login
        category: Auto-detected category (Development, Productivity, etc.)
        brew_package: Homebrew package name if applicable
        manual_instructions: Human-readable install steps for non-automatable items
        url: Download URL or account login URL
        metadata: Additional item-specific data
    """
    name: str
    install_method: str = "manual"
    enabled: bool = True
    in_dock: bool = False
    start_on_login: bool = False
    category: str = "Other"
    brew_package: Optional[str] = None
    manual_instructions: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Item to dictionary, omitting None values."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class BrowserExtension:
    """
    Represents a browser extension.

    Attributes:
        name: Extension name
        browser: Browser name (Chrome, Brave, etc.)
        extension_id: Unique extension identifier
        version: Extension version
        enabled: Whether to reinstall on target
        store_url: Chrome Web Store or extension download URL
    """
    name: str
    browser: str
    extension_id: str
    version: Optional[str] = None
    enabled: bool = True
    store_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert BrowserExtension to dictionary."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class ShellConfig:
    """
    Represents a shell configuration file.

    Attributes:
        filename: Config file name (.zshrc, .bash_profile, etc.)
        path: Full path to config file
        content: File contents
        backup: Whether to backup existing file on target before overwriting
    """
    filename: str
    path: str
    content: str
    backup: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert ShellConfig to dictionary."""
        return asdict(self)


@dataclass
class SystemPreference:
    """
    Represents a macOS system preference setting.

    Attributes:
        domain: Preference domain (e.g., com.apple.dock)
        key: Preference key
        value: Preference value
        value_type: Value type (string, int, bool, etc.)
        description: Human-readable description of what this setting does
        command: Full defaults write command to apply this setting
    """
    domain: str
    key: str
    value: Any
    value_type: str
    description: Optional[str] = None
    command: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert SystemPreference to dictionary."""
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class ScanProfile:
    """
    Complete scan profile containing all discovered environment data.

    Attributes:
        scan_date: ISO timestamp of when scan was performed
        machine_name: Name of the scanned machine
        homebrew_formulae: List of Homebrew packages
        homebrew_casks: List of Homebrew casks
        applications: List of installed applications
        accounts: List of accounts/web services requiring manual login
        browser_extensions: List of browser extensions
        browser_bookmarks: Browser bookmarks data
        shell_configs: Shell configuration files
        git_config: Git configuration
        system_preferences: macOS system preferences
        dock_items: Items in the Dock
        login_items: Items that start on login
    """
    scan_date: str
    machine_name: str
    homebrew_formulae: List[Item] = field(default_factory=list)
    homebrew_casks: List[Item] = field(default_factory=list)
    applications: List[Item] = field(default_factory=list)
    accounts: List[Item] = field(default_factory=list)
    browser_extensions: List[BrowserExtension] = field(default_factory=list)
    browser_bookmarks: Dict[str, Any] = field(default_factory=dict)
    shell_configs: List[ShellConfig] = field(default_factory=list)
    git_config: Optional[str] = None
    system_preferences: List[SystemPreference] = field(default_factory=list)
    dock_items: List[str] = field(default_factory=list)
    login_items: List[str] = field(default_factory=list)
    ssh_config: str = ""
    ssh_key_names: List[str] = field(default_factory=list)
    crontab: str = ""
    setup_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert ScanProfile to dictionary with nested object conversion."""
        return {
            "scan_date": self.scan_date,
            "machine_name": self.machine_name,
            "homebrew_formulae": [item.to_dict() for item in self.homebrew_formulae],
            "homebrew_casks": [item.to_dict() for item in self.homebrew_casks],
            "applications": [item.to_dict() for item in self.applications],
            "accounts": [item.to_dict() for item in self.accounts],
            "browser_extensions": [ext.to_dict() for ext in self.browser_extensions],
            "browser_bookmarks": self.browser_bookmarks,
            "shell_configs": [cfg.to_dict() for cfg in self.shell_configs],
            "git_config": self.git_config,
            "system_preferences": [pref.to_dict() for pref in self.system_preferences],
            "dock_items": self.dock_items,
            "login_items": self.login_items,
            "ssh_config": self.ssh_config,
            "ssh_key_names": self.ssh_key_names,
            "crontab": self.crontab,
            "setup_notes": self.setup_notes,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert ScanProfile to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save(self, filepath: str) -> None:
        """Save ScanProfile to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScanProfile':
        """Create ScanProfile from dictionary."""
        profile = cls(
            scan_date=data.get("scan_date", ""),
            machine_name=data.get("machine_name", ""),
        )

        # Convert items
        profile.homebrew_formulae = [
            Item(**item) for item in data.get("homebrew_formulae", [])
        ]
        profile.homebrew_casks = [
            Item(**item) for item in data.get("homebrew_casks", [])
        ]
        profile.applications = [
            Item(**item) for item in data.get("applications", [])
        ]
        profile.accounts = [
            Item(**item) for item in data.get("accounts", [])
        ]
        profile.browser_extensions = [
            BrowserExtension(**ext) for ext in data.get("browser_extensions", [])
        ]
        profile.browser_bookmarks = data.get("browser_bookmarks", {})
        profile.shell_configs = [
            ShellConfig(**cfg) for cfg in data.get("shell_configs", [])
        ]
        profile.git_config = data.get("git_config")
        profile.system_preferences = [
            SystemPreference(**pref) for pref in data.get("system_preferences", [])
        ]
        profile.dock_items = data.get("dock_items", [])
        profile.login_items = data.get("login_items", [])
        profile.ssh_config = data.get("ssh_config", "")
        profile.ssh_key_names = data.get("ssh_key_names", [])
        profile.crontab = data.get("crontab", "")
        profile.setup_notes = data.get("setup_notes", "")

        return profile

    @classmethod
    def load(cls, filepath: str) -> 'ScanProfile':
        """Load ScanProfile from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
