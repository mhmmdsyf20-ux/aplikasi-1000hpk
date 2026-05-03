import sys
import os

# Tambahkan path proyek ke sys.path
project_home = '/home/USERNAMU/mysite'  # Ganti USERNAMU dengan username PythonAnywhere kamu
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable agar tidak exit saat DB error
os.environ['FLASK_TESTING'] = ''

from app import create_app
application = create_app()
