"""Saneado de texto no confiable (peticiones HTTP, Excel, salida de un LLM) antes de guardarlo."""

import re
import unicodedata
from urllib.parse import urlsplit

import nh3

# Controles C0/C1 salvo tabulador y saltos de línea, más caracteres de ancho cero y de dirección bidi
# (usados para ocultar texto o falsear nombres de fichero).
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\u2066-\u2069]")
_ALLOWED_URL_SCHEMES = frozenset({"http", "https"})

# nh3 devuelve texto con entidades. Solo se deshacen las inocuas; `&lt;` y `&gt;` se mantienen
# codificadas para que el resultado nunca contenga marcado aunque otro consumidor lo pinte sin escapar.
_SAFE_ENTITIES = (("&quot;", '"'), ("&#39;", "'"), ("&#x27;", "'"), ("&amp;", "&"))


def clean_text(value: str) -> str:
    """Normaliza a NFC, elimina HTML y caracteres de control (incluidos los de dirección bidi)."""
    text = nh3.clean(unicodedata.normalize("NFC", value), tags=set())
    for entity, char in _SAFE_ENTITIES:
        text = text.replace(entity, char)
    return _CONTROL_CHARS.sub("", text).strip()


def validate_http_url(value: str) -> str:
    """Solo URLs http(s) absolutas: bloquea javascript:, data:, file: y similares."""
    candidate = clean_text(value)
    # Una URL no contiene espacios ni saltos de línea. `urlsplit` los ignora al analizar, pero el texto
    # original se guardaría tal cual y podría colarse en un enlace o en un prompt como instrucción.
    # Se mira también el original: el saneado convierte algunos espacios (p. ej. NBSP) en entidades HTML.
    if any(char.isspace() for char in candidate) or any(char.isspace() for char in value.strip()):
        raise ValueError("La URL no puede contener espacios ni saltos de línea")
    parts = urlsplit(candidate)
    if parts.scheme.lower() not in _ALLOWED_URL_SCHEMES or not parts.netloc:
        raise ValueError("La URL debe ser http o https")
    return candidate


def clean_bounded(value: str, max_length: int) -> str:
    """Sanea y recorta a `max_length` (para columnas de tamaño fijo)."""
    return clean_text(value)[:max_length]
