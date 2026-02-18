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
- **Sortable columns** — click any column header to sort ascending/descending
- Enable/disable items for installation on target machine
- View item properties (install method, location, dock status, login status)
- **Regenerate Files** button to update installation files after changes

### Scan
- Click "Scan > Run Scan" to run a new environment scan
- Scans all Homebrew packages, applications, browser extensions, and system preferences
- Every scan auto-saves data and generates installation files
- Results are displayed immediately on the dashboard

### Saved Scans
- Click "Scan > Saved Scans" to browse all saved scans
- Each scan includes installation files (Brewfile, install.sh, etc.)
- Click a row to load a scan into the dashboard
- Click file buttons to view individual installation files

### View JSON Scan Data
- Click "Scan > View JSON Scan Data" to see raw scan JSON
- Copy or download the JSON for external use

### Compare Scans
- Navigate to `/diff/<scan_dir1>/<scan_dir2>` to compare two scans
- See added, removed, and common items between scans
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
├── scans/                  # Auto-saved scans with installation files
│   ├── scan_history.json
│   └── scan_*/             # Timestamped scan directories
│       ├── saved_scan.json
│       ├── Brewfile
│       ├── install.sh
│       ├── MANUAL_STEPS.md
│       ├── SETUP_NOTES.md
│       └── SOFTWARE_CATALOG.md
├── requirements.txt        # Python dependencies
└── README_FLASK.md        # This file
```

## API Endpoints

### GET /
Main dashboard showing scanned items

### POST /scan
Run new environment scan (auto-saves scan + generates installation files)

### GET /saved_scans
List all saved scans with installation file paths
Returns JSON with scan list filtered to completed scans with existing directories

### GET /load_scan/<scan_dirname>
Load a saved scan by directory name into the dashboard

### POST /regenerate
Regenerate installation files for the currently loaded scan
Use after toggling items on/off

### POST /toggle_item
Toggle enabled/disabled state for an item
Body: `{"item_type": "homebrew_cask", "index": 0, "enabled": true}`

### GET /diff/<scan_dir1>/<scan_dir2>
Compare two saved scans
Shows added, removed, and common items

### GET /scan_history
Get full scan history (including failed scans)

### GET /view_json
View current scan data as formatted JSON

### GET /api/profile/json
API endpoint to get current scan data as JSON

### GET /open_file?path=<filepath>
Serve a file for viewing in the browser

## Tips

### Running a Full Scan
1. Click "Scan > Run Scan" in the navigation
2. Wait for scan to complete (may take 10-30 seconds)
3. Scan auto-saves with all installation files
4. Review results on dashboard
5. Toggle items as needed, then click "Regenerate Files"

### Preparing for New Machine Setup
1. Run a full scan on your current machine
2. Review and enable only the items you want on the new machine
3. Click "Regenerate Files" to update installation files
4. Commit the scan directory to Git or copy to USB drive
5. On new machine:
   - Run the `install.sh` script
   - Follow instructions in `MANUAL_STEPS.md`

### Tracking Changes Over Time
1. Run scans periodically (weekly/monthly) — each auto-saves
2. Use scan comparison to see what's changed
3. Keep scans in Git to track history

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
- Saved scans may contain sensitive information (file paths, configurations)
- Review installation files before sharing or committing to public repos
- The default secret key should be changed for production use

## Next Steps

After using the web interface:
1. Review the generated `MANUAL_STEPS.md` for items requiring manual setup
2. Test the `install.sh` script in a VM or test environment first
3. Back up your current machine before running on a new machine
4. Verify installation with another scan on the new machine
