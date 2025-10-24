"""Pytest configuration helpers for the backend test suite."""
from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR / "app"

project_path = str(PROJECT_DIR)

if project_path not in sys.path:
    sys.path.insert(0, project_path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")
