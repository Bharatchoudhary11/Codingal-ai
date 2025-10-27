"""Expose the Django project package from its nested backend location."""
from pathlib import Path

_repo_root = Path(__file__).resolve().parent.parent
_backend_project_dir = _repo_root / "backend" / "app" / "app"

__path__ = [str(_backend_project_dir)]
