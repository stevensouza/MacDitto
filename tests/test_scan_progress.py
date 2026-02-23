"""
Tests for scan progress tracking and history features.
"""

import pytest
import json
import time
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from macditto.scanner import Scanner
from macditto.models import ScanProfile


class TestScannerProgressCallback:
    """Test Scanner progress callback functionality."""

    def test_scanner_accepts_progress_callback(self):
        """Test that Scanner accepts progress_callback parameter."""
        callback = MagicMock()
        scanner = Scanner(progress_callback=callback)
        assert scanner.progress_callback == callback

    def test_scanner_without_progress_callback(self):
        """Test that Scanner works without progress_callback."""
        scanner = Scanner()
        assert scanner.progress_callback is None

    def test_progress_callback_invoked_during_scan(self, tmp_path):
        """Test that progress callback is invoked during scan_all()."""
        callback = MagicMock()
        scanner = Scanner(progress_callback=callback)

        # Mock all scan methods to return empty results quickly
        with patch.object(scanner, 'scan_homebrew', return_value=([], [])), \
             patch.object(scanner, 'scan_applications', return_value=[]), \
             patch.object(scanner, 'scan_dock_items', return_value=[]), \
             patch.object(scanner, 'scan_login_items', return_value=[]), \
             patch.object(scanner, 'scan_shell_configs', return_value=[]), \
             patch.object(scanner, 'scan_git_config', return_value=None), \
             patch.object(scanner, 'scan_browser_extensions', return_value=[]), \
             patch.object(scanner, 'scan_browser_bookmarks', return_value={}), \
             patch.object(scanner, 'scan_macos_preferences', return_value=[]), \
             patch.object(scanner, 'scan_deep_configs', return_value=0):

            profile = scanner.scan_all()

            # Callback should be invoked 12 times (one for each step)
            assert callback.call_count == 12

            # Verify callback was called with correct parameters
            first_call = callback.call_args_list[0]
            step_name, step_number, total_steps, item_counts = first_call[0]

            assert isinstance(step_name, str)
            assert step_number == 1
            assert total_steps == 12
            assert isinstance(item_counts, dict)

    def test_progress_callback_includes_item_counts(self):
        """Test that progress callback includes accumulated item counts."""
        callback = MagicMock()
        scanner = Scanner(progress_callback=callback)

        # Mock scan methods to return specific counts
        with patch.object(scanner, 'scan_homebrew', return_value=([MagicMock()], [MagicMock(), MagicMock()])), \
             patch.object(scanner, 'scan_applications', return_value=[MagicMock()]), \
             patch.object(scanner, 'scan_dock_items', return_value=[]), \
             patch.object(scanner, 'scan_login_items', return_value=[]), \
             patch.object(scanner, 'scan_shell_configs', return_value=[]), \
             patch.object(scanner, 'scan_git_config', return_value=None), \
             patch.object(scanner, 'scan_browser_extensions', return_value=[]), \
             patch.object(scanner, 'scan_browser_bookmarks', return_value={}), \
             patch.object(scanner, 'scan_macos_preferences', return_value=[]), \
             patch.object(scanner, 'scan_deep_configs', return_value=0):

            profile = scanner.scan_all()

            # Check first callback (after Homebrew scan)
            first_call = callback.call_args_list[0]
            item_counts = first_call[0][3]
            assert item_counts['homebrew_formulae'] == 1
            assert item_counts['homebrew_casks'] == 2

            # Check second callback (after applications scan)
            second_call = callback.call_args_list[1]
            item_counts = second_call[0][3]
            assert item_counts['homebrew_formulae'] == 1
            assert item_counts['homebrew_casks'] == 2
            assert item_counts['applications'] == 1


class TestFlaskScanProgress:
    """Test Flask app scan progress endpoints."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from macditto.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    def test_scan_endpoint_starts_background_scan(self, client):
        """Test that /scan endpoint starts scan in background."""
        with patch('macditto.app.threading.Thread') as mock_thread:
            response = client.post('/scan')
            data = json.loads(response.data)

            assert response.status_code == 200
            assert data['success'] is True
            assert data['message'] == 'Scan started'
            mock_thread.assert_called_once()

    def test_scan_endpoint_prevents_concurrent_scans(self, client):
        """Test that /scan returns 409 if scan already in progress."""
        import macditto.app as app_module

        # Set scan_in_progress flag
        original_value = app_module.scan_in_progress
        app_module.scan_in_progress = True

        try:
            response = client.post('/scan')
            data = json.loads(response.data)

            assert response.status_code == 409
            assert data['success'] is False
            assert 'already in progress' in data['error'].lower()
        finally:
            # Restore original value
            app_module.scan_in_progress = original_value

    def test_scan_progress_endpoint_returns_sse(self, client):
        """Test that /scan_progress endpoint returns SSE stream."""
        import macditto.app as app_module

        # Set up test progress state
        original_progress = app_module.scan_progress.copy()
        app_module.scan_progress = {
            'current_step': 'Test step',
            'step_number': 5,
            'total_steps': 12,
            'percentage': 50,
            'item_counts': {'test': 123},
            'completed': True,
            'error': None
        }

        try:
            response = client.get('/scan_progress')

            assert response.status_code == 200
            assert response.content_type == 'text/event-stream; charset=utf-8'
        finally:
            # Restore original progress
            app_module.scan_progress = original_progress


class TestScanHistory:
    """Test scan history storage and retrieval."""

    @pytest.fixture
    def client(self):
        """Create Flask test client."""
        from macditto.app import app
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def temp_history_file(self, tmp_path, monkeypatch):
        """Create temporary scan history file."""
        import macditto.app as app_module
        history_file = tmp_path / 'scan_history.json'
        monkeypatch.setattr(app_module, 'scan_history_file', history_file)
        return history_file

    def test_save_scan_history(self, temp_history_file):
        """Test saving scan record to history."""
        from macditto.app import save_scan_history, load_scan_history

        scan_record = {
            'timestamp': '20260215_143025',
            'scan_date': '2026-02-15T14:30:25.123456',
            'end_date': '2026-02-15T14:30:37.654321',
            'duration_seconds': 12.53,
            'machine_name': "Steve's MacBook Pro",
            'item_counts': {
                'homebrew_formulae': 45,
                'homebrew_casks': 32,
                'applications': 78
            },
            'status': 'completed'
        }

        save_scan_history(scan_record)

        # Verify file was created and contains record
        assert temp_history_file.exists()
        history = load_scan_history()
        assert len(history) == 1
        assert history[0]['timestamp'] == '20260215_143025'
        assert history[0]['status'] == 'completed'

    def test_load_scan_history_empty(self, temp_history_file):
        """Test loading scan history when file doesn't exist."""
        from macditto.app import load_scan_history

        history = load_scan_history()
        assert history == []

    def test_save_scan_history_keeps_last_50(self, temp_history_file):
        """Test that scan history keeps only last 50 records."""
        from macditto.app import save_scan_history, load_scan_history

        # Add 55 scan records
        for i in range(55):
            scan_record = {
                'timestamp': f'20260215_{i:06d}',
                'scan_date': f'2026-02-15T12:{i:02d}:00',
                'end_date': f'2026-02-15T12:{i:02d}:10',
                'duration_seconds': 10.0,
                'machine_name': 'Test Machine',
                'item_counts': {},
                'status': 'completed'
            }
            save_scan_history(scan_record)

        # Should only have 50 records
        history = load_scan_history()
        assert len(history) == 50

        # Most recent should be first (index 54)
        assert history[0]['timestamp'] == '20260215_000054'

    def test_scan_history_endpoint(self, client, temp_history_file):
        """Test /scan_history endpoint."""
        from macditto.app import save_scan_history

        # Add test records
        for i in range(3):
            scan_record = {
                'timestamp': f'2026021{i}_120000',
                'scan_date': f'2026-02-1{i}T12:00:00',
                'end_date': f'2026-02-1{i}T12:00:10',
                'duration_seconds': 10.0,
                'machine_name': 'Test Machine',
                'item_counts': {'test': i},
                'status': 'completed'
            }
            save_scan_history(scan_record)

        response = client.get('/scan_history')
        data = json.loads(response.data)

        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['scans']) == 3
        assert data['scans'][0]['timestamp'] == '20260212_120000'  # Most recent first

    def test_scan_record_includes_all_fields(self, temp_history_file):
        """Test that scan record includes all required fields."""
        from macditto.app import save_scan_history, load_scan_history

        scan_record = {
            'timestamp': '20260215_143025',
            'scan_date': '2026-02-15T14:30:25.123456',
            'end_date': '2026-02-15T14:30:37.654321',
            'duration_seconds': 12.53,
            'machine_name': "Steve's MacBook Pro",
            'item_counts': {
                'homebrew_formulae': 45,
                'homebrew_casks': 32,
                'applications': 78,
                'browser_extensions': 12,
                'system_preferences': 8
            },
            'status': 'completed'
        }

        save_scan_history(scan_record)
        history = load_scan_history()

        record = history[0]
        assert 'timestamp' in record
        assert 'scan_date' in record
        assert 'end_date' in record
        assert 'duration_seconds' in record
        assert 'machine_name' in record
        assert 'item_counts' in record
        assert 'status' in record

    def test_failed_scan_saved_to_history(self, temp_history_file):
        """Test that failed scans are saved to history."""
        from macditto.app import save_scan_history, load_scan_history

        failed_scan_record = {
            'timestamp': '20260215_143025',
            'scan_date': '2026-02-15T14:30:25.123456',
            'end_date': '2026-02-15T14:30:37.654321',
            'duration_seconds': 5.0,
            'machine_name': 'Unknown',
            'item_counts': {},
            'status': 'failed',
            'error': 'Permission denied'
        }

        save_scan_history(failed_scan_record)
        history = load_scan_history()

        assert len(history) == 1
        assert history[0]['status'] == 'failed'
        assert 'error' in history[0]
