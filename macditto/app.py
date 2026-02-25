"""
Flask web application for MacDitto - Mac Environment Duplication Tool.

Provides web interface for scanning, viewing, and managing Mac configurations.
Every scan auto-saves and auto-generates installation files.
"""

import os
import re
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
current_scan_dirname = None  # Track which scan dir is loaded
scans_dir = Path(__file__).parent.parent / 'scans'
scan_history_file = scans_dir / 'scan_history.json'
machine_notes_path = scans_dir / 'machine_notes.md'

# Global variables for scan tracking
scan_in_progress = False
scan_progress = {
    'current_step': '',
    'step_number': 0,
    'total_steps': 14,
    'percentage': 0,
    'item_counts': {},
    'completed': False,
    'error': None
}
scan_start_time = None

# Ensure directories exist
scans_dir.mkdir(exist_ok=True)


# Disable caching for all responses (especially static files)
@app.after_request
def add_no_cache_headers(response):
    """Add headers to disable browser caching during development."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


def sanitize_machine_name(name):
    """Sanitize machine name for use in directory names."""
    # Remove apostrophes, then replace non-alphanumeric (except hyphens) with underscores
    name = name.replace("'", "").replace("\u2019", "")
    name = re.sub(r'[^a-zA-Z0-9\-]', '_', name)
    # Collapse multiple underscores
    name = re.sub(r'_+', '_', name).strip('_')
    return name


def create_scan_dir(machine_name, timestamp):
    """Create and return scan directory path: scans/scan_{SafeMachineName}_{TIMESTAMP}/"""
    safe_name = sanitize_machine_name(machine_name)
    dirname = f"scan_{safe_name}_{timestamp}"
    scan_dir = scans_dir / dirname
    scan_dir.mkdir(parents=True, exist_ok=True)
    return scan_dir, dirname


def generate_install_files(profile, scan_dir):
    """Generate all installation files in the given scan directory."""
    files = {}

    # Generate Brewfile
    brewfile_path = scan_dir / 'Brewfile'
    generate_brewfile(profile, brewfile_path)
    files['brewfile'] = str(brewfile_path.absolute())

    # Generate install.sh
    install_script_path = scan_dir / 'install.sh'
    generate_install_script(profile, install_script_path)
    files['install_script'] = str(install_script_path.absolute())

    # Generate MANUAL_STEPS.md
    manual_steps_path = scan_dir / 'MANUAL_STEPS.md'
    generate_manual_steps(profile, manual_steps_path)
    files['manual_steps'] = str(manual_steps_path.absolute())

    # Generate SETUP_NOTES.md
    setup_notes_path = scan_dir / 'SETUP_NOTES.md'
    generate_setup_notes(profile, setup_notes_path)
    files['setup_notes'] = str(setup_notes_path.absolute())

    # Generate SOFTWARE_CATALOG.md
    software_catalog_path = scan_dir / 'SOFTWARE_CATALOG.md'
    generate_software_catalog(profile, software_catalog_path)
    files['software_catalog'] = str(software_catalog_path.absolute())

    # Generate DOTFILES.md
    dotfiles_path = scan_dir / 'DOTFILES.md'
    generate_dotfiles(profile, dotfiles_path)
    files['dotfiles'] = str(dotfiles_path.absolute())

    return files


@app.route('/')
def dashboard():
    """
    Main dashboard showing all scanned items organized by category.
    """
    global current_profile

    # Load most recent scan if current_profile is None
    if current_profile is None:
        current_profile = load_most_recent_scan()

    # Load machine-level notes (shared across all scans)
    machine_notes = ''
    if machine_notes_path.exists():
        machine_notes = machine_notes_path.read_text(encoding='utf-8')

    if current_profile is None:
        # No scan exists, show empty dashboard with scan button
        return render_template('dashboard.html',
                             profile=None,
                             all_items=[],
                             category_counts={},
                             scan_files={},
                             machine_notes=machine_notes)

    # Organize items by category (returns flat list sorted by category)
    all_items = organize_items_by_category(current_profile)

    # Calculate counts per category
    category_counts = {}
    for item in all_items:
        cat = item.get('category', 'Other')
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Get installation file paths for the current scan
    scan_files = {}
    if current_scan_dirname:
        scan_dir = scans_dir / current_scan_dirname
        file_map = {
            'brewfile': scan_dir / 'Brewfile',
            'install_script': scan_dir / 'install.sh',
            'manual_steps': scan_dir / 'MANUAL_STEPS.md',
            'setup_notes': scan_dir / 'SETUP_NOTES.md',
            'software_catalog': scan_dir / 'SOFTWARE_CATALOG.md',
            'dotfiles': scan_dir / 'DOTFILES.md',
        }
        for key, path in file_map.items():
            if path.exists():
                scan_files[key] = str(path.absolute())

    # Detect if we're viewing a historical (non-latest) scan
    is_historical = False
    if current_scan_dirname:
        try:
            scan_files_list = list(scans_dir.glob('*/saved_scan.json'))
            if scan_files_list:
                most_recent = max(scan_files_list, key=lambda p: p.stat().st_mtime)
                is_historical = most_recent.parent.name != current_scan_dirname
        except Exception:
            pass

    return render_template('dashboard.html',
                         profile=current_profile,
                         all_items=all_items,
                         category_counts=category_counts,
                         scan_files=scan_files,
                         is_historical=is_historical,
                         machine_notes=machine_notes)


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
        'total_steps': 14,
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
    Auto-saves scan and generates installation files.
    """
    global current_profile, current_scan_dirname, scan_in_progress, scan_progress, scan_start_time

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

        # Scan notes start empty for each new scan.
        # Machine-level notes (scans/machine_notes.md) handle persistent notes.

        # Calculate duration
        duration = time.time() - scan_start_time

        # Auto-save: create scan directory and save everything
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        scan_dir, scan_dirname = create_scan_dir(current_profile.machine_name, timestamp)
        current_scan_dirname = scan_dirname

        # Save scan data (was profile JSON)
        saved_scan_path = scan_dir / 'saved_scan.json'
        current_profile.save(str(saved_scan_path))

        # Generate all installation files
        files = generate_install_files(current_profile, scan_dir)

        # Mark as completed
        scan_progress['completed'] = True
        scan_progress['percentage'] = 100

        # Save to scan history
        scan_record = {
            'timestamp': timestamp,
            'scan_date': current_profile.scan_date,
            'end_date': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'machine_name': current_profile.machine_name,
            'item_counts': scan_progress['item_counts'].copy(),
            'status': 'completed',
            'scan_dir': str(scan_dir.absolute()),
            'scan_dirname': scan_dirname,
            'files': files
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


@app.route('/saved_scans')
def saved_scans():
    """
    Get saved scans list.
    Returns completed scans that still have existing directories.
    """
    try:
        history = load_scan_history()
        # Filter to completed scans with existing directories
        valid_scans = []
        for scan in history:
            if scan.get('status') == 'completed' and scan.get('scan_dir'):
                scan_dir = Path(scan['scan_dir'])
                if scan_dir.exists():
                    valid_scans.append(scan)
        return jsonify({
            'success': True,
            'scans': valid_scans
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/load_scan/<scan_dirname>')
def load_scan(scan_dirname):
    """
    Load a saved scan by directory name.
    """
    global current_profile, current_scan_dirname

    try:
        scan_path = scans_dir / scan_dirname / 'saved_scan.json'
        if not scan_path.exists():
            return jsonify({
                'success': False,
                'error': f'Saved scan not found: {scan_dirname}'
            }), 404

        current_profile = ScanProfile.load(str(scan_path))
        current_scan_dirname = scan_dirname

        return redirect(url_for('dashboard'))
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/regenerate', methods=['POST'])
def regenerate():
    """
    Regenerate installation files for the current scan after user toggles items.
    Re-saves saved_scan.json and regenerates all 5 installation files.
    """
    global current_profile, current_scan_dirname

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No scan loaded. Please run a scan first.'
        }), 400

    if current_scan_dirname is None:
        return jsonify({
            'success': False,
            'error': 'No saved scan directory associated. Please run a new scan.'
        }), 400

    try:
        scan_dir = scans_dir / current_scan_dirname
        if not scan_dir.exists():
            return jsonify({
                'success': False,
                'error': 'Scan directory not found. Please run a new scan.'
            }), 404

        # Re-save scan data
        saved_scan_path = scan_dir / 'saved_scan.json'
        current_profile.save(str(saved_scan_path))

        # Regenerate all installation files
        files = generate_install_files(current_profile, scan_dir)

        return jsonify({
            'success': True,
            'message': 'Installation files regenerated!',
            'files': files
        })
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


@app.route('/save_notes', methods=['POST'])
def save_notes():
    """
    Save setup notes to the current profile.
    Accepts JSON: {"notes": "markdown text..."}
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': False,
            'error': 'No profile loaded'
        }), 400

    try:
        data = request.get_json()
        current_profile.setup_notes = data.get('notes', '')

        # Persist to disk so notes survive app restarts and new scans
        if current_scan_dirname:
            saved_scan_path = scans_dir / current_scan_dirname / 'saved_scan.json'
            current_profile.save(str(saved_scan_path))

        return jsonify({
            'success': True,
            'message': 'Notes saved successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/get_notes')
def get_notes():
    """
    Get current setup notes.
    """
    global current_profile

    if current_profile is None:
        return jsonify({
            'success': True,
            'notes': ''
        })

    return jsonify({
        'success': True,
        'notes': current_profile.setup_notes
    })


@app.route('/save_machine_notes', methods=['POST'])
def save_machine_notes():
    """Save machine-level notes that persist across all scans."""
    try:
        data = request.get_json()
        notes = data.get('notes', '')
        machine_notes_path.write_text(notes, encoding='utf-8')
        return jsonify({'success': True, 'message': 'Machine notes saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get_machine_notes')
def get_machine_notes():
    """Get machine-level notes."""
    notes = ''
    if machine_notes_path.exists():
        notes = machine_notes_path.read_text(encoding='utf-8')
    return jsonify({'success': True, 'notes': notes})


@app.route('/diff/<scan_dir1>/<scan_dir2>')
def diff_scans(scan_dir1, scan_dir2):
    """
    Show differences between two saved scans.
    """
    try:
        path1 = scans_dir / scan_dir1 / 'saved_scan.json'
        path2 = scans_dir / scan_dir2 / 'saved_scan.json'

        if not path1.exists() or not path2.exists():
            return jsonify({
                'success': False,
                'error': 'One or both saved scans not found'
            }), 404

        p1 = ScanProfile.load(str(path1))
        p2 = ScanProfile.load(str(path2))

        diff = compute_diff(p1, p2)

        return render_template('diff.html',
                             profile1=scan_dir1,
                             profile2=scan_dir2,
                             p1=p1,
                             p2=p2,
                             diff=diff)
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
            'error': 'No scan loaded. Please run a scan first.'
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
    """Organize all items by category, returning a flat list sorted by category."""
    all_items = []

    for idx, item in enumerate(profile.homebrew_formulae):
        item_dict = item.to_dict()
        item_dict['item_type'] = 'homebrew_formula'
        item_dict['original_index'] = idx
        all_items.append(item_dict)

    for idx, item in enumerate(profile.homebrew_casks):
        item_dict = item.to_dict()
        item_dict['item_type'] = 'homebrew_cask'
        item_dict['original_index'] = idx
        all_items.append(item_dict)

    for idx, item in enumerate(profile.applications):
        item_dict = item.to_dict()
        item_dict['item_type'] = 'application'
        item_dict['original_index'] = idx
        all_items.append(item_dict)

    # Sort by category, then by name within each category
    all_items.sort(key=lambda x: (x.get('category', 'Other'), x.get('name', '').lower()))

    return all_items


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


def load_most_recent_scan():
    """Load the most recently saved scan."""
    global current_scan_dirname
    try:
        scan_files = list(scans_dir.glob('*/saved_scan.json'))
        if not scan_files:
            return None

        most_recent = max(scan_files, key=lambda p: p.stat().st_mtime)
        current_scan_dirname = most_recent.parent.name
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

    # Restore SSH config
    if profile.ssh_config:
        script += '\n# Restore SSH config\n'
        script += 'echo "Restoring SSH configuration..."\n'
        script += 'mkdir -p ~/.ssh\n'
        script += 'chmod 700 ~/.ssh\n'
        script += 'if [ -f ssh_config ]; then\n'
        script += '    cp ssh_config ~/.ssh/config\n'
        script += '    chmod 600 ~/.ssh/config\n'
        script += 'fi\n'

    if profile.ssh_key_names:
        script += '\n# SSH keys reminder\n'
        script += 'echo "NOTE: The following SSH keys were found on the source machine:"\n'
        for key_name in profile.ssh_key_names:
            script += f'echo "  - {key_name}"\n'
        script += 'echo "You will need to regenerate or securely transfer these keys."\n'

    # Restore crontab
    if profile.crontab:
        script += '\n# Restore crontab\n'
        script += 'echo "Restoring crontab..."\n'
        script += 'if [ -f crontab.txt ]; then\n'
        script += '    crontab crontab.txt\n'
        script += '    echo "Crontab restored"\n'
        script += 'fi\n'

    # Apply system preferences
    if profile.system_preferences:
        script += '\n# Apply macOS system preferences\n'
        for pref in profile.system_preferences:
            script += f'{pref.command}\n'

    # Restore deep tool configurations
    deep_items = _get_deep_config_items(profile)
    if deep_items:
        script += '\n# Restore tool configurations\n'
        script += 'echo "Restoring tool configurations..."\n'
        for item in deep_items:
            dc = item.metadata["deep_config"]
            tool = dc["tool"]
            script += f'\n# {tool.capitalize()} configuration\n'
            script += f'if command -v {tool} &> /dev/null; then\n'
            script += f'    echo "Restoring {tool} configuration..."\n'
            for cmd in dc.get("restore_commands", []):
                script += f'    {cmd}\n'
            script += 'fi\n'

    script += '\necho ""\n'
    script += 'echo "Installation complete!"\n'
    script += 'echo "See MANUAL_STEPS.md for remaining manual steps."\n'

    with open(filepath, 'w') as f:
        f.write(script)

    # Make executable
    os.chmod(filepath, 0o755)


def _get_deep_config_items(profile):
    """Collect all enabled items with deep_config metadata."""
    results = []
    for item_list in [profile.homebrew_formulae, profile.homebrew_casks, profile.applications]:
        for item in item_list:
            if item.enabled and item.metadata.get("deep_config"):
                results.append(item)
    return results


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

    # Tool configuration restoration
    deep_items = _get_deep_config_items(profile)
    if deep_items:
        md += "## Tool Configuration Restoration\n\n"
        md += "The following tools have internal configurations that will be restored by `install.sh`.\n\n"
        for item in deep_items:
            dc = item.metadata["deep_config"]
            md += f"### {item.name}\n"
            md += f"{dc.get('restore_note', '')}\n\n"
            for di in dc.get("items", []):
                name = di.get("name", "")
                size = di.get("size", "")
                item_type = di.get("type", "")
                label = f"{item_type}: " if item_type else ""
                size_label = f" ({size})" if size else ""
                md += f"- {label}{name}{size_label}\n"
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


def generate_setup_notes(profile, filepath):
    """Generate SETUP_NOTES.md from machine notes and per-scan notes."""
    md = f"""# Setup Notes

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Machine: {profile.machine_name}

---

"""
    # Machine-level notes (persistent across all scans)
    machine_notes = ''
    if machine_notes_path.exists():
        machine_notes = machine_notes_path.read_text(encoding='utf-8').strip()

    if machine_notes:
        md += "## Machine Notes\n\n"
        md += machine_notes + "\n\n"

    # Per-scan notes
    if profile.setup_notes:
        md += "## Scan Notes\n\n"
        md += profile.setup_notes + "\n"

    if not machine_notes and not profile.setup_notes:
        md += "_No setup notes have been added yet. Use the MacDitto web interface to add notes about your setup._\n"

    with open(filepath, 'w') as f:
        f.write(md)


def generate_dotfiles(profile, filepath):
    """Generate DOTFILES.md concatenating shell configs, git config, SSH, crontab, and macOS defaults."""
    md = f"""# Dotfiles

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Machine: {profile.machine_name}

"""

    # Shell configs
    for cfg in profile.shell_configs:
        md += f"## {cfg.filename}\n\n"
        md += f"```bash\n{cfg.content}\n```\n\n"

    # Git config
    if profile.git_config:
        md += "## .gitconfig\n\n"
        md += f"```ini\n{profile.git_config}\n```\n\n"

    # SSH config
    if profile.ssh_config:
        md += "## .ssh/config\n\n"
        md += f"```\n{profile.ssh_config}\n```\n\n"

    # SSH key names
    if profile.ssh_key_names:
        md += "## SSH Keys\n\n"
        md += "Key files found (names only — private key contents are never exported):\n\n"
        for key_name in profile.ssh_key_names:
            md += f"- `{key_name}`\n"
        md += "\n"

    # Crontab
    if profile.crontab:
        md += "## Crontab\n\n"
        md += f"```\n{profile.crontab}\n```\n\n"

    # macOS defaults
    if profile.system_preferences:
        md += "## macOS Defaults\n\n"
        md += "| Domain | Key | Value | Description |\n"
        md += "|--------|-----|-------|-------------|\n"
        for pref in profile.system_preferences:
            desc = pref.description or ''
            md += f"| `{pref.domain}` | `{pref.key}` | `{pref.value}` | {desc} |\n"
        md += "\n### Restore Commands\n\n"
        md += "```bash\n"
        for pref in profile.system_preferences:
            if pref.command:
                md += f"{pref.command}\n"
        md += "```\n"

    with open(filepath, 'w') as f:
        f.write(md)


def generate_software_catalog(profile, filepath):
    """Generate SOFTWARE_CATALOG.md with organized software descriptions."""
    md = f"""# Software Catalog

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Machine: {profile.machine_name}

"""

    # Homebrew Formulae
    if profile.homebrew_formulae:
        md += "## Homebrew Formulae\n\n"
        by_category = {}
        for item in profile.homebrew_formulae:
            if item.enabled:
                cat = item.category or 'Other'
                by_category.setdefault(cat, []).append(item)

        for category in sorted(by_category.keys()):
            md += f"### {category}\n\n"
            for item in sorted(by_category[category], key=lambda x: x.name):
                desc = item.metadata.get('description', '')
                if desc:
                    md += f"- **{item.name}** - {desc}\n"
                else:
                    md += f"- **{item.name}**\n"
            md += "\n"

    # Homebrew Casks
    if profile.homebrew_casks:
        md += "## Homebrew Casks\n\n"
        by_category = {}
        for item in profile.homebrew_casks:
            if item.enabled:
                cat = item.category or 'Other'
                by_category.setdefault(cat, []).append(item)

        for category in sorted(by_category.keys()):
            md += f"### {category}\n\n"
            for item in sorted(by_category[category], key=lambda x: x.name):
                desc = item.metadata.get('description', '')
                if desc:
                    md += f"- **{item.name}** - {desc}\n"
                else:
                    md += f"- **{item.name}**\n"
            md += "\n"

    # Manual Installations
    manual_apps = [item for item in profile.applications if item.enabled]
    if manual_apps:
        md += "## Applications\n\n"
        by_category = {}
        for item in manual_apps:
            cat = item.category or 'Other'
            by_category.setdefault(cat, []).append(item)

        for category in sorted(by_category.keys()):
            md += f"### {category}\n\n"
            for item in sorted(by_category[category], key=lambda x: x.name):
                desc = item.metadata.get('description', '')
                method = item.install_method
                if desc:
                    md += f"- **{item.name}** ({method}) - {desc}\n"
                else:
                    md += f"- **{item.name}** ({method})\n"
            md += "\n"

    # Deep configuration details
    deep_items = _get_deep_config_items(profile)
    if deep_items:
        md += "## Tool Configurations\n\n"
        for item in deep_items:
            dc = item.metadata["deep_config"]
            md += f"### {item.name}\n\n"
            for di in dc.get("items", []):
                name = di.get("name", "")
                size = di.get("size", "")
                item_type = di.get("type", "")
                label = f"{item_type}: " if item_type else ""
                size_label = f" ({size})" if size else ""
                md += f"- {label}{name}{size_label}\n"
            md += "\n"

    with open(filepath, 'w') as f:
        f.write(md)


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


def migrate_legacy_data():
    """Migrate existing profiles/ and output/ data to scans/ directory."""
    project_root = Path(__file__).parent.parent
    profiles_dir = project_root / 'profiles'
    output_dir = project_root / 'output'

    # Migrate profiles
    if profiles_dir.exists():
        for json_file in profiles_dir.glob('*.json'):
            try:
                profile = ScanProfile.load(str(json_file))
                # Create a scan dir from profile info
                timestamp = json_file.stem.split('_')[-2] + '_' + json_file.stem.split('_')[-1] if '_' in json_file.stem else datetime.fromtimestamp(json_file.stat().st_mtime).strftime('%Y%m%d_%H%M%S')
                machine_name = profile.machine_name or 'Unknown'
                scan_dir, scan_dirname = create_scan_dir(machine_name, timestamp)

                # Save as saved_scan.json
                saved_scan_path = scan_dir / 'saved_scan.json'
                if not saved_scan_path.exists():
                    profile.save(str(saved_scan_path))
                    # Generate install files
                    generate_install_files(profile, scan_dir)
            except Exception:
                continue  # Skip files that can't be loaded


if __name__ == '__main__':
    # Use port 5001 by default (5000 is often used by macOS AirPlay Receiver)
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=True, port=port)
