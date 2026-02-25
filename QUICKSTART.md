# MacDitto Quick Start Guide

Get MacDitto running in 60 seconds.

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Start the Web Interface

```bash
./run_app.sh
```

**Or run directly:**
```bash
python -m macditto.app
```

## Step 3: Open Your Browser

Navigate to:
```
http://localhost:5001
```

## Step 4: Run Your First Scan

1. Click **Scan > Run Scan** in the navigation bar
2. Wait 10-30 seconds for the scan to complete
3. View your Mac's configuration on the dashboard
4. Scan data and installation files are auto-saved!

## What You'll See

- **Summary Cards** showing total counts of packages, apps, extensions
- **Category Sections** organizing items by type (Development, Browsers, etc.)
- **Item Details** with install methods and status flags (📌 in Dock, ▶️ starts on login)
- **Enable/Disable Checkboxes** for each item
- **Regenerate Files** button to update installation files after toggling items

## Common Tasks

### Load a Saved Scan

```
Click "Scan" > "Saved Scans" > Click on a scan row
```

Scans are auto-saved in `scans/` directory.

### Regenerate Installation Files

After toggling items on/off:
```
Click "Regenerate Files" button in the dashboard banner
```

### View Installation Files

```
Click "Scan" > "Saved Scans" > Click file buttons (Brew, install.sh, etc.)
```

Each saved scan includes:
- `saved_scan.json` - Complete scan data
- `Brewfile` - Homebrew packages
- `install.sh` - Automated install script
- `MANUAL_STEPS.md` - Manual instructions
- `SETUP_NOTES.md` - Your personal notes
- `SOFTWARE_CATALOG.md` - Software catalog
- `DOTFILES.md` - Shell configs, git config, SSH, crontab, macOS defaults

### Compare Two Scans

```
Navigate to: /diff/scan_dir1/scan_dir2
```

Shows what changed between scans.

## For New Mac Setup

### On your current Mac:

1. Run MacDitto scan (auto-saves everything)
2. Review and disable unwanted items
3. Click "Regenerate Files" to update
4. Commit `scans/` directory or copy to USB

### On your new Mac:

1. Install Homebrew:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Clone MacDitto:
   ```bash
   git clone <your-repo-url>
   cd MacDitto
   pip install -r requirements.txt
   ```

3. Run the install script:
   ```bash
   cd scans/scan_MachineName_YYYYMMDD_HHMMSS/
   chmod +x install.sh
   ./install.sh
   ```

4. Follow remaining steps in `MANUAL_STEPS.md`

## Troubleshooting

**Port 5001 already in use?**
```bash
python -m macditto.app --port 5002
```

**Scan not working?**
- Check Homebrew is installed: `brew --version`
- Check permissions for system access

**Items missing?**
- Standard macOS apps are filtered out by design
- Only directly installed Homebrew packages shown (not dependencies)

## Learn More

- [Flask Web Interface Guide](README_FLASK.md)
- [Full Requirements](docs/REQUIREMENTS.md)
- [Implementation Details](docs/FLASK_IMPLEMENTATION.md)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=macditto
```

## Need Help?

Check the logs in the Flask app console for error messages.

---

**Happy replicating!** 🚀
