"""
Tests for Flask web application.
"""

import pytest
import json
import os
from pathlib import Path

from macditto.app import app, organize_items_by_category, compute_diff
from macditto.models import ScanProfile, Item


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_profile():
    """Create sample scan profile for testing."""
    profile = ScanProfile(
        scan_date="2026-02-15T10:00:00",
        machine_name="Test Mac"
    )

    profile.homebrew_formulae = [
        Item(name="git", install_method="brew", category="Development", brew_package="git"),
        Item(name="python", install_method="brew", category="Development", brew_package="python"),
    ]

    profile.homebrew_casks = [
        Item(name="brave-browser", install_method="cask", category="Browsers", brew_package="brave-browser"),
        Item(name="docker", install_method="cask", category="Development", brew_package="docker"),
    ]

    profile.applications = [
        Item(name="IntelliJ IDEA", install_method="manual", category="Development"),
    ]

    return profile


def test_app_exists():
    """Test that Flask app is created."""
    assert app is not None


def test_index_route(client):
    """Test dashboard route loads."""
    response = client.get('/')
    assert response.status_code == 200


def test_saved_scans_route(client):
    """Test saved scans list route."""
    response = client.get('/saved_scans')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'scans' in data


def test_organize_items_by_category(sample_profile):
    """Test organizing items by category."""
    all_items = organize_items_by_category(sample_profile)

    categories = [item.get('category', 'Other') for item in all_items]
    assert "Development" in categories
    assert "Browsers" in categories

    # Development should have 4 items (2 formulae + 1 cask + 1 app)
    assert sum(1 for c in categories if c == "Development") == 4

    # Browsers should have 1 item
    assert sum(1 for c in categories if c == "Browsers") == 1


def test_compute_diff():
    """Test profile diff computation."""
    profile1 = ScanProfile(
        scan_date="2026-02-15T10:00:00",
        machine_name="Mac 1"
    )
    profile1.homebrew_formulae = [
        Item(name="git", install_method="brew", brew_package="git"),
        Item(name="python", install_method="brew", brew_package="python"),
    ]

    profile2 = ScanProfile(
        scan_date="2026-02-15T11:00:00",
        machine_name="Mac 2"
    )
    profile2.homebrew_formulae = [
        Item(name="git", install_method="brew", brew_package="git"),
        Item(name="node", install_method="brew", brew_package="node"),
    ]

    diff = compute_diff(profile1, profile2)

    assert "python" in diff["removed"]
    assert "node" in diff["added"]
    assert "git" in diff["common"]


def test_toggle_item_endpoint(client):
    """Test toggle item endpoint without profile."""
    import macditto.app as app_module
    original = app_module.current_profile
    app_module.current_profile = None

    response = client.post('/toggle_item',
                          data=json.dumps({
                              "item_type": "homebrew_formula",
                              "index": 0,
                              "enabled": True
                          }),
                          content_type='application/json')

    # Should fail because no profile is loaded
    assert response.status_code == 400

    data = json.loads(response.data)
    assert data['success'] is False

    app_module.current_profile = original


def test_load_scan_nonexistent(client):
    """Test loading a saved scan that doesn't exist."""
    response = client.get('/load_scan/nonexistent_scan_dir')

    data = json.loads(response.data)
    assert data['success'] is False
    assert response.status_code == 404


def test_regenerate_no_profile(client):
    """Test regenerate endpoint without profile."""
    import macditto.app as app_module
    # Ensure no profile loaded
    original = app_module.current_profile
    app_module.current_profile = None

    response = client.post('/regenerate',
                          content_type='application/json')

    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False

    # Restore
    app_module.current_profile = original


def test_scan_history_route(client):
    """Test scan history route."""
    response = client.get('/scan_history')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'success' in data
    assert 'scans' in data
