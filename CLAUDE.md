# MacDitto - Project Guide

MacDitto is a Python/Flask tool for scanning and replicating macOS environments. It captures installed software, configurations, and preferences, then generates scripts to replicate the setup on a new Mac.

## Key Commands

```bash
# Run the web app (default port 5001)
python3 -m macditto.app

# Run all tests (104 tests)
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=macditto

# Run a specific test file
pytest tests/test_inspectors.py -v
```

## Architecture

```
macditto/
├── app.py          # Flask routes + file generation (Brewfile, install.sh,
│                   #   MANUAL_STEPS.md, SETUP_NOTES.md, SOFTWARE_CATALOG.md, DOTFILES.md)
├── scanner.py      # Scanner class with 14-step scan_all() method, progress callbacks
├── models.py       # Dataclasses: ScanProfile, Item, BrowserExtension, ShellConfig, SystemPreference
├── utils.py        # Helpers: run_command(), detect_category(), is_standard_macos_app()
├── inspectors.py   # Decorator-based @register_inspector() for deep tool inspection
├── templates/      # Jinja2: base.html, dashboard.html, diff.html, help.html, json_viewer.html
└── static/         # style.css, app.js, favicon-32.png
```

## Key Patterns

- **Inspector system**: Add new inspectors by decorating a function with `@register_inspector("toolname", match_names=["name1"])`. Return `{"tool": str, "items": list, "restore_commands": list, "restore_note": str}` or `None`. See `inspectors.py` for Ollama and Docker examples.
- **Progress callbacks**: `scan_all()` reports progress via `progress_callback(step_name, step_number, total_steps, item_counts)`.
- **Auto-save**: Every scan saves to `scans/scan_{MachineName}_{TIMESTAMP}/` with all generated files.
- **Notes system**: Machine Notes persist in `scans/machine_notes.md` (shared across scans). Scan Notes are per-scan in each scan's `SETUP_NOTES.md`.
- **Help page**: `/help` renders `README.md` via `help.html` template — updating README updates in-app help.

## Testing Conventions

- All tests use `pytest` with `unittest.mock`
- External commands (`brew`, `defaults`, `osascript`, `ollama`, `docker`) are always mocked
- Test files mirror source: `test_scanner.py`, `test_models.py`, `test_utils.py`, `test_flask_app.py`, `test_integration.py`, `test_inspectors.py`, `test_scan_progress.py`
- Tests are self-contained (no shared fixtures file)

## Dependencies

- **Runtime**: Flask >= 3.0.0 (only dependency)
- **Test**: pytest >= 7.4.0, pytest-cov >= 4.1.0
- **Python**: 3.9+
- **macOS**: 12.0+ (Monterey or later)
- **Port**: Default 5001 (not 5000, which conflicts with macOS AirPlay Receiver)
