"""Búsqueda diaria de ofertas. Ver busqueda_diaria.py."""

import sys
from pathlib import Path

# El saneado de texto es el mismo que usa la API: una sola implementación para todo el proyecto.
_BACKEND_SRC = Path(__file__).resolve().parents[2] / "backend" / "src"
if str(_BACKEND_SRC) not in sys.path:
    sys.path.insert(0, str(_BACKEND_SRC))
