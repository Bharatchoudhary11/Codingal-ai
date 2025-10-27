"""Expose the Django project package from its nested backend location."""
from pathlib import Path

_app_package_dir = Path(__file__).resolve().parent
_backend_project_dir = _app_package_dir.parent / "backend" / "app" / "app"

__path__ = [str(_app_package_dir), str(_backend_project_dir)]
