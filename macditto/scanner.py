"""
Scanner module for MacDitto - scans macOS environment for installed software and configurations.
"""

import os
import json
import plistlib
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    ScanProfile, Item, BrowserExtension, ShellConfig, SystemPreference
)
from .utils import (
    get_home_directory, run_command, detect_category, is_standard_macos_app,
    get_machine_name, file_exists, read_file, get_timestamp,
    get_brew_cask_name, check_brew_cask_exists, get_manual_app_description
)


class Scanner:
    """
    Main scanner class for discovering macOS environment configuration.

    Scans:
    - Homebrew formulae and casks
    - Installed applications
    - Dock items
    - Login items
    - Shell configurations
    - Git configuration
    - Browser extensions and bookmarks
    - macOS system preferences
    """

    def __init__(self, progress_callback=None):
        """
        Initialize Scanner with home directory and common paths.

        Args:
            progress_callback: Optional callback function for progress updates.
                               Called with (step_name, step_number, total_steps, item_counts)
        """
        self.home_dir = get_home_directory()
        self.applications_dir = "/Applications"
        self.user_applications_dir = os.path.join(self.home_dir, "Applications")
        self.progress_callback = progress_callback

    def scan_homebrew(self) -> tuple[List[Item], List[Item]]:
        """
        Scan Homebrew for installed formulae and casks.

        Uses `brew bundle dump` to get directly installed packages (not dependencies).
        Also uses `brew list` and `brew list --cask` as fallback.

        Returns:
            Tuple of (formulae: List[Item], casks: List[Item])
        """
        formulae = []
        casks = []

        # Try brew bundle dump first (gives only user-installed items)
        success, stdout, _ = run_command(['brew', 'bundle', 'dump', '--describe', '--file=-'])
        if success:
            for line in stdout.strip().split('\n'):
                if line.startswith('brew '):
                    # Extract package name from: brew "package" # Description
                    parts = line.split('"')
                    if len(parts) >= 2:
                        package_name = parts[1]
                        description = parts[2].strip().lstrip('#').strip() if len(parts) > 2 else ""
                        formulae.append(Item(
                            name=package_name,
                            install_method="brew",
                            brew_package=package_name,
                            category=detect_category(package_name),
                            metadata={"description": description} if description else {}
                        ))
                elif line.startswith('cask '):
                    # Extract cask name from: cask "package" # Description
                    parts = line.split('"')
                    if len(parts) >= 2:
                        cask_name = parts[1]
                        description = parts[2].strip().lstrip('#').strip() if len(parts) > 2 else ""
                        casks.append(Item(
                            name=cask_name,
                            install_method="cask",
                            brew_package=cask_name,
                            category=detect_category(cask_name),
                            metadata={"description": description} if description else {}
                        ))

        # Fallback: Use brew list if bundle dump didn't work
        if not formulae:
            success, stdout, _ = run_command(['brew', 'list', '--formula'])
            if success:
                for package in stdout.strip().split('\n'):
                    if package:
                        formulae.append(Item(
                            name=package,
                            install_method="brew",
                            brew_package=package,
                            category=detect_category(package)
                        ))

        if not casks:
            success, stdout, _ = run_command(['brew', 'list', '--cask'])
            if success:
                for cask in stdout.strip().split('\n'):
                    if cask:
                        casks.append(Item(
                            name=cask,
                            install_method="cask",
                            brew_package=cask,
                            category=detect_category(cask)
                        ))

        return formulae, casks

    def scan_applications(self) -> List[Item]:
        """
        Scan /Applications directory for installed apps.

        Excludes standard macOS apps and apps already captured via Homebrew casks.

        Returns:
            List of Item objects representing installed applications
        """
        applications = []

        # Scan both /Applications and ~/Applications
        app_dirs = [self.applications_dir]
        if os.path.exists(self.user_applications_dir):
            app_dirs.append(self.user_applications_dir)

        for app_dir in app_dirs:
            try:
                for item in os.listdir(app_dir):
                    if item.endswith('.app'):
                        app_name = item.replace('.app', '')

                        # Skip standard macOS apps
                        if is_standard_macos_app(app_name):
                            continue

                        # Try to get bundle identifier
                        bundle_id = self._get_bundle_id(os.path.join(app_dir, item))

                        # Skip if it's an Apple app
                        if bundle_id and is_standard_macos_app(app_name, bundle_id):
                            continue

                        # Check if app has a brew cask equivalent
                        brew_cask = get_brew_cask_name(app_name)
                        install_method = "manual"
                        brew_package = None

                        if brew_cask:
                            # Verify the cask actually exists
                            if check_brew_cask_exists(brew_cask):
                                install_method = "cask"
                                brew_package = brew_cask

                        metadata = {
                            "path": os.path.join(app_dir, item)
                        }
                        if bundle_id:
                            metadata["bundle_id"] = bundle_id
                        if brew_cask and not brew_package:
                            # Cask mapping exists but couldn't verify - note it
                            metadata["suggested_cask"] = brew_cask

                        applications.append(Item(
                            name=app_name,
                            install_method=install_method,
                            brew_package=brew_package,
                            category=detect_category(app_name),
                            metadata=metadata
                        ))
            except PermissionError:
                # Skip directories we can't read
                continue

        return applications

    def _get_bundle_id(self, app_path: str) -> Optional[str]:
        """
        Get bundle identifier from application Info.plist.

        Args:
            app_path: Path to .app bundle

        Returns:
            Bundle identifier string or None if not found
        """
        info_plist_path = os.path.join(app_path, 'Contents', 'Info.plist')
        if not os.path.exists(info_plist_path):
            return None

        try:
            with open(info_plist_path, 'rb') as f:
                plist = plistlib.load(f)
                return plist.get('CFBundleIdentifier')
        except Exception:
            return None

    def scan_dock_items(self) -> List[str]:
        """
        Scan Dock for pinned applications.

        Uses `defaults read com.apple.dock` to get persistent apps in Dock.

        Returns:
            List of application names in Dock
        """
        dock_items = []

        success, stdout, _ = run_command(['defaults', 'read', 'com.apple.dock', 'persistent-apps'])
        if success:
            try:
                # Parse the plist output
                # Look for file-label values which contain app names
                lines = stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'file-label' in line and i + 1 < len(lines):
                        # Extract app name from next line
                        next_line = lines[i + 1].strip()
                        if next_line:
                            # Remove quotes and semicolon
                            app_name = next_line.replace('"', '').replace(';', '').strip()
                            if app_name:
                                dock_items.append(app_name)
            except Exception:
                pass

        # Alternative: parse as plist binary
        if not dock_items:
            try:
                success, stdout, _ = run_command(['defaults', 'export', 'com.apple.dock', '-'])
                if success:
                    plist = plistlib.loads(stdout.encode())
                    persistent_apps = plist.get('persistent-apps', [])
                    for app in persistent_apps:
                        tile_data = app.get('tile-data', {})
                        file_label = tile_data.get('file-label', '')
                        if file_label:
                            dock_items.append(file_label)
            except Exception:
                pass

        return dock_items

    def scan_login_items(self) -> List[str]:
        """
        Scan for applications that start automatically on login.

        Uses osascript to query System Events for login items.

        Returns:
            List of application names configured to start on login
        """
        login_items = []

        # Use osascript to get login items via System Events
        applescript = '''
        tell application "System Events"
            get the name of every login item
        end tell
        '''

        success, stdout, _ = run_command(['osascript', '-e', applescript])
        if success and stdout.strip():
            # Parse comma-separated list
            items = stdout.strip().split(', ')
            login_items = [item.strip() for item in items if item.strip()]

        return login_items

    def scan_shell_configs(self) -> List[ShellConfig]:
        """
        Scan for shell configuration files.

        Looks for: .zshrc, .zprofile, .bash_profile, .bashrc, .profile

        Returns:
            List of ShellConfig objects with file contents
        """
        shell_configs = []

        config_files = [
            '.zshrc',
            '.zprofile',
            '.bash_profile',
            '.bashrc',
            '.profile',
        ]

        for config_file in config_files:
            file_path = os.path.join(self.home_dir, config_file)
            content = read_file(file_path)
            if content is not None:
                shell_configs.append(ShellConfig(
                    filename=config_file,
                    path=file_path,
                    content=content
                ))

        return shell_configs

    def scan_git_config(self) -> Optional[str]:
        """
        Read Git configuration file.

        Returns:
            Contents of .gitconfig file or None if not found
        """
        git_config_path = os.path.join(self.home_dir, '.gitconfig')
        return read_file(git_config_path)

    def scan_browser_extensions(self) -> List[BrowserExtension]:
        """
        Scan for installed browser extensions.

        Supports:
        - Google Chrome
        - Brave Browser

        Returns:
            List of BrowserExtension objects
        """
        extensions = []

        # Chrome extension paths
        chrome_path = os.path.join(
            self.home_dir,
            'Library/Application Support/Google/Chrome/Default/Extensions'
        )
        extensions.extend(self._scan_chrome_extensions(chrome_path, 'Chrome'))

        # Brave extension paths
        brave_path = os.path.join(
            self.home_dir,
            'Library/Application Support/BraveSoftware/Brave-Browser/Default/Extensions'
        )
        extensions.extend(self._scan_chrome_extensions(brave_path, 'Brave'))

        return extensions

    def _scan_chrome_extensions(self, extensions_path: str, browser_name: str) -> List[BrowserExtension]:
        """
        Scan Chrome/Brave extensions directory.

        Args:
            extensions_path: Path to browser extensions directory
            browser_name: Browser name (Chrome, Brave, etc.)

        Returns:
            List of BrowserExtension objects
        """
        extensions = []

        # First, scan standard extensions folder
        if os.path.exists(extensions_path):
            try:
                for extension_id in os.listdir(extensions_path):
                    ext_path = os.path.join(extensions_path, extension_id)
                    if not os.path.isdir(ext_path):
                        continue

                    # Find latest version directory
                    try:
                        versions = os.listdir(ext_path)
                        if not versions:
                            continue

                        # Get the latest version (alphabetically last)
                        latest_version = sorted(versions)[-1]
                        manifest_path = os.path.join(ext_path, latest_version, 'manifest.json')

                        if os.path.exists(manifest_path):
                            with open(manifest_path, 'r', encoding='utf-8') as f:
                                manifest = json.load(f)
                                name = manifest.get('name', extension_id)
                                version = manifest.get('version', latest_version)

                                # Chrome Web Store URL
                                store_url = f"https://chrome.google.com/webstore/detail/{extension_id}"

                                extensions.append(BrowserExtension(
                                    name=name,
                                    browser=browser_name,
                                    extension_id=extension_id,
                                    version=version,
                                    store_url=store_url
                                ))
                    except Exception:
                        continue
            except PermissionError:
                pass

        # Now scan for developer mode extensions from Preferences file
        profile_dir = os.path.dirname(extensions_path)
        prefs_path = os.path.join(profile_dir, 'Preferences')

        if os.path.exists(prefs_path):
            try:
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    ext_settings = prefs.get('extensions', {}).get('settings', {})

                    for ext_id, ext_data in ext_settings.items():
                        # Check if this is a developer mode extension
                        # Location 4 = unpacked extension (developer mode)
                        location = ext_data.get('location', 0)
                        from_webstore = ext_data.get('from_webstore', True)

                        if location == 4 or not from_webstore:
                            # This is a developer extension
                            path = ext_data.get('path', '')
                            manifest_data = ext_data.get('manifest', {})

                            # Try to read manifest from the actual path
                            if path and os.path.exists(path):
                                manifest_path = os.path.join(path, 'manifest.json')
                                if os.path.exists(manifest_path):
                                    try:
                                        with open(manifest_path, 'r', encoding='utf-8') as mf:
                                            manifest_data = json.load(mf)
                                    except Exception:
                                        pass

                            name = manifest_data.get('name', ext_id)
                            version = manifest_data.get('version', 'dev')

                            # Mark as developer extension
                            store_url = f"Developer Extension (unpacked from: {path})" if path else "Developer Extension"

                            extensions.append(BrowserExtension(
                                name=f"{name} [DEV]",
                                browser=browser_name,
                                extension_id=ext_id,
                                version=version,
                                store_url=store_url
                            ))
            except Exception:
                pass

        return extensions

    def scan_browser_bookmarks(self) -> Dict[str, Any]:
        """
        Scan browser bookmarks.

        Supports:
        - Google Chrome
        - Brave Browser

        Returns:
            Dictionary with browser names as keys and bookmark data as values
        """
        bookmarks = {}

        # Chrome bookmarks
        chrome_bookmarks_path = os.path.join(
            self.home_dir,
            'Library/Application Support/Google/Chrome/Default/Bookmarks'
        )
        if os.path.exists(chrome_bookmarks_path):
            try:
                with open(chrome_bookmarks_path, 'r', encoding='utf-8') as f:
                    bookmarks['Chrome'] = json.load(f)
            except Exception:
                pass

        # Brave bookmarks
        brave_bookmarks_path = os.path.join(
            self.home_dir,
            'Library/Application Support/BraveSoftware/Brave-Browser/Default/Bookmarks'
        )
        if os.path.exists(brave_bookmarks_path):
            try:
                with open(brave_bookmarks_path, 'r', encoding='utf-8') as f:
                    bookmarks['Brave'] = json.load(f)
            except Exception:
                pass

        return bookmarks

    def scan_macos_preferences(self) -> List[SystemPreference]:
        """
        Scan macOS system preferences.

        Captures key customizations via `defaults read` commands:
        - Dock settings (size, position, auto-hide, magnification)
        - Trackpad settings (tap to click, scroll direction, gestures)
        - Keyboard settings (key repeat rate)
        - Finder preferences (show extensions, default view)
        - Screenshot settings (location, format)

        Returns:
            List of SystemPreference objects
        """
        preferences = []

        # Dock preferences
        dock_prefs = [
            ('com.apple.dock', 'tilesize', 'Dock icon size'),
            ('com.apple.dock', 'autohide', 'Dock auto-hide enabled'),
            ('com.apple.dock', 'magnification', 'Dock magnification enabled'),
            ('com.apple.dock', 'orientation', 'Dock position (left/bottom/right)'),
            ('com.apple.dock', 'show-recents', 'Show recent applications in Dock'),
        ]

        for domain, key, description in dock_prefs:
            pref = self._read_preference(domain, key, description)
            if pref:
                preferences.append(pref)

        # Trackpad preferences
        trackpad_prefs = [
            ('com.apple.AppleMultitouchTrackpad', 'Clicking', 'Tap to click'),
            ('NSGlobalDomain', 'com.apple.swipescrolldirection', 'Natural scroll direction'),
        ]

        for domain, key, description in trackpad_prefs:
            pref = self._read_preference(domain, key, description)
            if pref:
                preferences.append(pref)

        # Keyboard preferences
        keyboard_prefs = [
            ('NSGlobalDomain', 'KeyRepeat', 'Key repeat rate'),
            ('NSGlobalDomain', 'InitialKeyRepeat', 'Initial key repeat delay'),
        ]

        for domain, key, description in keyboard_prefs:
            pref = self._read_preference(domain, key, description)
            if pref:
                preferences.append(pref)

        # Finder preferences
        finder_prefs = [
            ('NSGlobalDomain', 'AppleShowAllExtensions', 'Show all file extensions'),
            ('com.apple.finder', 'ShowPathbar', 'Show path bar'),
            ('com.apple.finder', 'ShowStatusBar', 'Show status bar'),
        ]

        for domain, key, description in finder_prefs:
            pref = self._read_preference(domain, key, description)
            if pref:
                preferences.append(pref)

        # Screenshot preferences
        screenshot_prefs = [
            ('com.apple.screencapture', 'location', 'Screenshot save location'),
            ('com.apple.screencapture', 'type', 'Screenshot file format'),
        ]

        for domain, key, description in screenshot_prefs:
            pref = self._read_preference(domain, key, description)
            if pref:
                preferences.append(pref)

        return preferences

    def _read_preference(self, domain: str, key: str, description: str) -> Optional[SystemPreference]:
        """
        Read a single system preference.

        Args:
            domain: Preference domain (e.g., com.apple.dock)
            key: Preference key
            description: Human-readable description

        Returns:
            SystemPreference object or None if preference not found
        """
        success, stdout, _ = run_command(['defaults', 'read', domain, key])
        if not success:
            return None

        value = stdout.strip()

        # Determine value type
        value_type = 'string'
        actual_value: Any = value

        if value.lower() in ('true', '1'):
            value_type = 'bool'
            actual_value = True
        elif value.lower() in ('false', '0'):
            value_type = 'bool'
            actual_value = False
        elif value.isdigit():
            value_type = 'int'
            actual_value = int(value)
        elif value.replace('.', '').replace('-', '').isdigit():
            value_type = 'float'
            actual_value = float(value)

        # Generate defaults write command
        if value_type == 'bool':
            command = f"defaults write {domain} {key} -bool {str(actual_value).lower()}"
        elif value_type == 'int':
            command = f"defaults write {domain} {key} -int {actual_value}"
        elif value_type == 'float':
            command = f"defaults write {domain} {key} -float {actual_value}"
        else:
            command = f"defaults write {domain} {key} -string \"{actual_value}\""

        return SystemPreference(
            domain=domain,
            key=key,
            value=actual_value,
            value_type=value_type,
            description=description,
            command=command
        )

    def fetch_brew_descriptions(self, packages: List[str]) -> Dict[str, str]:
        """
        Fetch descriptions for Homebrew formulae using brew info --json=v2.

        Args:
            packages: List of formula package names

        Returns:
            Dictionary mapping package name to description
        """
        descriptions = {}
        if not packages:
            return descriptions

        try:
            success, stdout, _ = run_command(
                ['brew', 'info', '--json=v2'] + packages, timeout=60
            )
            if success:
                data = json.loads(stdout)
                for formula in data.get('formulae', []):
                    name = formula.get('name', '')
                    desc = formula.get('desc', '')
                    if name and desc:
                        descriptions[name] = desc
        except Exception:
            pass

        return descriptions

    def fetch_cask_descriptions(self, casks: List[str]) -> Dict[str, str]:
        """
        Fetch descriptions for Homebrew casks using brew info --json=v2 --cask.

        Args:
            casks: List of cask package names

        Returns:
            Dictionary mapping cask name to description
        """
        descriptions = {}
        if not casks:
            return descriptions

        try:
            success, stdout, _ = run_command(
                ['brew', 'info', '--json=v2', '--cask'] + casks, timeout=60
            )
            if success:
                data = json.loads(stdout)
                for cask in data.get('casks', []):
                    token = cask.get('token', '')
                    desc = cask.get('desc', '')
                    if token and desc:
                        descriptions[token] = desc
        except Exception:
            pass

        return descriptions

    def scan_all(self) -> ScanProfile:
        """
        Run all scans and return unified ScanProfile.

        This is the main entry point for scanning the entire system.

        Returns:
            Complete ScanProfile with all discovered data
        """
        print("Starting MacDitto scan...")

        # Get machine info
        machine_name = get_machine_name()
        scan_date = get_timestamp()

        print(f"Scanning {machine_name}...")

        # Create profile
        profile = ScanProfile(
            scan_date=scan_date,
            machine_name=machine_name
        )

        # Initialize item counts dict
        item_counts = {}
        total_steps = 11

        # Step 1: Scan Homebrew
        if self.progress_callback:
            self.progress_callback("Scanning Homebrew packages", 1, total_steps, item_counts)
        print("Scanning Homebrew packages...")
        formulae, casks = self.scan_homebrew()
        profile.homebrew_formulae = formulae
        profile.homebrew_casks = casks
        item_counts['homebrew_formulae'] = len(formulae)
        item_counts['homebrew_casks'] = len(casks)
        print(f"  Found {len(formulae)} formulae and {len(casks)} casks")

        # Step 2: Scan applications
        if self.progress_callback:
            self.progress_callback("Scanning installed applications", 2, total_steps, item_counts)
        print("Scanning installed applications...")
        profile.applications = self.scan_applications()
        item_counts['applications'] = len(profile.applications)
        print(f"  Found {len(profile.applications)} applications")

        # Step 3: Scan Dock
        if self.progress_callback:
            self.progress_callback("Scanning Dock items", 3, total_steps, item_counts)
        print("Scanning Dock items...")
        profile.dock_items = self.scan_dock_items()
        item_counts['dock_items'] = len(profile.dock_items)
        print(f"  Found {len(profile.dock_items)} Dock items")

        # Mark items that are in Dock
        dock_names = set(profile.dock_items)
        for item_list in [profile.homebrew_casks, profile.applications]:
            for item in item_list:
                if item.name in dock_names:
                    item.in_dock = True

        # Step 4: Scan login items
        if self.progress_callback:
            self.progress_callback("Scanning login items", 4, total_steps, item_counts)
        print("Scanning login items...")
        profile.login_items = self.scan_login_items()
        item_counts['login_items'] = len(profile.login_items)
        print(f"  Found {len(profile.login_items)} login items")

        # Mark items that start on login
        login_names = set(profile.login_items)
        for item_list in [profile.homebrew_casks, profile.applications]:
            for item in item_list:
                if item.name in login_names:
                    item.start_on_login = True

        # Step 5: Scan shell configs
        if self.progress_callback:
            self.progress_callback("Scanning shell configurations", 5, total_steps, item_counts)
        print("Scanning shell configurations...")
        profile.shell_configs = self.scan_shell_configs()
        item_counts['shell_configs'] = len(profile.shell_configs)
        print(f"  Found {len(profile.shell_configs)} shell config files")

        # Step 6: Scan Git config
        if self.progress_callback:
            self.progress_callback("Scanning Git configuration", 6, total_steps, item_counts)
        print("Scanning Git configuration...")
        profile.git_config = self.scan_git_config()
        item_counts['git_config'] = 1 if profile.git_config else 0
        if profile.git_config:
            print("  Found .gitconfig")

        # Step 7: Scan browser extensions
        if self.progress_callback:
            self.progress_callback("Scanning browser extensions", 7, total_steps, item_counts)
        print("Scanning browser extensions...")
        profile.browser_extensions = self.scan_browser_extensions()
        item_counts['browser_extensions'] = len(profile.browser_extensions)
        print(f"  Found {len(profile.browser_extensions)} browser extensions")

        # Step 8: Scan browser bookmarks
        if self.progress_callback:
            self.progress_callback("Scanning browser bookmarks", 8, total_steps, item_counts)
        print("Scanning browser bookmarks...")
        profile.browser_bookmarks = self.scan_browser_bookmarks()
        bookmark_count = sum(1 for _ in profile.browser_bookmarks.keys())
        item_counts['browser_bookmarks'] = bookmark_count
        print(f"  Found bookmarks for {bookmark_count} browsers")

        # Step 9: Scan macOS preferences
        if self.progress_callback:
            self.progress_callback("Scanning macOS system preferences", 9, total_steps, item_counts)
        print("Scanning macOS system preferences...")
        profile.system_preferences = self.scan_macos_preferences()
        item_counts['system_preferences'] = len(profile.system_preferences)
        print(f"  Found {len(profile.system_preferences)} system preferences")

        # Step 10: Fetch software descriptions
        if self.progress_callback:
            self.progress_callback("Fetching software descriptions", 10, total_steps, item_counts)
        print("Fetching software descriptions...")

        # Fetch brew formula descriptions
        formula_names = [item.brew_package or item.name for item in profile.homebrew_formulae]
        formula_descs = self.fetch_brew_descriptions(formula_names)
        for item in profile.homebrew_formulae:
            key = item.brew_package or item.name
            if key in formula_descs and not item.metadata.get('description'):
                item.metadata['description'] = formula_descs[key]

        # Fetch cask descriptions
        cask_names = [item.brew_package or item.name for item in profile.homebrew_casks]
        cask_descs = self.fetch_cask_descriptions(cask_names)
        for item in profile.homebrew_casks:
            key = item.brew_package or item.name
            if key in cask_descs and not item.metadata.get('description'):
                item.metadata['description'] = cask_descs[key]

        # Add descriptions for manual applications
        for item in profile.applications:
            if not item.metadata.get('description'):
                desc = get_manual_app_description(item.name)
                if desc:
                    item.metadata['description'] = desc

        desc_count = sum(
            1 for items in [profile.homebrew_formulae, profile.homebrew_casks, profile.applications]
            for item in items if item.metadata.get('description')
        )
        print(f"  Fetched {desc_count} descriptions")

        # Step 11: Finalization
        if self.progress_callback:
            self.progress_callback("Finalizing scan results", 11, total_steps, item_counts)

        print("\nScan complete!")
        return profile
