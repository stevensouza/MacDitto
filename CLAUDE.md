# CLAUDE.md - MacDitto

## Project Overview

MacDitto is a Python/Flask tool that scans a macOS environment (installed software, configs, preferences) and generates automated scripts to replicate it on a new Mac.

## Tech Stack

- **Language:** Python 3.9+
- **Web Framework:** Flask 3.0+
- **Testing:** pytest, pytest-cov
- **Linting:** black, flake8
- **Platform:** macOS only (12.0+ / Monterey and later)

## Project Structure

```
macditto/           # Main package
  app.py            # Flask web application (routes, API endpoints)
  scanner.py        # Environment scanner (Homebrew, apps, Dock, etc.)
  models.py         # Data models (ScanProfile, etc.)
  utils.py          # Utility functions (categorization)
  templates/        # Jinja2 HTML templates
  static/           # CSS (style.css) and JS (app.js)
tests/              # Test suite
  test_scanner.py   # Scanner unit tests
  test_models.py    # Model unit tests
  test_utils.py     # Utility unit tests
  test_flask_app.py # Flask route tests
  test_integration.py # End-to-end tests
  test_scan_progress.py # Scan progress tests
profiles/           # Saved scan profiles (JSON, gitignored)
output/             # Generated export files (gitignored)
scan.py             # CLI scan entry point
run_app.sh          # Startup script
```

## Common Commands

```bash
# Run the web app
python3 -m macditto.app
# or
./run_app.sh

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=macditto

# Run a specific test file
pytest tests/test_scanner.py -v

# Lint
black macditto/ tests/
flake8 macditto/ tests/
```

## Key Conventions

- Flask app runs on port 5000 by default
- Profiles are saved as timestamped JSON files in `profiles/`
- Exports generate a directory in `output/export_TIMESTAMP/` containing Brewfile, install.sh, MANUAL_STEPS.md, SETUP_NOTES.md, SOFTWARE_CATALOG.md, and macditto_config.json
- The `profiles/` and `output/` directories contain personal data and are gitignored
- Follow PEP 8 style
- All new features should include tests
