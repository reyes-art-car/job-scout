import json
import re

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
MAX_RESPONSE_CHARS = 2_000_000
MAX_OFFERS = 200


def extract_offer_dicts(response: str) -> list[dict]:
    """Extrae el primer array JSON de objetos de la respuesta del modelo (con o sin bloque ```json).

    Se decodifica con `raw_decode` desde cada «[»: tolera texto antes y después del JSON y no depende de
    expresiones regulares que puedan fallar con llaves anidadas. Devuelve [] si no hay un array válido.
    """
    text = response[:MAX_RESPONSE_CHARS]
    candidates = [match.group(1) for match in _FENCE.finditer(text)] + [text]
    decoder = json.JSONDecoder()
    for candidate in candidates:
        for start in (i for i, char in enumerate(candidate) if char == "["):
            try:
                value, _ = decoder.raw_decode(candidate[start:])
            except json.JSONDecodeError:
                continue
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value[:MAX_OFFERS]
    return []
