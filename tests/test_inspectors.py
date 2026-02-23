"""
Tests for MacDitto deep configuration inspectors.
"""

import pytest
from unittest.mock import patch

from macditto.inspectors import (
    inspect_ollama,
    inspect_docker,
    INSPECTOR_REGISTRY,
    TOOL_MATCH_NAMES,
)


class TestInspectorRegistry:
    """Tests for the inspector registry."""

    def test_ollama_registered(self):
        assert "ollama" in INSPECTOR_REGISTRY

    def test_docker_registered(self):
        assert "docker" in INSPECTOR_REGISTRY

    def test_match_names_defined(self):
        assert "ollama" in TOOL_MATCH_NAMES
        assert "docker" in TOOL_MATCH_NAMES
        assert "docker desktop" in TOOL_MATCH_NAMES["docker"]


class TestOllamaInspector:
    """Tests for the Ollama inspector."""

    @patch("macditto.inspectors.run_command")
    def test_ollama_not_installed(self, mock_run):
        mock_run.return_value = (False, "", "command not found: ollama")
        result = inspect_ollama()
        assert result is None

    @patch("macditto.inspectors.run_command")
    def test_ollama_no_models(self, mock_run):
        mock_run.return_value = (True, "NAME    ID    SIZE    MODIFIED\n", "")
        result = inspect_ollama()
        assert result is None

    @patch("macditto.inspectors.run_command")
    def test_ollama_empty_output(self, mock_run):
        mock_run.return_value = (True, "", "")
        result = inspect_ollama()
        assert result is None

    @patch("macditto.inspectors.run_command")
    def test_ollama_with_models(self, mock_run):
        output = (
            "NAME                ID            SIZE    MODIFIED\n"
            "llama3.2:latest     abcdef123456  2.0 GB  3 days ago\n"
            "codellama:7b        789def456abc  3.8 GB  1 week ago\n"
        )
        mock_run.return_value = (True, output, "")
        result = inspect_ollama()

        assert result is not None
        assert result["tool"] == "ollama"
        assert len(result["items"]) == 2
        assert result["items"][0]["name"] == "llama3.2:latest"
        assert result["items"][0]["size"] == "2.0 GB"
        assert result["items"][1]["name"] == "codellama:7b"
        assert len(result["restore_commands"]) == 2
        assert result["restore_commands"][0] == "ollama pull llama3.2:latest"
        assert result["restore_commands"][1] == "ollama pull codellama:7b"
        assert "restore_note" in result

    @patch("macditto.inspectors.run_command")
    def test_ollama_single_model(self, mock_run):
        output = (
            "NAME             ID            SIZE    MODIFIED\n"
            "mistral:latest   abc123456789  4.1 GB  2 hours ago\n"
        )
        mock_run.return_value = (True, output, "")
        result = inspect_ollama()

        assert result is not None
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "mistral:latest"


class TestDockerInspector:
    """Tests for the Docker inspector."""

    @patch("macditto.inspectors.run_command")
    def test_docker_not_installed(self, mock_run):
        mock_run.return_value = (False, "", "command not found: docker")
        result = inspect_docker()
        assert result is None

    @patch("macditto.inspectors.run_command")
    def test_docker_daemon_not_running(self, mock_run):
        mock_run.return_value = (False, "", "Cannot connect to the Docker daemon")
        result = inspect_docker()
        assert result is None

    @patch("macditto.inspectors.run_command")
    def test_docker_no_images_or_containers(self, mock_run):
        # First call: docker info succeeds
        # Second call: docker images returns empty
        # Third call: docker ps returns empty
        mock_run.side_effect = [
            (True, "Docker info output", ""),
            (True, "", ""),
            (True, "", ""),
        ]
        result = inspect_docker()
        assert result is None

    @patch("macditto.inspectors.run_command")
    def test_docker_with_images(self, mock_run):
        mock_run.side_effect = [
            (True, "Docker info", ""),  # docker info
            (True, "postgres:15\t300MB\nredis:latest\t120MB\n", ""),  # docker images
            (True, "", ""),  # docker ps -a
        ]
        result = inspect_docker()

        assert result is not None
        assert result["tool"] == "docker"
        assert len(result["items"]) == 2
        assert result["items"][0]["type"] == "image"
        assert result["items"][0]["name"] == "postgres:15"
        assert result["items"][0]["size"] == "300MB"
        assert len(result["restore_commands"]) == 2
        assert result["restore_commands"][0] == "docker pull postgres:15"

    @patch("macditto.inspectors.run_command")
    def test_docker_with_containers(self, mock_run):
        mock_run.side_effect = [
            (True, "Docker info", ""),  # docker info
            (True, "", ""),  # docker images
            (True, "mydb\tpostgres:15\tUp 2 hours\n", ""),  # docker ps -a
        ]
        result = inspect_docker()

        assert result is not None
        assert len(result["items"]) == 1
        assert result["items"][0]["type"] == "container"
        assert result["items"][0]["name"] == "mydb"
        assert result["items"][0]["image"] == "postgres:15"
        assert result["items"][0]["status"] == "Up 2 hours"
        # Containers don't generate restore commands
        assert len(result["restore_commands"]) == 0

    @patch("macditto.inspectors.run_command")
    def test_docker_filters_none_images(self, mock_run):
        mock_run.side_effect = [
            (True, "Docker info", ""),
            (True, "postgres:15\t300MB\n<none>:<none>\t50MB\n", ""),
            (True, "", ""),
        ]
        result = inspect_docker()

        assert result is not None
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "postgres:15"

    @patch("macditto.inspectors.run_command")
    def test_docker_with_images_and_containers(self, mock_run):
        mock_run.side_effect = [
            (True, "Docker info", ""),
            (True, "postgres:15\t300MB\n", ""),
            (True, "mydb\tpostgres:15\tUp 2 hours\n", ""),
        ]
        result = inspect_docker()

        assert result is not None
        assert len(result["items"]) == 2
        assert result["items"][0]["type"] == "image"
        assert result["items"][1]["type"] == "container"
        assert "restore_note" in result
