import os
import sys

# Ensure project root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()

# Run collectstatic automatically on cold start if staticfiles is missing
staticfiles_dir = os.path.join(BASE_DIR, "staticfiles")
if not os.path.exists(staticfiles_dir) or not os.listdir(staticfiles_dir):
    try:
        from django.core.management import call_command
        call_command("collectstatic", interactive=False, clear=True)
    except Exception as e:
        print("Auto collectstatic warning:", e)
