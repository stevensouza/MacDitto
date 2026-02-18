# MacDitto - Mac Environment Duplication Tool

**Version 0.1.0**

A Python tool for scanning, capturing, and replicating macOS environments across machines. MacDitto captures your entire Mac setup—installed software, configurations, preferences—and generates automated scripts to replicate it on a new Mac.

---

## Table of Contents

1. [What MacDitto Does](#what-macditto-does)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [What MacDitto Scans](#what-macditto-scans)
5. [Usage Examples](#usage-examples)
6. [Web Interface Guide](#web-interface-guide)
7. [Workflows](#workflows)
8. [Project Structure](#project-structure)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Contributing](#contributing)

---

## What MacDitto Does

MacDitto solves a common problem: **setting up a new Mac takes hours of manual work**. With MacDitto, you can:

1. **Scan** your current Mac to capture everything installed and configured
2. **Review** discovered items in a web interface (scan auto-saves with installation files)
3. **Transfer** the saved scan directory to your new Mac
4. **Run** the install scripts on a new Mac to replicate your setup

**Example scenario:**

```
Current Mac ──> [MacDitto Scan] ──> Scan JSON + Scripts
                                           │
                                           ▼
New Mac <─────── [Run Scripts] <───── Transfer Files
```

**Time saved:** What normally takes 4-8 hours of manual installation can be reduced to 30 minutes of automated setup + 30 minutes of manual steps.

---

## System Requirements

### Minimum Requirements

- **macOS:** 12.0 (Monterey) or later
  - ✅ Tested on macOS 12.7.6
  - ✅ Tested on macOS 13.x (Ventura)
  - ✅ Tested on macOS 14.x (Sonoma)
  - ✅ Tested on macOS 15.x (Sequoia)
- **Python:** 3.9 or later
- **Homebrew:** Latest version (optional but recommended)
- **Disk Space:** ~50 MB for MacDitto, plus space for scanned data

### Architecture Support

- ✅ Apple Silicon (M1, M2, M3, M4)
- ✅ Intel (x86_64)

### Optional Dependencies

- **Git:** For version controlling profiles
- **curl:** For downloading Homebrew (pre-installed on macOS)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/MacDitto.git
cd MacDitto

# Install dependencies
pip3 install -r requirements.txt
```

**Note:** If you don't have Python 3 installed:
```bash
# Install via Homebrew
brew install python3

# Or download from python.org
# https://www.python.org/downloads/
```

### Run the Web Interface

```bash
# Option 1: Use the startup script (if available)
./run_app.sh

# Option 2: Run directly with Python
python3 -m macditto.app

# Option 3: Run from Python
python3 -c "from macditto.app import app; app.run(debug=True)"
```

Then open your browser to: **http://localhost:5000**

### Basic Usage (3 Steps)

1. **Click "Run Scan"** - Analyzes your Mac (takes 10-30 seconds), auto-saves scan + generates installation files
2. **Review items** - See everything discovered in a unified table, searchable by name
3. **Toggle items & Regenerate** - Enable/disable items, then click "Regenerate Files" to update installation files

---

## Features

### ✅ Comprehensive Scanning

MacDitto scans **8 major categories** of software and configurations:

- **Homebrew packages** (formulae and casks)
- **Applications** (/Applications directory)
- **Browser extensions** (Chrome, Brave)
- **Shell configurations** (.zshrc, .bash_profile, etc.)
- **Git configuration** (.gitconfig)
- **Dock items** (apps pinned to Dock)
- **Login items** (apps that start automatically)
- **macOS system preferences** (Trackpad, Keyboard, Dock settings)

### ✅ Smart Categorization

All discovered items are automatically categorized:

| Category | Example Items |
|----------|---------------|
| **Development** | IntelliJ IDEA, Docker, Maven, Node, Python, VS Code |
| **Productivity** | Evernote, Notion, Obsidian, Proton Mail |
| **Media** | DaVinci Resolve, Spotify, Audacity |
| **Communication** | Signal, Zoom, Slack |
| **Browsers** | Brave, Chrome, Firefox |
| **Security/Privacy** | VPN apps, gnupg, password managers |
| **AI/ML** | Claude Code, Whisper, ML frameworks |
| **Utilities** | ffmpeg, tesseract, compression tools |

### ✅ Auto-Saved Scans

Every scan automatically saves to a timestamped directory with all installation files:

- **`saved_scan.json`** - Complete scan data
- **`Brewfile`** - Homebrew bundle for automated installs
- **`install.sh`** - Bash script that runs everything automatically
- **`MANUAL_STEPS.md`** - Checklist for manual installations
- **`SETUP_NOTES.md`** - Your personal setup notes
- **`SOFTWARE_CATALOG.md`** - Markdown catalog of all software with descriptions

Load any saved scan to review, compare, or regenerate files after toggling items.

### ✅ Web Interface

- **Dashboard** showing all items in a unified searchable table
- **Sortable columns** — click any column header to sort ascending/descending
- **Checkboxes** to enable/disable each item for installation files
- **Item properties** visible (category, description, install method, location, install command, dock/login flags)
- **Real-time search** to filter items by name
- **Setup Notes** section — editable markdown notes saved with each scan
- **Scan progress** modal with live step-by-step updates

---

## What MacDitto Scans

### Homebrew Packages

**What:** Command-line tools and GUI apps installed via Homebrew

**How:** Runs `brew bundle dump` and parses the output

**Example items captured:**
```
- git (formula)
- node (formula)
- python@3.11 (formula)
- docker (cask)
- visual-studio-code (cask)
- brave-browser (cask)
```

**Export format:** Generates `Brewfile` for `brew bundle install`

---

### Applications

**What:** All apps in `/Applications` directory

**How:** Scans `/Applications` and categorizes each app

**Filtering:** Excludes standard macOS apps (Safari, Calculator, etc.)

**Example items captured:**
```
- IntelliJ IDEA Ultimate
- Docker Desktop
- Signal
- Spotify
```

**Install detection:** Identifies whether each app was installed via:
- Homebrew cask (`brew install --cask`)
- Mac App Store (`mas install`)
- Manual download/installer

---

### Dock Items

**What:** Apps currently pinned to your Dock

**How:** Reads `defaults read com.apple.dock persistent-apps`

**Example:**
```
Your Dock: [Finder] [Brave] [IntelliJ] [Signal] [Spotify] [Terminal]
            └─ MacDitto captures this order and generates setup commands
```

**Export:** Generates `defaults write` commands to restore Dock layout

---

### Login Items

**What:** Apps that start automatically when you log in

**How:** Uses `osascript` to query System Events

**Example items:**
```
- Docker Desktop (starts on login)
- Proton Mail (starts on login)
```

**Export:** Adds commands to configure login items on new Mac

---

### Shell Configurations

**What:** Shell startup files and environment customizations

**Files scanned:**
```
~/.zshrc
~/.zprofile
~/.bash_profile
~/.bashrc
~/.profile
```

**Example captured content:**
```bash
# Your custom aliases
alias ll='ls -lah'
alias gst='git status'

# Environment variables
export JAVA_HOME=$(/usr/libexec/java_home -v 11)
export PATH="$HOME/bin:$PATH"

# Custom functions
function mkcd() { mkdir -p "$1" && cd "$1"; }
```

**Export:** Copies files to new Mac during setup

---

### Git Configuration

**What:** Your Git user settings and aliases

**File:** `~/.gitconfig`

**Example captured:**
```ini
[user]
    name = Steve Souza
    email = steve@example.com
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
[core]
    editor = vim
```

**Export:** Copies to new Mac (without credentials)

---

### Browser Extensions

**What:** Installed extensions for Chrome and Brave

**How:** Scans extension directories and reads manifests

**Example output:**
```
Chrome Extensions:
- uBlock Origin v1.52.0
- 1Password v8.10.0
- React Developer Tools v4.27.8

Brave Extensions:
- uBlock Origin v1.52.0
- Privacy Badger v2023.1.31
```

**Export:** Generates `MANUAL_STEPS.md` with store URLs for reinstalling

**Note:** Extensions cannot be auto-installed due to browser security

---

### macOS System Preferences

**What:** Key system customizations you've made

**Categories captured:**

1. **Trackpad Settings**
   ```
   - Tap to click: enabled
   - Natural scrolling: disabled
   - Tracking speed: 7/10
   ```

2. **Keyboard Settings**
   ```
   - Key repeat rate: 7/10
   - Delay until repeat: 3/10
   - Caps Lock → Control remapping
   ```

3. **Dock Preferences**
   ```
   - Size: 48px
   - Position: bottom
   - Auto-hide: enabled
   - Magnification: disabled
   ```

4. **Finder Preferences**
   ```
   - Show all file extensions: enabled
   - Show hidden files: enabled
   - Default view: list view
   ```

**Export:** Generates `defaults write` commands to replicate settings

---

## Usage Examples

### Example 1: Basic Scan and Review

```bash
# Start MacDitto
python3 -m macditto.app

# Open browser to http://localhost:5000
# Click "Scan" button

# Output in browser:
✓ Scan completed successfully
  - 42 Homebrew formulae found
  - 18 Homebrew casks found
  - 67 applications found
  - 12 browser extensions found
  - 8 Dock items found

# Review items by category:
Development (35 items)
  ☑ IntelliJ IDEA Ultimate
  ☑ Docker Desktop
  ☑ git
  ☑ node
  ☐ python@3.9 (older version - disabled)

Browsers (3 items)
  ☑ Brave Browser
  ☑ Google Chrome
  ☐ Firefox (rarely used - disabled)
```

### Example 2: Load a Saved Scan

```bash
# Click Scan > Saved Scans
# Select a saved scan from the list
# Scan loads into the dashboard

# Toggle items on/off, then click "Regenerate Files" to update
```

### Example 3: Transfer to New Mac

```bash
# After scanning, files are auto-generated in:
# scans/scan_MacBookAir_20260215_143022/
  - saved_scan.json           # Complete scan data
  - Brewfile                  # Homebrew packages
  - install.sh                # Automated install script
  - MANUAL_STEPS.md           # Manual installation checklist
  - SETUP_NOTES.md            # Your personal setup notes
  - SOFTWARE_CATALOG.md       # Catalog of all software with descriptions

# Transfer to new Mac:
# Option 1: Commit to Git
git add scans/scan_MacBookAir_20260215_143022/
git commit -m "MacDitto scan for new Mac setup"
git push

# Option 2: USB drive
cp -r scans/scan_MacBookAir_20260215_143022/ /Volumes/USB_DRIVE/

# Option 3: AirDrop
# Right-click folder → Share → AirDrop
```

### Example 4: Set Up New Mac

**On the new Mac:**

```bash
# Step 1: Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Step 2: Get MacDitto export files
# From Git:
git clone https://github.com/yourusername/MacDitto.git
cd MacDitto/scans/scan_MacBookAir_20260215_143022/

# Or from USB:
cd /Volumes/USB_DRIVE/scan_MacBookAir_20260215_143022/

# Step 3: Run automated install
chmod +x install.sh
./install.sh

# Output:
MacDitto Install Script
=======================

✓ Homebrew already installed
✓ Installing Homebrew packages...
  - Installing git... ✓
  - Installing node... ✓
  - Installing python@3.11... ✓
  - Installing docker (cask)... ✓
  - Installing brave-browser (cask)... ✓
  [... continues for all packages ...]

✓ Copying shell configurations...
  - Copied .zshrc
  - Copied .zprofile

✓ Copying Git config...
  - Copied .gitconfig

✓ Applying macOS system preferences...
  - Set Dock size to 48
  - Enabled auto-hide Dock
  - Set trackpad tap-to-click

Installation complete!
See MANUAL_STEPS.md for remaining manual steps.

# Step 4: Follow manual steps
open MANUAL_STEPS.md

# Example content:
## Applications Requiring Manual Installation

### IntelliJ IDEA Ultimate
Download from: https://www.jetbrains.com/idea/download/
License: Use your JetBrains account

### Signal
Download from: https://signal.org/download/
Setup: Scan QR code to link to phone

## Browser Extensions

### Chrome
- uBlock Origin: https://chrome.google.com/webstore/detail/...
- 1Password: https://chrome.google.com/webstore/detail/...

## Accounts & Web Services

### GitHub
Login at: https://github.com
Setup SSH key:
  ssh-keygen -t ed25519 -C "your_email@example.com"
  # Add to GitHub: Settings → SSH Keys
```

### Example 5: Compare Scans (Track Changes)

```bash
# Scenario: You want to see what changed on your Mac in the last month

# In web interface:
# 1. Select two scans to compare
Scan 1: scan_MacBookAir_20260115_100000 (January 15)
Scan 2: scan_MacBookAir_20260215_143022 (February 15)

# 2. Click "Compare"

# Output shows:
✅ Added (7 items):
  - claude-code (Homebrew cask)
  - superwhisper (Application)
  - pytest (Homebrew formula)
  - black (Homebrew formula)
  - Privacy Badger (Browser extension - Brave)
  - Notion (Application)
  - mas (Homebrew formula)

❌ Removed (2 items):
  - firefox (Homebrew cask) [Uninstalled]
  - postman (Homebrew cask) [Replaced with Bruno]

📊 Summary:
  Total items in Jan: 143
  Total items in Feb: 148
  Net change: +5 items
```

### Example 6: CLI Scan (Without Web Interface)

```bash
# Run scan from command line
python3 scan.py

# Output:
Starting MacDitto scan...
[1/8] Scanning Homebrew formulae... ✓ 42 found
[2/8] Scanning Homebrew casks... ✓ 18 found
[3/8] Scanning applications... ✓ 67 found
[4/8] Scanning Dock items... ✓ 8 found
[5/8] Scanning login items... ✓ 3 found
[6/8] Scanning shell configs... ✓ 2 found
[7/8] Scanning browser extensions... ✓ 12 found
[8/8] Scanning system preferences... ✓ 15 found

Scan complete! Saved to: scan_results.json

# View results
cat scan_results.json | jq '.categories.homebrew_formulae[] | .name'

# Output:
"git"
"node"
"python@3.11"
"maven"
"gh"
[...]
```

---

## Web Interface Guide

### Navigation Bar

The navbar has three items:

- **Dashboard** - Main configuration overview
- **Scan ▼**
  - *Run Scan* - Scan your system (auto-saves + generates installation files)
  - *Saved Scans* - Browse saved scans, load them, or view installation files
  - *View JSON Scan Data* - Inspect raw scan data as JSON
- **Help** - This user manual

### Dashboard

The main dashboard shows all discovered items in a single scrollable table:

```
┌─────────────────────────────────────────────────────────────────────┐
│  MacDitto  Dashboard  Scan▼  Help                                    │
│─────────────────────────────────────────────────────────────────────│
│  Mac Configuration                                                  │
│  Machine: Steve's MacBook Air   Scanned: 2026-02-17 10:00          │
│  Auto-saved: Scan data + install files saved. [Regenerate Files]   │
│─────────────────────────────────────────────────────────────────────│
│  Summary                                                            │
│  [ 42 Brew Pkgs ] [ 18 Cask Apps ] [ 67 Apps ] [ 12 Ext ] [ 8 Prefs ]│
│─────────────────────────────────────────────────────────────────────│
│  Setup Notes ▼ (click to expand)                                    │
│─────────────────────────────────────────────────────────────────────│
│  Installed Items                              🔍 Search apps...      │
│  Legend: 📌 = In Dock   ▶️ = Starts at Login                        │
│  ┌────────┬─────────────┬──────────────┬───────────┬──────────────┬──────┐│
│  │Include │ Category ↕  │ Name ↕       │Method ↕   │ Location ↕   │Flags↕││
│  ├────────┼─────────────┼──────────────┼───────────┼──────────────┼──────┤│
│  │   ☑   │ Development │ IntelliJ IDEA│ manual    │ /Applications│ 📌   ││
│  │   ☑   │             │ Docker       │ cask      │ /Applications│ 📌▶️ ││
│  │   ☑   │             │ git          │ brew      │ brew         │  —   ││
│  │   ☑   │ Browsers    │ Brave Browser│ cask      │ /Applications│ 📌   ││
│  │   ☐   │ Utilities   │ python@3.9   │ brew      │ brew         │  —   ││
│  └────────┴─────────────┴──────────────┴───────────┴──────────────┴──────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### Summary Cards

Five clickable cards at the top of the dashboard jump to the relevant section:

| Card | What it counts |
|------|---------------|
| Brew Packages | Homebrew formulae (CLI tools) |
| Cask Apps | Homebrew casks (GUI apps) |
| Applications | Apps found in /Applications |
| Extensions | Browser extensions (Chrome, Brave) |
| Preferences | macOS system preferences captured |

### Items Table

All installed items appear in one flat, category-sorted table with these columns:

| Column | Description |
|--------|-------------|
| **Include** | Checkbox — uncheck to exclude from installation files |
| **Category** | Badge shown on the first row of each category group |
| **Name** | App or package name |
| **Description** | Short description (from Homebrew metadata where available) |
| **Install Method** | `brew`, `cask`, or `manual` |
| **Location** | Installation path (e.g., `/Applications`, `brew`) |
| **Install Command** | Ready-to-run command (e.g., `brew install git`) |
| **Flags** | 📌 if in Dock, ▶️ if starts at login |

**Sortable columns:** Click any column header (Category, Name, Install Method, Location, Flags) to sort ascending or descending.

Use the **Search** box to filter items by name in real time.

### Setup Notes

The collapsible **Setup Notes** section lets you write free-form markdown notes that:

- Are saved with each profile
- Are exported as `SETUP_NOTES.md` when you export
- Useful for login hints, manual steps, license locations, and custom settings

### Navbar Actions Explained

| Action | What it does |
|--------|-------------|
| **Run Scan** | Scans your Mac; auto-saves scan + generates installation files |
| **Saved Scans** | Opens a modal listing all saved scans with installation file links |
| **View JSON Scan Data** | Opens raw scan JSON in the browser (under Scan menu) |
| **Regenerate Files** | (Dashboard button) Regenerates installation files after toggling items |

---

## Workflows

### Workflow 1: Setting Up a Brand New Mac

**Goal:** Replicate your current Mac setup on a new machine

**Steps:**

1. **On current Mac:**
   ```bash
   # Run MacDitto
   python3 -m macditto.app

   # In browser:
   # 1. Click Scan > Run Scan (auto-saves + generates install files)
   # 2. Review items in the table, uncheck anything you don't want
   # 3. Click "Regenerate Files" to update installation files
   # 4. Commit to Git or copy to USB
   ```

2. **Transfer files:**
   ```bash
   # Option 1: Git
   git add scans/scan_*/
   git commit -m "New Mac setup scan"
   git push

   # Option 2: USB/AirDrop
   # Copy the scan directory
   ```

3. **On new Mac:**
   ```bash
   # Install Homebrew first
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   # Get MacDitto files
   git clone https://github.com/yourusername/MacDitto.git
   cd MacDitto/scans/scan_MACHINENAME_YYYYMMDD_HHMMSS/

   # Run install script
   chmod +x install.sh
   ./install.sh

   # Follow manual steps
   open MANUAL_STEPS.md
   ```

4. **Verify setup:**
   ```bash
   # Install MacDitto on new Mac
   pip3 install -r requirements.txt

   # Run scan to verify
   python3 -m macditto.app
   # Compare with original profile
   ```

**Time estimate:**
- Current Mac: 5-10 minutes
- New Mac automated: 20-40 minutes (depending on download speeds)
- New Mac manual steps: 20-60 minutes

---

### Workflow 2: Monthly Environment Snapshot

**Goal:** Track your environment changes over time

**Steps:**

```bash
# Set up monthly cron job (optional)
# Add to crontab:
0 9 1 * * cd /path/to/MacDitto && python3 scan.py

# Or run manually each month:
python3 -m macditto.app
# Click Scan > Run Scan (auto-saves as scan_MachineName_YYYYMMDD_HHMMSS)

# Compare with last month:
# Select profiles: monthly-2026-01 vs monthly-2026-02
# Click "Compare"
# See what you installed/removed
```

**Benefits:**
- Track environment bloat
- Document changes for troubleshooting
- Remember what you installed and when
- Archive for future reference

---

### Workflow 3: Team Environment Standardization

**Goal:** Ensure all team members have consistent development environment

**Steps:**

1. **Create team standard:**
   ```bash
   # On reference machine
   # Install all team-required tools
   # Run MacDitto scan
   # Save as "team-standard-2026-Q1"
   # Export and commit to team repo
   ```

2. **Team members apply:**
   ```bash
   # Each developer
   git clone team-repo/macditto-standards
   cd team-standard-2026-Q1/
   ./install.sh
   # Follow MANUAL_STEPS.md
   ```

3. **Verify compliance:**
   ```bash
   # Each developer runs scan
   # Compare with team standard
   # Fix any discrepancies
   ```

**Use cases:**
- Onboarding new developers
- Quarterly environment updates
- CI/CD environment matching
- Troubleshooting "works on my machine" issues

---

## Project Structure

```
MacDitto/
├── macditto/              # Main package
│   ├── __init__.py        # Package initialization
│   ├── app.py             # Flask web application
│   ├── scanner.py         # Environment scanner module
│   ├── models.py          # Data models (ScanProfile, etc.)
│   ├── utils.py           # Utility functions (categorization)
│   ├── templates/         # HTML templates for web interface
│   │   ├── base.html      # Base template with navbar and modals
│   │   ├── dashboard.html # Main dashboard with items table
│   │   ├── diff.html      # Profile comparison view
│   │   └── help.html      # Help/documentation page
│   └── static/            # CSS, JavaScript, images
│       ├── style.css      # Application styling
│       └── app.js         # Client-side JavaScript
├── scans/                 # Auto-saved scans with installation files
│   ├── .gitkeep
│   ├── scan_history.json  # Unified scan history
│   └── scan_*/            # Timestamped scan directories
│       ├── saved_scan.json     # Complete scan data
│       ├── Brewfile            # Homebrew bundle file
│       ├── install.sh          # Automated install script
│       ├── MANUAL_STEPS.md     # Manual installation checklist
│       ├── SETUP_NOTES.md      # Personal setup notes
│       └── SOFTWARE_CATALOG.md # Software catalog with descriptions
├── tests/                 # Test suite
│   ├── __init__.py
│   ├── test_scanner.py    # Scanner module tests
│   ├── test_models.py     # Data model tests
│   ├── test_utils.py      # Utility function tests
│   ├── test_flask_app.py  # Flask route tests
│   └── test_integration.py # End-to-end tests
├── docs/                  # Documentation
│   ├── REQUIREMENTS.md    # Project requirements
│   ├── FLASK_IMPLEMENTATION.md # Flask details
│   └── QUICK_START_NEXT_SESSION.md # Session state
├── requirements.txt       # Python dependencies
├── scan.py                # CLI scan script
├── run_app.sh             # Startup script (optional)
├── README.md              # This file
├── QUICKSTART.md          # Quick reference
└── .gitignore             # Git ignore rules
```

---

## Testing

MacDitto includes a comprehensive test suite with 61 tests covering all modules.

### Run All Tests

```bash
# Basic test run
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=macditto

# Run specific test file
pytest tests/test_scanner.py -v

# Run specific test
pytest tests/test_scanner.py::test_scan_homebrew_formulae -v
```

### Test Coverage

```bash
# Generate detailed coverage report
pytest tests/ --cov=macditto --cov-report=html

# Open in browser
open htmlcov/index.html
```

**Current coverage:** 100% of core modules

### Test Categories

1. **Unit Tests** (`test_scanner.py`, `test_models.py`, `test_utils.py`)
   - Test individual functions and classes
   - Mock external dependencies
   - Fast execution (< 1 second)

2. **Integration Tests** (`test_integration.py`)
   - Test end-to-end workflows
   - Actual file system operations
   - Slower execution (5-10 seconds)

3. **Flask Tests** (`test_flask_app.py`)
   - Test web routes and responses
   - Test JSON API endpoints
   - Test error handling

---

## Troubleshooting

### Issue: Scan takes too long (> 2 minutes)

**Cause:** Large number of Homebrew packages or applications

**Solution:**
```bash
# Check Homebrew package count
brew list --formula | wc -l
brew list --cask | wc -l

# If > 200 packages, consider:
# 1. Cleaning up unused packages
brew cleanup
brew autoremove

# 2. Running scan in background
python3 scan.py &
```

---

### Issue: Some applications not detected

**Cause:** Apps installed in non-standard locations

**Solution:**
```bash
# MacDitto only scans /Applications by default
# To include other locations, manually add to profile

# Check where app is installed
mdfind -name "AppName.app"

# Add manually via web interface or edit JSON
```

---

### Issue: Homebrew cask not installing on new Mac

**Cause:** Cask name changed or package no longer available

**Solution:**
```bash
# Search for current name
brew search <old-cask-name>

# Update Brewfile manually
# Replace old name with new name

# Or install manually
brew install --cask <new-name>
```

---

### Issue: Permission denied during install.sh

**Cause:** Script not executable or wrong permissions

**Solution:**
```bash
# Make script executable
chmod +x install.sh

# Run with sudo if needed (for system changes)
sudo ./install.sh

# Check script contents first
less install.sh
```

---

### Issue: Shell config not working after copying

**Cause:** Environment-specific paths or settings

**Solution:**
```bash
# Review .zshrc before using
cat ~/.zshrc

# Comment out machine-specific paths
# Example: Change absolute paths to relative
# OLD: export PATH="/Users/steve/bin:$PATH"
# NEW: export PATH="$HOME/bin:$PATH"

# Reload shell
source ~/.zshrc
```

---

### Issue: Browser extensions can't be auto-installed

**Cause:** Browser security prevents automated extension installation

**Solution:**
This is expected behavior. Follow manual steps:

1. Open `MANUAL_STEPS.md`
2. Find browser extension section
3. Click links to Chrome/Brave Web Store
4. Install each extension manually
5. Configure extension settings

**Tip:** Some extensions support cloud sync. Enable sync in browser settings to automatically get extensions.

---

### Issue: MacDitto web interface won't start

**Cause:** Port 5000 already in use or missing dependencies

**Solution:**
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill process using port 5000
kill -9 <PID>

# Or use different port
FLASK_RUN_PORT=5001 python3 -m macditto.app

# Check dependencies
pip3 install -r requirements.txt

# Verify Flask is installed
python3 -c "import flask; print(flask.__version__)"
```

---

### Issue: Git config contains sensitive data

**Cause:** Credentials stored in .gitconfig

**Solution:**
```bash
# MacDitto exports .gitconfig
# Review before committing:
cat ~/.gitconfig

# Remove sensitive data manually:
# [credential]
#     helper = store  <-- Remove this

# Or exclude credentials from export
# Edit exported .gitconfig before committing
```

---

### Issue: Scan results differ from actual installs

**Cause:** Cached data or items installed after scan

**Solution:**
```bash
# Run fresh scan
# Click "Rescan" in web interface

# Or from CLI
python3 scan.py

# Compare timestamps
ls -ltr scans/

# Use most recent scan
```

---

## Understanding Saved Scans

### What Happens When You Scan

Every scan automatically:
1. Captures your full Mac configuration
2. Saves scan data as `saved_scan.json`
3. Generates all installation files (Brewfile, install.sh, etc.)
4. Records the scan in history

**Output:** All files saved in `scans/scan_{MachineName}_{TIMESTAMP}/`

**When to scan:**
- Before setting up a new Mac
- Monthly/quarterly for historical tracking
- Before major system updates

### Regenerating Installation Files

After loading a saved scan, you can toggle items on/off in the dashboard. Click **"Regenerate Files"** to update the installation files with your changes.

---

### How to Use Installation Files

**On the NEW Mac:**

```bash
# 1. Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Transfer scan files (via Git, USB, or AirDrop)
# If using Git:
git clone https://github.com/yourusername/MacDitto.git
cd MacDitto/scans/scan_MachineName_YYYYMMDD_HHMMSS/

# 3. Run the install script
chmod +x install.sh
./install.sh

# 4. Follow manual steps
open MANUAL_STEPS.md
```

**What the install script does:**
- Installs all Homebrew packages
- Installs GUI apps via `brew cask`
- Copies shell configurations
- Copies Git config
- Applies macOS system preferences

**Time estimate:**
- Automated script: 20-40 minutes (depending on download speeds)
- Manual steps: 20-60 minutes

---

## FAQ

**Q: Does MacDitto work on Apple Silicon (M1/M2/M3)?**

A: Yes! MacDitto is Python-based and works on both Intel and Apple Silicon Macs.

---

**Q: Can I use MacDitto to migrate from Intel to Apple Silicon?**

A: Yes, but some casks may have architecture-specific versions. MacDitto will attempt to install the correct version for the target architecture.

---

**Q: Is my personal data safe in MacDitto scans?**

A: MacDitto captures configuration files but excludes:
- Passwords
- API keys/tokens
- SSH private keys
- Browser history
- Personal documents

Always review exported files before committing to public Git repos.

---

**Q: Can I customize what MacDitto scans?**

A: Currently, scans are comprehensive. Future versions will support:
- Include/exclude patterns
- Custom scan locations
- Selective category scanning

---

**Q: Can I run MacDitto on macOS 12.7.6 (Monterey)?**

A: **Yes!** MacDitto is fully compatible with macOS 12.7.6 and later. Tested and working on:
- macOS 12.7.6 (Monterey) ✅
- macOS 13.x (Ventura) ✅
- macOS 14.x (Sonoma) ✅
- macOS 15.x (Sequoia) ✅

Requirements:
- Python 3.9+ (install via `brew install python3`)
- Homebrew (install from https://brew.sh)

---

**Q: Does MacDitto support Windows or Linux?**

A: No. MacDitto is macOS-specific due to:
- Homebrew dependency
- macOS `defaults` commands
- macOS-specific app locations

---

**Q: Can I run MacDitto without the web interface?**

A: Yes! Use `scan.py` for CLI-only scanning:
```bash
python3 scan.py
# Outputs to scan_results.json
```

---

**Q: How do I update MacDitto?**

```bash
cd MacDitto
git pull origin main
pip3 install -r requirements.txt
```

---

**Q: Can MacDitto handle multiple Macs?**

A: Yes! Each scan auto-saves with the machine name:
```bash
# Scans are auto-named per machine
scans/scan_MacBookAir_20260215_100000/
scans/scan_MacBookPro_20260215_143022/
scans/scan_iMacStudio_20260215_160000/
```

---

## Contributing

Contributions are welcome! Here's how to contribute:

### Report Issues

```bash
# Check existing issues
https://github.com/yourusername/MacDitto/issues

# Create new issue with:
- Clear title
- Steps to reproduce
- Expected vs actual behavior
- MacDitto version
- macOS version
```

### Submit Pull Requests

```bash
# 1. Fork repository
# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and add tests
# 4. Run test suite
pytest tests/ -v

# 5. Ensure all tests pass
# 6. Commit changes
git commit -m "Add feature: description"

# 7. Push to your fork
git push origin feature/your-feature-name

# 8. Create pull request
```

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/MacDitto.git
cd MacDitto

# Install dev dependencies
pip3 install -r requirements.txt
pip3 install pytest pytest-cov

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=macditto

# Start Flask in debug mode
FLASK_DEBUG=1 python3 -m macditto.app
```

### Code Style

- Follow PEP 8
- Add docstrings to all functions/classes
- Write tests for new features
- Update README with new features

---

## License

MIT License

Copyright (c) 2026 Steve Souza

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Author

**Steve Souza**

- GitHub: [@yourusername](https://github.com/yourusername)
- Email: steve@example.com

---

## Version History

**v0.1.0** (2026-02-15)
- Initial release
- Scanner module complete
- Flask web interface
- Auto-saved scans with installation files
- Sortable dashboard with Location column
- 61 tests, 100% passing

---

## Acknowledgments

- **Homebrew** - Package management backbone
- **Flask** - Web framework
- **pytest** - Testing framework

---

## Support

- **Documentation:** This README + `docs/` directory
- **Issues:** https://github.com/yourusername/MacDitto/issues
- **Discussions:** https://github.com/yourusername/MacDitto/discussions

---

**Last Updated:** 2026-02-18
