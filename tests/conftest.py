# tests/conftest.py
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _add_src_to_path_and_isolate_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    - Añade ./src al sys.path para que los tests puedan hacer: `import api`, `import memory_json`, etc.
    - Aísla el CWD en tmp_path para que data/memory/ se cree en un directorio temporal
      (no ensucia tu repo real).
    """
    project_root = Path(__file__).resolve().parents[1]
    src_dir = project_root / "src"

    # Asegura que "src" está en el path de imports
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    # Aísla filesystem (CWD) para tests
    monkeypatch.chdir(tmp_path)
    yield

