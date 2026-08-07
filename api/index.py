import os
import shutil
import sys
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Copy bundled db.sqlite3 to /tmp/db.sqlite3 for Vercel Serverless Demo Environment
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
if IS_VERCEL:
    tmp_db = Path("/tmp/db.sqlite3")
    bundled_db = Path(BASE_DIR) / "db.sqlite3"
    if bundled_db.exists() and (not tmp_db.exists() or tmp_db.stat().st_size == 0):
        try:
            shutil.copyfile(bundled_db, tmp_db)
        except Exception as e:
            pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()
