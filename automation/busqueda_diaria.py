#!/usr/bin/env python3
"""Búsqueda diaria de ofertas junior Java/Spring/Angular.

    python automation/busqueda_diaria.py                    # portales de España
    python automation/busqueda_diaria.py --portal linkedin  # solo LinkedIn España, exhaustivo
    python automation/busqueda_diaria.py --portal europa    # empresas internacionales 100 % remoto

La lógica vive en el paquete `jobsearch/`; este fichero solo es el punto de entrada que usa el .bat.
Dependencias: pip install -r automation/requirements.txt
"""

import sys

from jobsearch.cli import main

if __name__ == "__main__":
    sys.exit(main())
