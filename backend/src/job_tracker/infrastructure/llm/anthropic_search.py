"""Cliente de búsqueda sobre la API de Claude con las herramientas de servidor web_search y web_fetch."""

import logging
from typing import Any

import anthropic

from job_tracker.domain.search.exceptions import LlmError
from job_tracker.domain.search.llm import LlmResult

logger = logging.getLogger("job_tracker.search")

# La API ejecuta las búsquedas en sus servidores; si el turno es largo devuelve `pause_turn` y hay que
# reenviar la conversación para que continúe. Se acota para que un bucle no gaste dinero sin fin.
MAX_CONTINUATIONS = 6


class AnthropicSearchLlm:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        max_tokens: int,
        max_web_searches: int,
        max_web_fetches: int,
        timeout_seconds: int,
        client: Any | None = None,
    ) -> None:
        if client is None and not api_key:
            raise LlmError("Falta ANTHROPIC_API_KEY")
        self._client = client or anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds, max_retries=2)
        self._model = model
        self._max_tokens = max_tokens
        self._tools: list[Any] = [
            {"type": "web_search_20250305", "name": "web_search", "max_uses": max_web_searches},
            {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": max_web_fetches},
        ]

    def search(self, prompt: str) -> LlmResult:
        messages: list[Any] = [{"role": "user", "content": prompt}]
        input_tokens = output_tokens = searches = fetches = 0
        final_text = ""
        for _ in range(MAX_CONTINUATIONS):
            try:
                with self._client.messages.stream(
                    model=self._model, max_tokens=self._max_tokens, tools=self._tools, messages=messages
                ) as stream:
                    message = stream.get_final_message()
            except anthropic.APIError as exc:
                # El detalle (que puede incluir cabeceras o ids internos) va al log, no al usuario.
                logger.warning("Fallo de la API de Claude: %s", exc)
                raise LlmError("El servicio de búsqueda no está disponible ahora mismo") from exc

            input_tokens += message.usage.input_tokens
            output_tokens += message.usage.output_tokens
            server_usage = getattr(message.usage, "server_tool_use", None)
            if server_usage is not None:
                searches += server_usage.web_search_requests
                fetches += server_usage.web_fetch_requests
            final_text = "".join(getattr(block, "text", "") for block in message.content if block.type == "text")

            if message.stop_reason != "pause_turn":
                break
            messages = [*messages, {"role": "assistant", "content": message.content}]
        else:
            logger.warning("La búsqueda superó %d continuaciones", MAX_CONTINUATIONS)

        if not final_text.strip():
            raise LlmError("El modelo no devolvió ninguna respuesta")
        return LlmResult(final_text, input_tokens, output_tokens, searches, fetches)
