from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LlmResult:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    web_searches: int = 0
    web_fetches: int = 0


class SearchLlm(Protocol):
    """Puerto del modelo que busca ofertas en la web. Lanza `LlmError` si no puede completar la búsqueda."""

    def search(self, prompt: str) -> LlmResult: ...
