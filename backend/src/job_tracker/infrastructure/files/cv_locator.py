from pathlib import Path


class DirectoryCvLocator:
    """Localiza CVs adaptados dentro de un directorio base sin permitir salir de él.

    El nombre del fichero procede de la base de datos (que a su vez puede rellenar un LLM o un
    importador), así que nunca se confía en él: se resuelve la ruta real, incluidos los enlaces
    simbólicos, y se exige que siga dentro del directorio base.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir.resolve()

    def locate(self, filename: str) -> Path | None:
        if not filename or "\x00" in filename:
            return None
        candidate = (self._base_dir / Path(filename).name).resolve()
        if not candidate.is_relative_to(self._base_dir) or not candidate.is_file():
            return None
        return candidate
