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
http://localhost:5000
```

## Step 4: Run Your First Scan

1. Click the **"Scan"** button in the navigation bar
2. Wait 10-30 seconds for the scan to complete
3. View your Mac's configuration on the dashboard

## What You'll See

- **Summary Cards** showing total counts of packages, apps, extensions
- **Category Sections** organizing items by type (Development, Browsers, etc.)
- **Item Details** with install methods and status flags (📌 in Dock, ▶️ starts on login)
- **Enable/Disable Checkboxes** for each item

## Common Tasks

### Save a Profile Snapshot

```
Click "Save" → Enter optional name → Click "Save"
```

Profiles are saved in `profiles/` directory.

### Load a Saved Profile

```
Click "Profiles" → Click on a profile name
```

### Export Install Scripts

```
Click "Export"
```

Files are generated in `output/export_TIMESTAMP/`:
- `Brewfile` - Homebrew packages
- `install.sh` - Automated install script
- `MANUAL_STEPS.md` - Manual instructions
- `macditto_config.json` - Full config

### Compare Two Profiles

```
Navigate to: /diff/profile1.json/profile2.json
```

Shows what changed between profiles.

## For New Mac Setup

### On your current Mac:

1. Run MacDitto scan
2. Review and disable unwanted items
3. Click "Export"
4. Commit `output/` directory or copy to USB

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
   cd output/export_TIMESTAMP/
   chmod +x install.sh
   ./install.sh
   ```

4. Follow remaining steps in `MANUAL_STEPS.md`

## Troubleshooting

**Port 5000 already in use?**
```bash
python -m macditto.app --port 5001
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

All 76 tests should pass.

## Need Help?

Check the logs in the Flask app console for error messages.

---

**Happy replicating!** 🚀
