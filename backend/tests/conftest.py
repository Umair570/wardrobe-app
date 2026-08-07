"""
Shared pytest setup.

Test modules in this suite import in two different styles — `app.services...`
and `backend.app.services...` — so both the repository root and `backend/` go on
sys.path. `ml/` lives at the repository root too, which the classification tests
rely on.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent

for path in (REPO_ROOT, BACKEND_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
