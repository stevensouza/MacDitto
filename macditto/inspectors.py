"""
Deep configuration inspectors for MacDitto.

Each inspector probes a tool's internal state (models, images, extensions, etc.)
and returns structured data for display and restoration on a new machine.

To add a new inspector, simply define a function decorated with @register_inspector:

    @register_inspector("mytool", match_names=["mytool", "my-tool"])
    def inspect_mytool():
        success, stdout, _ = run_command(["mytool", "status"], timeout=15)
        if not success:
            return None
        # ... parse stdout ...
        return {
            "tool": "mytool",
            "items": [...],
            "restore_commands": [...],
            "restore_note": "..."
        }
"""

from typing import Dict, Any, Optional, List, Callable

from .utils import run_command


# Registry: maps tool identifiers to inspector functions
INSPECTOR_REGISTRY: Dict[str, Callable[[], Optional[Dict[str, Any]]]] = {}

# Tool name -> list of item names (lowercased) that match this tool in the scan profile
TOOL_MATCH_NAMES: Dict[str, List[str]] = {}


def register_inspector(tool_name: str, match_names: Optional[List[str]] = None):
    """Decorator to register an inspector function.

    Args:
        tool_name: Identifier for this inspector (e.g., "ollama", "docker")
        match_names: Item names (lowercased) to match against in the scan profile.
                     Defaults to [tool_name].
    """
    def decorator(func):
        INSPECTOR_REGISTRY[tool_name] = func
        TOOL_MATCH_NAMES[tool_name] = match_names or [tool_name]
        return func
    return decorator


@register_inspector("ollama", match_names=["ollama"])
def inspect_ollama() -> Optional[Dict[str, Any]]:
    """Inspect Ollama for installed models."""
    success, stdout, _ = run_command(["ollama", "list"], timeout=15)
    if not success or not stdout.strip():
        return None

    lines = stdout.strip().split("\n")
    if len(lines) <= 1:
        # Only header row, no models
        return None

    items = []
    restore_commands = []
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if not parts:
            continue
        model_name = parts[0]
        # ollama list format: NAME ID SIZE MODIFIED
        size = parts[2] + " " + parts[3] if len(parts) >= 4 else ""
        items.append({"name": model_name, "size": size})
        restore_commands.append(f"ollama pull {model_name}")

    if not items:
        return None

    return {
        "tool": "ollama",
        "items": items,
        "restore_commands": restore_commands,
        "restore_note": (
            "Ollama models will be re-downloaded on the new machine. "
            "Large models may require significant time and bandwidth."
        ),
    }


@register_inspector("docker", match_names=["docker", "docker desktop"])
def inspect_docker() -> Optional[Dict[str, Any]]:
    """Inspect Docker for images and containers."""
    # Check if Docker daemon is accessible
    success, _, _ = run_command(["docker", "info"], timeout=10)
    if not success:
        return None

    items = []
    restore_commands = []

    # Get images
    success, stdout, _ = run_command(
        ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"],
        timeout=15,
    )
    if success and stdout.strip():
        for line in stdout.strip().split("\n"):
            if not line or "<none>" in line:
                continue
            parts = line.split("\t")
            image_name = parts[0]
            size = parts[1] if len(parts) > 1 else ""
            items.append({"type": "image", "name": image_name, "size": size})
            restore_commands.append(f"docker pull {image_name}")

    # Get containers (for reference, not auto-restored)
    success, stdout, _ = run_command(
        ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"],
        timeout=15,
    )
    if success and stdout.strip():
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                items.append({
                    "type": "container",
                    "name": parts[0],
                    "image": parts[1],
                    "status": parts[2] if len(parts) > 2 else "",
                })

    if not items:
        return None

    return {
        "tool": "docker",
        "items": items,
        "restore_commands": restore_commands,
        "restore_note": (
            "Docker images will be re-pulled. Containers are listed for reference "
            "but must be recreated manually (e.g., via docker-compose)."
        ),
    }
