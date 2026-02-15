# MacDitto - Mac Environment Duplication Tool

## Overview
MacDitto scans a Mac's environment (installed software, configurations, accounts, preferences) and generates portable configuration files + install scripts that can be run on a new Mac to replicate the setup.

## Technology Stack
- **Language:** Python 3
- **GUI:** Flask web application (runs in browser)
- **Data Format:** JSON config files
- **Install via:** Homebrew (Python + pip dependencies)
- **Portability:** Clone from GitHub on new machine, run MacDitto

---

## Core Modules

### 1. Scanner Module
Examines the current Mac and collects:

| Source | What It Captures | Method |
|--------|-----------------|--------|
| Homebrew formulae | Directly installed packages (not dependencies) | `brew bundle dump` |
| Homebrew casks | GUI apps installed via brew | `brew bundle dump` |
| /Applications | All installed apps | Directory listing |
| Dock | Apps pinned to icon bar | `defaults read com.apple.dock` |
| Login Items | Apps that start on login | `osascript` / System Events |
| Shell configs | .zshrc, .zprofile, .bash_profile | File copy |
| Git config | .gitconfig | File copy |
| Browser extensions | Chrome & Brave extensions | Extension directories |
| Browser bookmarks | Chrome & Brave bookmarks | Bookmarks JSON files |
| macOS preferences | Key system customizations | `defaults read` commands |

**Standard macOS apps are excluded** (Safari, Finder, GarageBand, iMovie, Keynote, Numbers, Pages, etc.)

### 2. Data Model (JSON Config)
```json
{
  "scan_date": "2026-02-15T10:30:00",
  "machine_name": "Steve's MacBook Air",
  "categories": {
    "homebrew_formulae": [...],
    "homebrew_casks": [...],
    "applications": [...],
    "accounts": [...],
    "browser_extensions": [...],
    "shell_configs": [...],
    "system_preferences": [...]
  }
}
```

Each item has properties:
- `name` - Display name
- `install_method` - brew, cask, app_store, manual, mas
- `enabled` - true/false (user checkbox)
- `in_dock` - true/false
- `start_on_login` - true/false
- `category` - auto-detected (Development, Productivity, Media, Security/Privacy, Communication)
- `brew_package` - Homebrew package name (if applicable)
- `manual_instructions` - Steps for non-automatable installs
- `url` - Download or login URL (for accounts/manual installs)

### 3. Web GUI (Flask)
- **Dashboard** showing all discovered items organized by category
- **Checkboxes** to enable/disable each item
- **Properties** visible per item (install method, dock, login, category)
- **Rescan button** to pick up new installs
- **Save/Load profiles** (save to dated snapshot files)
- **Diff view** between current scan and saved profile (show what's new/removed)
- **Export** generates install script + manual instructions markdown
- **Dry run** preview of what would be installed

### 4. Generator Module
Produces output files for new machine setup:

- **install.sh** - Automated install script:
  - Install Homebrew (if not present)
  - `brew bundle install` from generated Brewfile
  - `mas install` for Mac App Store apps
  - Copy shell configs (.zshrc, .zprofile, .bash_profile)
  - Copy .gitconfig
  - Configure Dock items via `defaults write`
  - Configure login items
  - Apply macOS preference `defaults write` commands
- **MANUAL_STEPS.md** - Human-readable instructions for:
  - Apps requiring manual download/install
  - Accounts to log into (with URLs)
  - Browser extensions to reinstall (with links)
  - SSH key generation
  - Any other non-automatable steps
- **Brewfile** - Standard Homebrew bundle file
- **macditto_config.json** - Full config for MacDitto on target machine

### 5. Runner Module (on new machine)
- Clone MacDitto from GitHub
- Read config file
- Execute install scripts with progress reporting
- Skip already-installed items
- Show manual steps in GUI
- Report what succeeded, what failed, what needs manual action

---

## Categories (Auto-Detected)

| Category | Examples |
|----------|----------|
| **Development** | IntelliJ IDEA, Docker Desktop, Maven, Node, Python, gh, openjdk, VisualVM, Anaconda |
| **Productivity** | Evernote, Proton Mail, Proton Authenticator |
| **Media** | DaVinci Resolve, Audacity, Blackmagic tools, Muse Hub, Spotify, GarageBand |
| **Communication** | Signal, Zoom |
| **Browsers** | Brave Browser, Google Chrome, DuckDuckGo |
| **Security/Privacy** | Surfshark, gnupg |
| **AI/ML** | Claude Code, superwhisper, Whispering, PingClaude, whisper-cpp |
| **Utilities** | ffmpeg, tesseract |

## Accounts / Web Services (User-Provided)
- GitHub (account login + SSH key setup)
- Proton Mail (email account)
- Brave/Chrome browser sync (if used)
- Any others user adds via GUI

---

## Key Features

### Profile Snapshots
- Save dated config snapshots: `macditto_2026-02-15.json`
- Compare snapshots to see what changed over time
- Load any snapshot as the active profile
- Default scan doesn't overwrite saved profiles

### Incremental Scanning
- Rescan detects new installs since last scan
- Highlights new items for user review
- User can enable/disable new items before saving

### Dry Run Mode
- Preview all install commands without executing
- Show what would be installed, configured, copied
- Useful for reviewing before running on new machine

### Validation on Target
- Check what's already installed on the new machine
- Only install missing items
- Report status: installed, missing, needs-update

### Mac App Store Integration
- Use `mas` CLI (Homebrew: `brew install mas`) for App Store apps
- Auto-detect App Store apps vs. direct downloads
- Generate `mas install <app-id>` commands

### macOS System Preferences Captured
Key customizations detected via `defaults read`:
- Trackpad settings (tap to click, scroll direction, gestures)
- Keyboard settings (key repeat rate, shortcuts)
- Dock settings (size, position, auto-hide, magnification)
- Finder preferences (show extensions, default view)
- Screenshots (location, format)
- Other common customizations

---

## Workflow

### On Source Machine (Current Mac)
1. Install/run MacDitto: `python -m macditto scan`
2. Open GUI in browser: `http://localhost:5000`
3. Review discovered items, enable/disable as needed
4. Assign categories, add accounts, add manual notes
5. Save profile: generates config + scripts
6. Push MacDitto project (with config) to GitHub

### On Target Machine (New Mac)
1. Install Homebrew: `/bin/bash -c "$(curl -fsSL ...)"`
2. Install Python: `brew install python`
3. Clone MacDitto: `git clone <repo-url>`
4. Run MacDitto: `python -m macditto setup`
5. Open GUI: review what will be installed
6. Run install (or dry run first)
7. Follow manual steps for remaining items
8. Verify with validation scan

---

## File Structure (Planned)
```
MacDitto/
├── macditto/
│   ├── __init__.py
│   ├── app.py              # Flask web app
│   ├── scanner.py           # Environment scanner
│   ├── generator.py         # Script/doc generator
│   ├── runner.py            # Install executor
│   ├── models.py            # Data models
│   ├── categories.py        # Auto-categorization logic
│   ├── utils.py             # Shared utilities
│   ├── templates/           # Flask HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── diff.html
│   │   └── setup.html
│   └── static/              # CSS, JS
│       ├── style.css
│       └── app.js
├── profiles/                # Saved scan profiles
│   └── .gitkeep
├── output/                  # Generated scripts
│   └── .gitkeep
├── tests/                   # Test suite
│   └── .gitkeep
├── docs/
│   └── REQUIREMENTS.md      # This file
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
└── README.md
```

---

## Non-Functional Requirements
- Must run on macOS (Apple Silicon and Intel)
- No personal data stored in configs (no passwords, tokens, secrets)
- Config files safe to commit to GitHub
- Minimal dependencies (Flask + standard library where possible)
- Clear error handling with actionable messages
- Progress reporting during install

---

## Decision Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-15 | Renamed from DevDitto to MacDitto | App may be used for non-dev machines too |
| 2026-02-15 | Python + Flask for GUI | Portable, lightweight, installs via Homebrew |
| 2026-02-15 | Capture shell + git configs | User wants full environment replication |
| 2026-02-15 | Detect browser extensions | Show in GUI + generate checklist with links |
| 2026-02-15 | Capture macOS system prefs | Generate `defaults write` commands for key settings |
| 2026-02-15 | Instructions: GUI + markdown | Both formats for manual steps |
| 2026-02-15 | Brewfile as backbone | Leverage Homebrew's native bundle system |
| 2026-02-15 | JSON config format | Human-readable, easy to edit, GitHub-friendly |
