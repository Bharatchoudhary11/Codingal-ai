"""Pytest configuration helpers for the backend test suite."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
PROJECT_DIR = BASE_DIR / "app"

repo_path = str(REPO_ROOT)
project_path = str(PROJECT_DIR)

if repo_path not in sys.path:
    sys.path.insert(0, repo_path)

if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "backend.app.app.settings"
)
