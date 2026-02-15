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
        'intellij', 'idea', 'vscode', 'visual studio', 'docker', 'maven', 'gradle',
        'node', 'npm', 'python', 'java', 'openjdk', 'jdk', 'git', 'github', 'gh',
        'visualvm', 'anaconda', 'conda', 'xcode', 'android studio', 'pycharm',
        'sublime', 'atom', 'vim', 'emacs', 'terminal', 'iterm', 'postman',
        'mongodb', 'postgresql', 'mysql', 'redis', 'kubernetes', 'kubectl'
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
        'ollama', 'lmstudio', 'tensorflow', 'pytorch', 'jupyter'
    ]

    # Utilities
    utility_keywords = [
        'finder', 'activity monitor', 'disk utility', 'cleanmymac', 'daisy disk',
        'istat', 'bartender', 'magnet', 'rectangle', 'bettertouchtool',
        'appcleaner', 'the unarchiver', 'keka', 'transmission', 'tesseract',
        'imagemagick', 'wget', 'curl', 'htop', 'tree'
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
