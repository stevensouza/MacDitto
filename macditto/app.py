"""
Flask web application for MacDitto - Mac Environment Duplication Tool.

Provides web interface for scanning, viewing, saving, and managing Mac configurations.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for

from .scanner import Scanner
from .models import ScanProfile


app = Flask(__name__)
app.config['SECRET_KEY'] = 'macditto-dev-secret-key-change-in-production'

# Global variables for current scan profile
current_profile = None
profiles_dir = Path(__file__).parent.parent / 'profiles'
output_dir = Path(__file__).parent.parent / 'output'

# Ensure directories exist
profiles_dir.mkdir(exist_ok=True)
output_dir.mkdir(exist_ok=True)


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
    Returns JSON with scan results.
    """
    global current_profile

    try:
        scanner = Scanner()
        current_profile = scanner.scan_all()

        # Organize items for response
        items_by_category = organize_items_by_category(current_profile)
        category_counts = {category: len(items) for category, items in items_by_category.items()}

        return jsonify({
            'success': True,
            'message': 'Scan completed successfully',
            'scan_date': current_profile.scan_date,
            'machine_name': current_profile.machine_name,
            'category_counts': category_counts
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
            'message': f'Profile saved as {filename}',
            'filename': filename
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

        return jsonify({
            'success': True,
            'message': f'Export generated in output/export_{timestamp}/',
            'export_dir': str(export_dir)
        })
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)
