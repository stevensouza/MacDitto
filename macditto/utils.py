"""
Utility functions for MacDitto scanner and system operations.
"""

import os
import subprocess
import platform
from typing import Tuple, Optional, List
from pathlib import Path


def get_home_directory() -> str:
    """
    Get the user's home directory path.

    Returns:
        Absolute path to home directory
    """
    return os.path.expanduser("~")


def run_command(command: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
    """
    Execute a shell command safely and capture output.

    Args:
        command: Command and arguments as list (e.g., ['brew', 'list'])
        timeout: Command timeout in seconds (default: 30)

    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)

    Examples:
        >>> success, out, err = run_command(['echo', 'hello'])
        >>> success
        True
        >>> out.strip()
        'hello'
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return (result.returncode == 0, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (False, "", f"Command timed out after {timeout} seconds")
    except FileNotFoundError:
        return (False, "", f"Command not found: {command[0]}")
    except Exception as e:
        return (False, "", str(e))


def detect_category(name: str, metadata: dict = None) -> str:
    """
    Auto-detect application category based on name and metadata.

    Args:
        name: Application or package name
        metadata: Additional metadata (bundle identifier, description, etc.)

    Returns:
        Category string (Development, Productivity, Media, etc.)

    Categories:
        - Development: IDEs, dev tools, version control, containers
        - Productivity: Office apps, note-taking, email clients
        - Media: Audio/video editing, music production, streaming
        - Communication: Messaging, video conferencing
        - Browsers: Web browsers
        - Security/Privacy: VPNs, encryption, authentication
        - AI/ML: AI assistants, ML tools, transcription
        - Utilities: System tools, file management, command-line utilities
        - Other: Everything else
    """
    name_lower = name.lower()

    # Development tools
    dev_keywords = [
        'intellij', 'idea', 'vscode', 'visual studio', 'visual-studio', 'docker', 'maven', 'gradle',
        'node', 'npm', 'python', 'java', 'openjdk', 'jdk', 'temurin', 'git', 'github', 'gh',
        'visualvm', 'anaconda', 'conda', 'xcode', 'android studio', 'pycharm',
        'sublime', 'atom', 'vim', 'emacs', 'terminal', 'iterm', 'postman',
        'mongodb', 'postgresql', 'mysql', 'redis', 'kubernetes', 'kubectl',
        'conductor'
    ]

    # Productivity apps
    productivity_keywords = [
        'evernote', 'notion', 'obsidian', 'bear', 'notes', 'proton mail',
        'mail', 'outlook', 'calendar', 'fantastical',
        'things', 'todoist', 'trello', 'asana', 'alfred', 'raycast',
        'office', 'microsoft word', 'excel', 'powerpoint', 'keynote', 'numbers', 'pages'
    ]

    # Media tools
    media_keywords = [
        'davinci', 'resolve', 'audacity', 'blackmagic', 'muse', 'spotify',
        'garageband', 'logic', 'final cut', 'premiere', 'photoshop', 'lightroom',
        'vlc', 'iina', 'plex', 'obs', 'handbrake', 'ffmpeg', 'youtube'
    ]

    # Communication apps
    communication_keywords = [
        'signal', 'zoom', 'teams', 'discord', 'telegram', 'whatsapp',
        'facetime', 'messages', 'skype', 'webex', 'slack'
    ]

    # Browsers
    browser_keywords = [
        'brave', 'chrome', 'firefox', 'safari', 'edge', 'opera', 'duckduckgo',
        'arc', 'vivaldi'
    ]

    # Security/Privacy
    security_keywords = [
        'surfshark', 'nordvpn', 'expressvpn', 'vpn', 'gnupg', 'gpg', '1password',
        'lastpass', 'bitwarden', 'keychain', 'malwarebytes', 'little snitch',
        'proton authenticator', 'authenticator'
    ]

    # AI/ML tools
    ai_keywords = [
        'claude', 'chatgpt', 'whisper', 'superwhisper', 'whispering', 'pingclaude',
        'ollama', 'lmstudio', 'msty', 'tensorflow', 'pytorch', 'jupyter'
    ]

    # Utilities
    utility_keywords = [
        'finder', 'activity monitor', 'disk utility', 'cleanmymac', 'daisy disk',
        'istat', 'bartender', 'magnet', 'rectangle', 'bettertouchtool',
        'appcleaner', 'the unarchiver', 'keka', 'transmission', 'tesseract',
        'imagemagick', 'wget', 'curl', 'htop', 'tree',
        'sqlite', 'httpie', 'jq'
    ]

    # Check each category
    if any(keyword in name_lower for keyword in dev_keywords):
        return "Development"
    elif any(keyword in name_lower for keyword in productivity_keywords):
        return "Productivity"
    elif any(keyword in name_lower for keyword in media_keywords):
        return "Media"
    elif any(keyword in name_lower for keyword in communication_keywords):
        return "Communication"
    elif any(keyword in name_lower for keyword in browser_keywords):
        return "Browsers"
    elif any(keyword in name_lower for keyword in security_keywords):
        return "Security/Privacy"
    elif any(keyword in name_lower for keyword in ai_keywords):
        return "AI/ML"
    elif any(keyword in name_lower for keyword in utility_keywords):
        return "Utilities"
    else:
        return "Other"


def is_standard_macos_app(name: str, bundle_id: Optional[str] = None) -> bool:
    """
    Check if an application is a standard macOS built-in app.

    These apps are excluded from scans as they're pre-installed on all Macs.

    Args:
        name: Application name
        bundle_id: Optional bundle identifier (e.g., com.apple.Safari)

    Returns:
        True if this is a standard macOS app that should be excluded
    """
    standard_apps = {
        # System apps
        'Safari', 'Mail', 'Maps', 'Messages', 'FaceTime', 'Photos',
        'Calendar', 'Contacts', 'Reminders', 'Notes', 'News', 'Stocks',
        'Home', 'Weather', 'Clock', 'Calculator', 'Voice Memos', 'Books',
        'App Store', 'System Preferences', 'System Settings', 'FindMy',
        'Shortcuts', 'Music', 'TV', 'Podcasts', 'Freeform',

        # Utilities
        'Finder', 'Activity Monitor', 'AirPort Utility', 'Audio MIDI Setup',
        'Bluetooth File Exchange', 'Boot Camp Assistant', 'ColorSync Utility',
        'Console', 'Digital Color Meter', 'Disk Utility', 'Grapher',
        'Keychain Access', 'Migration Assistant', 'Screenshot', 'Script Editor',
        'System Information', 'Terminal', 'TextEdit', 'VoiceOver Utility',

        # iWork suite
        'Keynote', 'Numbers', 'Pages',

        # iLife suite
        'GarageBand', 'iMovie',

        # Developer (often pre-installed on dev machines)
        'Xcode',
    }

    # Check by name
    if name in standard_apps:
        return True

    # Check by bundle ID (com.apple.* apps)
    if bundle_id and bundle_id.startswith('com.apple.'):
        return True

    return False


def get_machine_name() -> str:
    """
    Get the current machine's name.

    Returns:
        Machine name (e.g., "Steve's MacBook Air")
    """
    try:
        success, stdout, _ = run_command(['scutil', '--get', 'ComputerName'])
        if success and stdout.strip():
            return stdout.strip()
    except Exception:
        pass

    # Fallback to hostname
    return platform.node()


def file_exists(path: str) -> bool:
    """
    Check if a file exists.

    Args:
        path: File path (can use ~ for home directory)

    Returns:
        True if file exists, False otherwise
    """
    expanded_path = os.path.expanduser(path)
    return os.path.isfile(expanded_path)


def read_file(path: str) -> Optional[str]:
    """
    Read file contents safely.

    Args:
        path: File path (can use ~ for home directory)

    Returns:
        File contents as string, or None if file doesn't exist or can't be read
    """
    expanded_path = os.path.expanduser(path)
    try:
        with open(expanded_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def ensure_directory_exists(path: str) -> None:
    """
    Create directory if it doesn't exist.

    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def get_timestamp() -> str:
    """
    Get current timestamp in ISO 8601 format.

    Returns:
        ISO timestamp string (e.g., "2026-02-15T10:30:00")
    """
    from datetime import datetime
    return datetime.now().isoformat(timespec='seconds')


def get_brew_cask_name(app_name: str) -> Optional[str]:
    """
    Get the Homebrew cask name for an application.

    This function maps common application names to their brew cask equivalents.
    Even if an app was manually installed, we suggest the brew cask for
    future installations.

    Args:
        app_name: Application name (without .app extension)

    Returns:
        Brew cask name if available, None otherwise

    Examples:
        >>> get_brew_cask_name("Brave Browser")
        'brave-browser'
        >>> get_brew_cask_name("Google Chrome")
        'google-chrome'
    """
    # Normalize app name for matching
    name_lower = app_name.lower().strip()

    # Common mappings: app name -> brew cask name
    APP_TO_CASK_MAP = {
        # Browsers
        'brave browser': 'brave-browser',
        'brave': 'brave-browser',
        'google chrome': 'google-chrome',
        'chrome': 'google-chrome',
        'mozilla firefox': 'firefox',
        'firefox': 'firefox',
        'microsoft edge': 'microsoft-edge',
        'edge': 'microsoft-edge',
        'opera': 'opera',
        'duckduckgo': 'duckduckgo',
        'arc': 'arc',
        'vivaldi': 'vivaldi',
        'safari technology preview': 'safari-technology-preview',

        # VPNs / Security
        'surfshark': 'surfshark',
        'nordvpn': 'nordvpn',
        'expressvpn': 'expressvpn',
        'protonvpn': 'protonvpn',
        '1password': '1password',
        '1password 7': '1password7',
        'bitwarden': 'bitwarden',
        'malwarebytes': 'malwarebytes',
        'little snitch': 'little-snitch',

        # Development
        'visual studio code': 'visual-studio-code',
        'vscode': 'visual-studio-code',
        'intellij idea': 'intellij-idea',
        'intellij idea community edition': 'intellij-idea-ce',
        'intellij idea ultimate': 'intellij-idea',
        'pycharm': 'pycharm',
        'pycharm professional': 'pycharm',
        'pycharm community edition': 'pycharm-ce',
        'sublime text': 'sublime-text',
        'atom': 'atom',
        'docker desktop': 'docker',
        'docker': 'docker',
        'iterm2': 'iterm2',
        'iterm': 'iterm2',
        'postman': 'postman',
        'github desktop': 'github',
        'sublime merge': 'sublime-merge',
        'android studio': 'android-studio',
        'xcode': None,  # Apple app, not in brew casks

        # Communication
        'signal': 'signal',
        'zoom': 'zoom',
        'zoom.us': 'zoom',
        'microsoft teams': 'microsoft-teams',
        'teams': 'microsoft-teams',
        'discord': 'discord',
        'slack': 'slack',
        'telegram': 'telegram',
        'telegram desktop': 'telegram-desktop',
        'whatsapp': 'whatsapp',
        'skype': 'skype',

        # Media
        'vlc': 'vlc',
        'spotify': 'spotify',
        'iina': 'iina',
        'obs': 'obs',
        'obs studio': 'obs',
        'handbrake': 'handbrake',
        'plex': 'plex',
        'davinci resolve': 'davinci-resolve',
        'audacity': 'audacity',

        # Productivity
        'notion': 'notion',
        'obsidian': 'obsidian',
        'evernote': 'evernote',
        'bear': 'bear',
        'alfred': 'alfred',
        'raycast': 'raycast',
        'rectangle': 'rectangle',
        'magnet': 'magnet',
        'bettertouchtool': 'bettertouchtool',
        'bartender': 'bartender',
        'cleanmymac': 'cleanmymac',
        'cleanmymac x': 'cleanmymac',
        'appcleaner': 'appcleaner',
        'the unarchiver': 'the-unarchiver',
        'keka': 'keka',

        # AI/ML
        'claude for desktop': None,  # Not yet available via brew
        'chatgpt': 'chatgpt',
    }

    # Direct match
    if name_lower in APP_TO_CASK_MAP:
        return APP_TO_CASK_MAP[name_lower]

    # Try partial matches (e.g., "Brave Browser Beta" -> "brave-browser")
    for app_key, cask_name in APP_TO_CASK_MAP.items():
        if app_key in name_lower or name_lower in app_key:
            return cask_name

    # If no mapping found, return None
    return None


MANUAL_APP_DESCRIPTIONS = {
    # Development
    'IntelliJ IDEA': 'Java IDE for professional development',
    'IntelliJ IDEA CE': 'Free Java IDE for JVM development',
    'PyCharm': 'Python IDE for professional development',
    'PyCharm CE': 'Free Python IDE for development',
    'Visual Studio Code': 'Open-source code editor by Microsoft',
    'Sublime Text': 'Sophisticated text editor for code and markup',
    'Android Studio': 'IDE for Android app development',
    'Xcode': 'Apple IDE for macOS and iOS development',
    'Docker Desktop': 'Container platform for building and sharing apps',
    'Docker': 'Container platform for building and sharing apps',
    'iTerm2': 'Terminal emulator with advanced features for macOS',
    'iTerm': 'Terminal emulator with advanced features for macOS',
    'Postman': 'API development and testing platform',
    'GitHub Desktop': 'Git client with GitHub integration',
    'VisualVM': 'JVM monitoring and troubleshooting tool',
    'Anaconda-Navigator': 'Python data science distribution manager',

    # Browsers
    'Brave Browser': 'Privacy-focused web browser with ad blocking',
    'Google Chrome': 'Web browser by Google',
    'Firefox': 'Open-source web browser by Mozilla',
    'Microsoft Edge': 'Web browser by Microsoft',
    'Arc': 'Browser designed for productivity and organization',
    'Opera': 'Web browser with built-in VPN and ad blocker',
    'DuckDuckGo': 'Privacy-focused web browser',
    'Vivaldi': 'Highly customizable web browser',

    # Communication
    'Zoom': 'Video conferencing and meetings platform',
    'Zoom.us': 'Video conferencing and meetings platform',
    'Slack': 'Team communication and collaboration platform',
    'Discord': 'Voice, video, and text communication platform',
    'Signal': 'Encrypted messaging application',
    'Telegram': 'Cloud-based messaging application',
    'Telegram Desktop': 'Cloud-based messaging application',
    'WhatsApp': 'Messaging and calling application',
    'Microsoft Teams': 'Team collaboration and video conferencing',
    'Skype': 'Video calling and messaging application',
    'Webex': 'Video conferencing by Cisco',

    # Media
    'Spotify': 'Music streaming service',
    'VLC': 'Free open-source media player',
    'IINA': 'Modern media player for macOS',
    'OBS': 'Open-source streaming and recording software',
    'OBS Studio': 'Open-source streaming and recording software',
    'HandBrake': 'Open-source video transcoder',
    'DaVinci Resolve': 'Professional video editing software',
    'Audacity': 'Free open-source audio editor',
    'Plex': 'Media server and streaming platform',

    # Productivity
    'Notion': 'All-in-one workspace for notes and collaboration',
    'Obsidian': 'Knowledge base with linked markdown notes',
    'Evernote': 'Note-taking and organization application',
    'Bear': 'Elegant markdown note-taking application',
    'Alfred': 'Productivity app with spotlight replacement and workflows',
    'Raycast': 'Productivity launcher and command palette',
    'Rectangle': 'Window management with keyboard shortcuts',
    'Magnet': 'Window manager for organized desktop',
    'BetterTouchTool': 'Customization tool for input devices and window snapping',
    'Bartender': 'Menu bar icon organizer',
    'CleanMyMac': 'Mac cleaning and optimization utility',
    'CleanMyMac X': 'Mac cleaning and optimization utility',
    'AppCleaner': 'Application uninstaller for macOS',
    'The Unarchiver': 'Archive extraction utility',
    'Keka': 'File archiver and extractor',

    # Security/Privacy
    'Surfshark': 'VPN service for privacy and security',
    'NordVPN': 'VPN service for privacy and security',
    'ExpressVPN': 'VPN service for privacy and security',
    'ProtonVPN': 'Privacy-focused VPN service',
    '1Password': 'Password manager and secure vault',
    '1Password 7': 'Password manager and secure vault',
    'Bitwarden': 'Open-source password manager',
    'LastPass': 'Password manager and digital vault',
    'Malwarebytes': 'Anti-malware and security software',
    'Little Snitch': 'Network monitor and firewall for macOS',

    # AI/ML
    'ChatGPT': 'AI assistant by OpenAI',
    'Claude': 'AI assistant by Anthropic',
    'Ollama': 'Run large language models locally',
    'LM Studio': 'Desktop app for running local LLMs',
    'SuperWhisper': 'AI-powered voice-to-text transcription',
    'Whispering': 'AI speech-to-text transcription tool',

    # Utilities
    'Transmission': 'Lightweight BitTorrent client',
    'DaisyDisk': 'Disk space analyzer and cleaner',
    'iStat Menus': 'System monitor for the menu bar',
}


def get_manual_app_description(name: str) -> Optional[str]:
    """
    Get description for a manually installed application.

    Args:
        name: Application name

    Returns:
        Description string or None if not found
    """
    if name in MANUAL_APP_DESCRIPTIONS:
        return MANUAL_APP_DESCRIPTIONS[name]

    # Try case-insensitive match
    name_lower = name.lower()
    for app_name, desc in MANUAL_APP_DESCRIPTIONS.items():
        if app_name.lower() == name_lower:
            return desc

    return None


def check_brew_cask_exists(cask_name: str) -> bool:
    """
    Check if a Homebrew cask actually exists in the repository.

    Args:
        cask_name: Name of the cask to check

    Returns:
        True if cask exists, False otherwise
    """
    if not cask_name:
        return False

    success, stdout, _ = run_command(['brew', 'info', '--cask', cask_name], timeout=10)
    return success and cask_name in stdout.lower()
