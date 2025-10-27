"""WSGI entrypoint for Render deployment."""
from pathlib import Path
import os
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_APP_PATH = ROOT_DIR / "backend" / "app"
if str(BACKEND_APP_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_APP_PATH))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "backend.app.app.settings"
)

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
