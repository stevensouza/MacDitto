# MacDitto Flask Web Interface

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Flask Application

```bash
# From the project root directory
python -m macditto.app

# Or using Flask directly
export FLASK_APP=macditto.app
export FLASK_ENV=development
flask run
```

The application will start on `http://localhost:5000`

### 3. Access the Web Interface

Open your browser and navigate to:
```
http://localhost:5000
```

## Features

### Dashboard
- View all scanned items organized by category
- See summary statistics (packages, apps, extensions, preferences)
- Enable/disable items for installation on target machine
- View item properties (install method, dock status, login status)

### Scan
- Click "Scan" in the navigation to run a new environment scan
- Scans all Homebrew packages, applications, browser extensions, and system preferences
- Results are displayed immediately on the dashboard

### Save Profiles
- Click "Save" to save the current scan as a dated profile
- Optional: Provide a custom name for the profile
- Profiles are saved in the `profiles/` directory as JSON files

### Load Profiles
- Click "Profiles" to view all saved profiles
- Click on a profile to load it
- See when each profile was created and its file size

### Export
- Click "Export" to generate installation files
- Creates:
  - `Brewfile` - Homebrew bundle file
  - `install.sh` - Automated installation script
  - `MANUAL_STEPS.md` - Manual installation instructions
  - `macditto_config.json` - Full configuration backup
- Files are saved in `output/export_TIMESTAMP/`

### Compare Profiles
- Navigate to `/diff/<profile1>/<profile2>` to compare two profiles
- See added, removed, and common items between profiles
- Useful for tracking environment changes over time

## Directory Structure

```
MacDitto/
├── macditto/
│   ├── app.py              # Flask application
│   ├── scanner.py          # Environment scanner
│   ├── models.py           # Data models
│   ├── utils.py            # Utilities
│   ├── templates/          # HTML templates
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   └── diff.html
│   └── static/             # CSS and JavaScript
│       ├── style.css
│       └── app.js
├── profiles/               # Saved scan profiles
├── output/                 # Generated export files
├── requirements.txt        # Python dependencies
└── README_FLASK.md        # This file
```

## API Endpoints

### GET /
Main dashboard showing scanned items

### POST /scan
Run new environment scan
Returns JSON with scan results

### POST /save
Save current profile
Body: `{"name": "optional_profile_name"}`

### GET /profiles
List all saved profiles
Returns JSON with profile list

### GET /load/<profile_name>
Load a saved profile by filename

### POST /toggle_item
Toggle enabled/disabled state for an item
Body: `{"item_type": "homebrew_cask", "index": 0, "enabled": true}`

### GET /diff/<profile1>/<profile2>
Compare two saved profiles
Shows added, removed, and common items

### GET /export
Generate installation files
Creates Brewfile, install.sh, MANUAL_STEPS.md, and config JSON

## Tips

### Running a Full Scan
1. Click "Scan" in the navigation
2. Wait for scan to complete (may take 10-30 seconds)
3. Review results on dashboard
4. Enable/disable items as needed
5. Click "Save" to create a snapshot

### Preparing for New Machine Setup
1. Run a full scan on your current machine
2. Review and enable only the items you want on the new machine
3. Click "Export" to generate installation files
4. Commit the `output/` directory to Git or copy to USB drive
5. On new machine:
   - Run the `install.sh` script
   - Follow instructions in `MANUAL_STEPS.md`

### Tracking Changes Over Time
1. Save profiles periodically (weekly/monthly)
2. Use profile comparison to see what's changed
3. Keep profiles in Git to track history

## Troubleshooting

### Port Already in Use
If port 5000 is already in use, specify a different port:
```bash
python -m macditto.app --port 5001
# Or with Flask:
flask run --port 5001
```

### Scan Takes Too Long
- Browser extension scanning can be slow if you have many extensions
- System preference scanning requires reading many defaults
- First scan is always slower; subsequent scans reuse cached data

### Items Not Appearing
- Some applications may be filtered out (standard macOS apps)
- Homebrew packages must be directly installed (not dependencies)
- Browser extensions require browsers to be installed

## Development

### Running in Debug Mode
```bash
export FLASK_ENV=development
python -m macditto.app
```

Debug mode enables:
- Auto-reload on code changes
- Detailed error messages
- Interactive debugger

### Testing the Scanner
```bash
python -c "from macditto.scanner import Scanner; s = Scanner(); p = s.scan_all(); print(f'Found {len(p.homebrew_formulae)} brew packages')"
```

## Security Notes

- The Flask app is for LOCAL USE ONLY
- Do not expose to the internet without proper authentication
- Profiles may contain sensitive information (file paths, configurations)
- Review exported files before sharing or committing to public repos
- The default secret key should be changed for production use

## Next Steps

After using the web interface:
1. Review the generated `MANUAL_STEPS.md` for items requiring manual setup
2. Test the `install.sh` script in a VM or test environment first
3. Back up your current machine before running on a new machine
4. Verify installation with another scan on the new machine
