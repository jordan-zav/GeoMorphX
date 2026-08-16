"""Helpers to import GeoMorphX suite modules from QGIS plugin context."""

from __future__ import annotations

from pathlib import Path
import sys


def ensure_suite_importable() -> None:
    """Ensure `geomorphx` can be imported when plugin runs from source tree."""
    try:
        import geomorphx  # noqa: F401
        return
    except Exception:
        pass

    plugin_dir = Path(__file__).resolve().parent
    repo_root = plugin_dir.parent
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)