from pathlib import Path
import sys

# Ensure 'backend/' is on sys.path for imports like 'from app.main import app'
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
