import os
import sys
from pathlib import Path

# Use the repository root as the application path.
project_home = Path(__file__).resolve().parent
if str(project_home) not in sys.path:
    sys.path.insert(0, str(project_home))

# Load .env from repository root if present.
from dotenv import load_dotenv
load_dotenv(project_home / '.env')

from app import create_app
application = create_app()
