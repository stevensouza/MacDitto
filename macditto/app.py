"""
Flask web application for MacDitto - Mac Environment Duplication Tool.

Provides web interface for scanning, viewing, saving, and managing Mac configurations.
"""

import os
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for, Response

from .scanner import Scanner
from .models import ScanProfile


app = Flask(__name__)
app.config['SECRET_KEY'] = 'macditto-dev-secret-key-change-in-production'

# Global variables for current scan profile
current_profile = None
profiles_dir = Path(__file__).parent.parent / 'profiles'
output_dir = Path(__file__).parent.parent / 'output'
export_history_file = output_dir / 'export_history.json'
scan_history_file = output_dir / 'scan_history.json'

# Global variables for scan tracking
scan_in_progress = False
scan_progress = {
    'current_step': '',
    'step_number': 0,
    'total_steps': 10,
    'percentage': 0,
    'item_counts': {},
    'completed': False,
    'error': None
}
scan_start_time = None

# Ensure directories exist
profiles_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)


# Disable caching for all responses (especially static files)
@app.after_request
def add_no_cache_headers(response):
    """Add headers to disable browser caching during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/')
def dashboard():
    """
    Main dashboard showing all scanned items organized by category.
    """
    global current_profile

    # Load most recent profile if current_profile is None
    if current_profile is None:
        current_profile = load_most_recent_profile()

    if current_profile is None:
        # No profile exists, show empty dashboard with scan button
        return render_template('dashboard.html',
                             profile=None,
                             items_by_category={},
                             category_counts={})

    # Organize items by category
    items_by_category = organize_items_by_category(current_profile)

    # Calculate counts per category
    category_counts = {category: len(items) for category, items in items_by_category.items()}

    return render_template('dashboard.html',
                         profile=current_profile,
                         items_by_category=items_by_category,
                         category_counts=category_counts)


@app.route('/scan', methods=['POST'])
def scan():
    """
    Run new scan using Scanner.scan_all().
    Launches scan in background thread and returns immediately.
    """
    global scan_in_progress, scan_progress, scan_start_time

    # Check if scan already running
    if scan_in_progress:
        return jsonify({
            'success': False,
            'error': 'Scan already in progress'
        }), 409

    # Reset progress state
    scan_in_progress = True
    scan_start_time = time.time()
    scan_progress = {
        'current_step': 'Initializing scan',
        'step_number': 0,
        'total_steps': 10,
        'percentage': 0,
        'item_counts': {},
        'completed': False,
        'error': None
    }

    # Launch scan in background thread
    thread = threading.Thread(target=run_scan_background)
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'message': 'Scan started'
    })


def run_scan_background():
    """
    Run scan in background thread with progress tracking.
    """
    global current_profile, scan_in_progress, scan_progress, scan_start_time

    def progress_callback(step_name, step_number, total_steps, item_counts):
        """Update global scan progress."""
        global scan_progress
        scan_progress = {
            'current_step': step_name,
            'step_number': step_number,
            'total_steps': total_steps,
            'percentage': int((step_number / total_steps) * 100),
            'item_counts': item_counts.copy(),
            'completed': False,
            'error': None
        }

    try:
        scanner = Scanner(progress_callback=progress_callback)
        current_profile = scanner.scan_all()

        # Calculate duration
        duration = time.time() - scan_start_time

        # Mark as completed
        scan_progress['completed'] = True
        scan_progress['percentage'] = 100

        # Save to scan history
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        scan_record = {
            'timestamp': timestamp,
            'scan_date': current_profile.scan_date,
            'end_date': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'machine_name': current_profile.machine_name,
            'item_counts': scan_progress['item_counts'].copy(),
            'status': 'completed'
        }
        save_scan_history(scan_record)

    except Exception as e:
        # Mark as error
        scan_progress['error'] = str(e)
        scan_progress['completed'] = True

        # Save failed scan to history
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        duration = time.time() - scan_start_time
        scan_record = {
            'timestamp': timestamp,
            'scan_date': datetime.now().isoformat(),
            'end_date': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'machine_name': 'Unknown',
            'item_counts': {},
            'status': 'failed',
            'error': str(e)
        }
        save_scan_history(scan_record)

    finally:
        scan_in_progress = False


@app.route('/scan_progress')
def scan_progress_stream():
    """
    Server-Sent Events endpoint for scan progress updates.
    Streams progress updates every 250ms.
    """
    def generate():
        """Generate SSE data stream."""
        global scan_progress

        while True:
            # Send current progress
            progress_data = json.dumps(scan_progress)
            yield f"data: {progress_data}\n\n"

            # Check if completed or error
            if scan_progress.get('completed'):
                break

            # Wait 250ms before next update
            time.sleep(0.25)

    return Response(generate(), mimetype='text/event-stream')


@app.route('/save', methods=['POST'])
def save_profile():
    """
    Save current profile with name.
    Accepts JSON: {"name": "profile_name"} (optional)
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No profile to save. Please run a scan first.'
        }), 400

    try:
        data = request.get_json() or {}
        profile_name = data.get('name', '')

        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if profile_name:
            filename = f"{profile_name}_{timestamp}.json"
        else:
            filename = f"macditto_{timestamp}.json"

        filepath = profiles_dir / filename
        current_profile.save(str(filepath))

        return jsonify({
            'success': True,
            'message': f'Profile saved successfully!',
            'filename': filename,
            'filepath': str(filepath.absolute())
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/profiles')
def list_profiles():
    """
    List all saved profiles.
    Returns JSON with profile list.
    """
    try:
        profiles = []
        for filepath in sorted(profiles_dir.glob('*.json'), reverse=True):
            stat = filepath.stat()
            profiles.append({
                'name': filepath.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })

        return jsonify({
            'success': True,
            'profiles': profiles
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/load/<profile_name>')
def load_profile(profile_name):
    """
    Load saved profile by name.
    """
    global current_profile

    try:
        filepath = profiles_dir / profile_name
        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': f'Profile {profile_name} not found'
            }), 404

        current_profile = ScanProfile.load(str(filepath))

        return redirect(url_for('dashboard'))
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/toggle_item', methods=['POST'])
def toggle_item():
    """
    Toggle enabled/disabled state for an item.
    Accepts JSON: {"item_type": "homebrew_cask", "index": 0, "enabled": true}
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No profile loaded'
        }), 400

    try:
        data = request.get_json()
        item_type = data.get('item_type')
        index = data.get('index')
        enabled = data.get('enabled')

        # Get the appropriate list
        item_list = get_item_list(current_profile, item_type)

        if item_list is None or index >= len(item_list):
            return jsonify({
                'success': False,
                'error': 'Invalid item type or index'
            }), 400

        # Update enabled state
        item_list[index].enabled = enabled

        return jsonify({
            'success': True,
            'message': 'Item updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/diff/<profile1>/<profile2>')
def diff_profiles(profile1, profile2):
    """
    Show differences between two profiles.
    """
    try:
        profile1_path = profiles_dir / profile1
        profile2_path = profiles_dir / profile2

        if not profile1_path.exists() or not profile2_path.exists():
            return jsonify({
                'success': False,
                'error': 'One or both profiles not found'
            }), 404

        p1 = ScanProfile.load(str(profile1_path))
        p2 = ScanProfile.load(str(profile2_path))

        diff = compute_diff(p1, p2)

        return render_template('diff.html',
                             profile1=profile1,
                             profile2=profile2,
                             p1=p1,
                             p2=p2,
                             diff=diff)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/export')
def export():
    """
    Generate install scripts and manual instructions.
    Returns downloadable files.
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No profile to export. Please run a scan first.'
        }), 400

    try:
        # Generate export files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_dir = output_dir / f"export_{timestamp}"
        export_dir.mkdir(exist_ok=True)

        # Generate Brewfile
        brewfile_path = export_dir / 'Brewfile'
        generate_brewfile(current_profile, brewfile_path)

        # Generate install.sh
        install_script_path = export_dir / 'install.sh'
        generate_install_script(current_profile, install_script_path)

        # Generate MANUAL_STEPS.md
        manual_steps_path = export_dir / 'MANUAL_STEPS.md'
        generate_manual_steps(current_profile, manual_steps_path)

        # Save profile config
        config_path = export_dir / 'macditto_config.json'
        current_profile.save(str(config_path))

        # Save to export history
        export_record = {
            'timestamp': timestamp,
            'export_date': datetime.now().isoformat(),
            'machine_name': current_profile.machine_name,
            'export_dir': str(export_dir.absolute()),
            'export_dirname': f'export_{timestamp}',
            'files': {
                'brewfile': str(brewfile_path.absolute()),
                'install_script': str(install_script_path.absolute()),
                'manual_steps': str(manual_steps_path.absolute()),
                'config': str(config_path.absolute())
            }
        }
        save_export_history(export_record)

        return jsonify({
            'success': True,
            'message': f'Export completed successfully!',
            'export_dir': str(export_dir.absolute()),
            'export_dirname': f'export_{timestamp}',
            'files': export_record['files']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/help')
def help_page():
    """
    Display help/user manual page.
    Renders README.md content as HTML.
    """
    try:
        # Read README.md file
        readme_path = Path(__file__).parent.parent / 'README.md'

        if readme_path.exists():
            with open(readme_path, 'r') as f:
                readme_content = f.read()
        else:
            readme_content = "# Help documentation not found\n\nPlease ensure README.md exists in the project root."

        return render_template('help.html', readme_content=readme_content)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/view_json')
def view_json():
    """
    View current profile as formatted JSON.
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No profile loaded. Please run a scan first.'
        }), 400

    try:
        # Convert profile to dict and format as JSON
        profile_dict = current_profile.to_dict()
        json_str = json.dumps(profile_dict, indent=2)

        return render_template('json_viewer.html', json_content=json_str, profile=current_profile)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profile/json')
def api_profile_json():
    """
    API endpoint to get current profile as JSON.
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No profile loaded'
        }), 400

    return jsonify(current_profile.to_dict())


@app.route('/export_history')
def export_history():
    """
    Get export history.
    Returns JSON list of past exports.
    """
    try:
        history = load_export_history()
        return jsonify({
            'success': True,
            'exports': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/scan_history')
def scan_history():
    """
    Get scan history.
    Returns JSON list of past scans.
    """
    try:
        history = load_scan_history()
        return jsonify({
            'success': True,
            'scans': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/open_file')
def open_file():
    """
    Open a file in the default application (via browser).
    For local files, serves them for viewing with proper MIME types.
    """
    filepath = request.args.get('path', '')

    if not filepath:
        return jsonify({
            'success': False,
            'error': 'No file path provided'
        }), 400

    try:
        file_path = Path(filepath)

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        # Determine MIME type based on file extension
        extension = file_path.suffix.lower()
        mime_type = None

        if extension == '.json':
            mime_type = 'application/json'
        elif extension == '.md':
            mime_type = 'text/plain; charset=utf-8'
        elif extension == '.sh':
            mime_type = 'text/plain; charset=utf-8'
        elif file_path.name == 'Brewfile':
            mime_type = 'text/plain; charset=utf-8'
        else:
            mime_type = 'text/plain; charset=utf-8'

        # Serve the file for viewing (not downloading)
        return send_file(
            str(file_path),
            mimetype=mime_type,
            as_attachment=False
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Helper functions

def organize_items_by_category(profile):
    """Organize all items by category."""
    items_by_category = {}

    # Combine all items
    all_items = []

    for item in profile.homebrew_formulae:
        item_dict = item.to_dict()
        item_dict['item_type'] = 'homebrew_formula'
        all_items.append(item_dict)

    for item in profile.homebrew_casks:
        item_dict = item.to_dict()
        item_dict['item_type'] = 'homebrew_cask'
        all_items.append(item_dict)

    for item in profile.applications:
        item_dict = item.to_dict()
        item_dict['item_type'] = 'application'
        all_items.append(item_dict)

    # Group by category
    for item in all_items:
        category = item.get('category', 'Other')
        if category not in items_by_category:
            items_by_category[category] = []
        items_by_category[category].append(item)

    # Sort categories
    sorted_categories = sorted(items_by_category.keys())
    return {cat: items_by_category[cat] for cat in sorted_categories}


def get_item_list(profile, item_type):
    """Get item list from profile by type."""
    if item_type == 'homebrew_formula':
        return profile.homebrew_formulae
    elif item_type == 'homebrew_cask':
        return profile.homebrew_casks
    elif item_type == 'application':
        return profile.applications
    elif item_type == 'browser_extension':
        return profile.browser_extensions
    return None


def load_most_recent_profile():
    """Load the most recently modified profile."""
    try:
        json_files = list(profiles_dir.glob('*.json'))
        if not json_files:
            return None

        most_recent = max(json_files, key=lambda p: p.stat().st_mtime)
        return ScanProfile.load(str(most_recent))
    except Exception:
        return None


def compute_diff(profile1, profile2):
    """Compute differences between two profiles."""
    diff = {
        'added': [],
        'removed': [],
        'common': []
    }

    # Get all item names from both profiles
    items1 = set()
    items2 = set()

    for item in profile1.homebrew_formulae + profile1.homebrew_casks + profile1.applications:
        items1.add(item.name)

    for item in profile2.homebrew_formulae + profile2.homebrew_casks + profile2.applications:
        items2.add(item.name)

    diff['added'] = sorted(list(items2 - items1))
    diff['removed'] = sorted(list(items1 - items2))
    diff['common'] = sorted(list(items1 & items2))

    return diff


def generate_brewfile(profile, filepath):
    """Generate Brewfile for Homebrew bundle."""
    with open(filepath, 'w') as f:
        # Add formulae
        for item in profile.homebrew_formulae:
            if item.enabled and item.brew_package:
                f.write(f'brew "{item.brew_package}"\n')

        f.write('\n')

        # Add casks
        for item in profile.homebrew_casks:
            if item.enabled and item.brew_package:
                f.write(f'cask "{item.brew_package}"\n')


def generate_install_script(profile, filepath):
    """Generate install.sh script."""
    script = """#!/bin/bash
# MacDitto Install Script
# Generated on {date}
# Machine: {machine}

set -e  # Exit on error

echo "MacDitto Install Script"
echo "======================="
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew already installed"
fi

# Install packages from Brewfile
if [ -f "Brewfile" ]; then
    echo "Installing Homebrew packages..."
    brew bundle install --file=Brewfile
else
    echo "Warning: Brewfile not found"
fi

# Copy shell configs
echo "Copying shell configurations..."
""".format(date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'), machine=profile.machine_name)

    for shell_config in profile.shell_configs:
        script += f'# {shell_config.filename}\n'
        script += f'cp shell_configs/{shell_config.filename} ~/{shell_config.filename}\n'

    # Copy git config
    if profile.git_config:
        script += '\n# Copy Git config\n'
        script += 'cp configs/gitconfig ~/.gitconfig\n'

    # Apply system preferences
    if profile.system_preferences:
        script += '\n# Apply macOS system preferences\n'
        for pref in profile.system_preferences:
            script += f'{pref.command}\n'

    script += '\necho ""\n'
    script += 'echo "Installation complete!"\n'
    script += 'echo "See MANUAL_STEPS.md for remaining manual steps."\n'

    with open(filepath, 'w') as f:
        f.write(script)

    # Make executable
    os.chmod(filepath, 0o755)


def generate_manual_steps(profile, filepath):
    """Generate MANUAL_STEPS.md with human-readable instructions."""
    md = f"""# MacDitto Manual Installation Steps

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Machine: {profile.machine_name}

## Applications Requiring Manual Installation

"""

    # Find manual install items
    manual_items = []
    for item in profile.applications:
        if item.enabled and item.install_method == 'manual':
            manual_items.append(item)

    if manual_items:
        for item in manual_items:
            md += f"### {item.name}\n"
            if item.manual_instructions:
                md += f"{item.manual_instructions}\n"
            if item.url:
                md += f"URL: {item.url}\n"
            md += "\n"
    else:
        md += "No manual installations required.\n\n"

    # Browser extensions
    if profile.browser_extensions:
        md += "## Browser Extensions\n\n"

        extensions_by_browser = {}
        for ext in profile.browser_extensions:
            if ext.enabled:
                if ext.browser not in extensions_by_browser:
                    extensions_by_browser[ext.browser] = []
                extensions_by_browser[ext.browser].append(ext)

        for browser, extensions in extensions_by_browser.items():
            md += f"### {browser}\n\n"
            for ext in extensions:
                md += f"- **{ext.name}** (v{ext.version})\n"
                if ext.store_url:
                    md += f"  - Install from: {ext.store_url}\n"
            md += "\n"

    # Accounts
    if profile.accounts:
        md += "## Accounts & Web Services\n\n"
        for account in profile.accounts:
            md += f"### {account.name}\n"
            if account.url:
                md += f"Login at: {account.url}\n"
            if account.manual_instructions:
                md += f"{account.manual_instructions}\n"
            md += "\n"

    # Configuration notes
    md += """## Additional Setup Steps

1. **SSH Keys**: Generate new SSH keys and add to GitHub/services
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **Browser Sync**: Log into browser accounts to sync bookmarks and settings

3. **Restart Required**: Some applications may require a restart to fully activate

4. **Verify Installation**: Run MacDitto scan on new machine to verify setup
"""

    with open(filepath, 'w') as f:
        f.write(md)


def save_export_history(export_record):
    """Save export record to history file."""
    history = load_export_history()
    history.insert(0, export_record)  # Add to beginning (most recent first)

    # Keep only last 50 exports
    history = history[:50]

    with open(export_history_file, 'w') as f:
        json.dump(history, f, indent=2)


def load_export_history():
    """Load export history from file."""
    if not export_history_file.exists():
        return []

    try:
        with open(export_history_file, 'r') as f:
            return json.load(f)
    except Exception:
        return []


def save_scan_history(scan_record):
    """Save scan record to history file."""
    history = load_scan_history()
    history.insert(0, scan_record)  # Add to beginning (most recent first)

    # Keep only last 50 scans
    history = history[:50]

    with open(scan_history_file, 'w') as f:
        json.dump(history, f, indent=2)


def load_scan_history():
    """Load scan history from file."""
    if not scan_history_file.exists():
        return []

    try:
        with open(scan_history_file, 'r') as f:
            return json.load(f)
    except Exception:
        return []


if __name__ == '__main__':
    # Use port 5001 by default (5000 is often used by macOS AirPlay Receiver)
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=True, port=port)
