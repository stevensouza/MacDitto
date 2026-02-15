# MacDitto - Mac Environment Duplication Tool

A Python tool for scanning, capturing, and replicating macOS environments across machines.

## Features

- Scan your Mac for installed software, configurations, and preferences
- Web-based GUI for managing scans and profiles
- Save and load configuration snapshots
- Generate automated install scripts for new Macs
- Compare profiles to track environment changes
- Export Brewfile, install scripts, and manual setup instructions

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd MacDitto

# Install dependencies
pip install -r requirements.txt
```

### Run the Web Interface

```bash
# Option 1: Use the startup script
./run_app.sh

# Option 2: Run directly
python -m macditto.app
```

Then open your browser to `http://localhost:5000`

### Basic Usage

1. Click "Scan" to analyze your current Mac configuration
2. Review the discovered items on the dashboard
3. Enable/disable items you want to replicate
4. Click "Save" to create a profile snapshot
5. Click "Export" to generate install scripts

## What MacDitto Scans

- **Homebrew packages** (formulae and casks)
- **Applications** (/Applications directory)
- **Dock items** (pinned apps)
- **Login items** (apps that start on login)
- **Shell configurations** (.zshrc, .bash_profile, etc.)
- **Git configuration** (.gitconfig)
- **Browser extensions** (Chrome, Brave)
- **Browser bookmarks**
- **macOS system preferences** (Dock, Trackpad, Keyboard, etc.)

## Project Structure

```
MacDitto/
├── macditto/           # Main package
│   ├── app.py          # Flask web application
│   ├── scanner.py      # Environment scanner
│   ├── models.py       # Data models
│   ├── utils.py        # Utilities
│   ├── templates/      # HTML templates
│   └── static/         # CSS and JavaScript
├── profiles/           # Saved scan profiles
├── output/             # Generated export files
├── tests/              # Test suite
├── docs/               # Documentation
└── requirements.txt    # Python dependencies
```

## Documentation

- [Flask Web Interface Guide](README_FLASK.md)
- [Requirements and Architecture](docs/REQUIREMENTS.md)

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=macditto

# Run specific test file
pytest tests/test_scanner.py -v
```

## Use Cases

### Setting Up a New Mac

1. **On your current Mac:**
   - Run MacDitto scan
   - Save the profile
   - Export install scripts
   - Commit to Git or copy to USB

2. **On your new Mac:**
   - Install Homebrew
   - Clone MacDitto repo
   - Run the generated `install.sh` script
   - Follow `MANUAL_STEPS.md` for remaining setup

### Tracking Environment Changes

1. Save profiles periodically (weekly/monthly)
2. Use profile comparison to see what changed
3. Keep profiles in version control to track history

### Team Environment Standardization

1. Create a "team standard" profile
2. Share via Git repository
3. Team members run the install script to match the standard

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Author

Steve Souza

## Version

0.1.0 - Initial release with scanner module and Flask web interface
