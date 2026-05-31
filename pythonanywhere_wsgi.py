"""
pythonanywhere_wsgi.py — WSGI entry point khusus PythonAnywhere.

Copy isi file ini ke:
  /var/www/<username>_pythonanywhere_com_wsgi.py

Ganti <username> dengan username PythonAnywhere Anda.
"""

import os
import sys
from pathlib import Path

# ── Path proyek di PythonAnywhere ──────────────────────────────────────────────
# Ganti 'muhammadsyafii08' dengan username PythonAnywhere Anda
project_home = '/home/muhammadsyafii08/aplikasi-1000hpk'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

# ── Load .env ──────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# ── Buat Flask app ─────────────────────────────────────────────────────────────
from app import create_app
application = create_app()
