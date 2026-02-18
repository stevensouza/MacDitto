"""
Integration tests for full Flask app workflow.
"""

import pytest
import json
import os
from pathlib import Path

from macditto.app import app, current_profile
from macditto.scanner import Scanner
from macditto.models import ScanProfile


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_full_workflow_simulation(client, tmp_path):
    """Test simulated full workflow without actual scanning."""
    import macditto.app as app_module
    original_profile = app_module.current_profile
    original_dirname = app_module.current_scan_dirname
    app_module.current_profile = None
    app_module.current_scan_dirname = None

    # 1. Dashboard should load even without profile
    response = client.get('/')
    assert response.status_code == 200
    assert b'MacDitto' in response.data

    # 2. Check saved scans list
    response = client.get('/saved_scans')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True

    # 3. Try to regenerate without profile (should fail)
    # Note: dashboard GET / may auto-load a scan from disk, so re-clear
    app_module.current_profile = None
    app_module.current_scan_dirname = None
    response = client.post('/regenerate',
                          content_type='application/json')
    assert response.status_code == 400

    app_module.current_profile = original_profile
    app_module.current_scan_dirname = original_dirname


def test_scanner_integration():
    """Test that Scanner integrates properly with Flask app."""
    scanner = Scanner()

    # Scanner should be importable and instantiable
    assert scanner is not None

    # Scanner should have all required methods
    assert hasattr(scanner, 'scan_all')
    assert hasattr(scanner, 'scan_homebrew')
    assert hasattr(scanner, 'scan_applications')
    assert hasattr(scanner, 'scan_dock_items')
    assert hasattr(scanner, 'scan_login_items')
    assert hasattr(scanner, 'scan_shell_configs')
    assert hasattr(scanner, 'scan_git_config')
    assert hasattr(scanner, 'scan_browser_extensions')
    assert hasattr(scanner, 'scan_macos_preferences')


def test_profile_save_load_integration(tmp_path):
    """Test profile save and load functionality."""
    # Create a test profile
    profile = ScanProfile(
        scan_date="2026-02-15T10:00:00",
        machine_name="Test Mac"
    )

    # Save to temp directory
    filepath = tmp_path / "test_profile.json"
    profile.save(str(filepath))

    # Verify file was created
    assert filepath.exists()

    # Load the profile
    loaded_profile = ScanProfile.load(str(filepath))

    # Verify loaded profile matches
    assert loaded_profile.scan_date == profile.scan_date
    assert loaded_profile.machine_name == profile.machine_name


def test_export_file_generation(tmp_path):
    """Test that export generates required files."""
    from macditto.app import generate_brewfile, generate_install_script, generate_manual_steps
    from macditto.models import Item

    # Create test profile with some items
    profile = ScanProfile(
        scan_date="2026-02-15T10:00:00",
        machine_name="Test Mac"
    )

    profile.homebrew_formulae = [
        Item(name="git", install_method="brew", brew_package="git", enabled=True),
        Item(name="python", install_method="brew", brew_package="python", enabled=True),
    ]

    profile.homebrew_casks = [
        Item(name="docker", install_method="cask", brew_package="docker", enabled=True),
    ]

    # Generate Brewfile
    brewfile_path = tmp_path / "Brewfile"
    generate_brewfile(profile, brewfile_path)
    assert brewfile_path.exists()

    # Verify content
    brewfile_content = brewfile_path.read_text()
    assert 'brew "git"' in brewfile_content
    assert 'brew "python"' in brewfile_content
    assert 'cask "docker"' in brewfile_content

    # Generate install script
    install_script_path = tmp_path / "install.sh"
    generate_install_script(profile, install_script_path)
    assert install_script_path.exists()

    # Verify script is executable
    assert os.access(install_script_path, os.X_OK)

    # Verify content
    script_content = install_script_path.read_text()
    assert "#!/bin/bash" in script_content
    assert "MacDitto Install Script" in script_content

    # Generate manual steps
    manual_steps_path = tmp_path / "MANUAL_STEPS.md"
    generate_manual_steps(profile, manual_steps_path)
    assert manual_steps_path.exists()

    # Verify content
    manual_content = manual_steps_path.read_text()
    assert "MacDitto Manual Installation Steps" in manual_content


def test_category_organization():
    """Test that items are properly organized by category."""
    from macditto.app import organize_items_by_category
    from macditto.models import Item

    profile = ScanProfile(
        scan_date="2026-02-15T10:00:00",
        machine_name="Test Mac"
    )

    profile.homebrew_formulae = [
        Item(name="git", install_method="brew", category="Development", brew_package="git"),
        Item(name="python", install_method="brew", category="Development", brew_package="python"),
        Item(name="ffmpeg", install_method="brew", category="Media", brew_package="ffmpeg"),
    ]

    profile.homebrew_casks = [
        Item(name="docker", install_method="cask", category="Development", brew_package="docker"),
        Item(name="brave-browser", install_method="cask", category="Browsers", brew_package="brave-browser"),
    ]

    all_items = organize_items_by_category(profile)

    categories = [item.get('category', 'Other') for item in all_items]
    unique_categories = set(categories)

    # Should have 3 categories
    assert len(unique_categories) == 3

    # Development should have 3 items (2 formulae + 1 cask)
    assert sum(1 for c in categories if c == "Development") == 3

    # Media should have 1 item
    assert sum(1 for c in categories if c == "Media") == 1

    # Browsers should have 1 item
    assert sum(1 for c in categories if c == "Browsers") == 1


def test_diff_computation():
    """Test profile diff computation."""
    from macditto.app import compute_diff
    from macditto.models import Item

    profile1 = ScanProfile(
        scan_date="2026-02-15T10:00:00",
        machine_name="Mac 1"
    )
    profile1.homebrew_formulae = [
        Item(name="git", install_method="brew", brew_package="git"),
        Item(name="python", install_method="brew", brew_package="python"),
        Item(name="node", install_method="brew", brew_package="node"),
    ]

    profile2 = ScanProfile(
        scan_date="2026-02-15T11:00:00",
        machine_name="Mac 2"
    )
    profile2.homebrew_formulae = [
        Item(name="git", install_method="brew", brew_package="git"),
        Item(name="python", install_method="brew", brew_package="python"),
        Item(name="ruby", install_method="brew", brew_package="ruby"),
    ]

    diff = compute_diff(profile1, profile2)

    # node was removed
    assert "node" in diff["removed"]
    assert len(diff["removed"]) == 1

    # ruby was added
    assert "ruby" in diff["added"]
    assert len(diff["added"]) == 1

    # git and python are common
    assert "git" in diff["common"]
    assert "python" in diff["common"]
    assert len(diff["common"]) == 2
