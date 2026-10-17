"""Cliente del modelo. `LlmClient` es el puerto: en producción se usa Claude Code, en las pruebas un doble."""

import json
import os
import subprocess
from pathlib import Path
from typing import Protocol

READ_ONLY_TOOLS = ("WebSearch", "WebFetch")  # sin Bash ni escritura: el modelo solo puede leer la web
DEFAULT_TIMEOUT_SECONDS = 1200


class LlmError(RuntimeError):
    pass


class LlmClient(Protocol):
    def complete(self, prompt: str) -> str: ...


class ClaudeCodeCli:
    """Ejecuta Claude Code en modo no interactivo (usa la suscripción ya iniciada) y devuelve su respuesta."""

    def __init__(
        self,
        node_exe: Path | None = None,
        cli_script: Path | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._node = node_exe or Path(os.environ.get("NODE_EXE", r"C:\Program Files\nodejs\node.exe"))
        self._cli = cli_script or Path(
            os.environ.get(
                "CLAUDE_CJS",
                str(
                    Path(os.environ.get("APPDATA", ""))
                    / "npm" / "node_modules" / "@anthropic-ai" / "claude-code" / "cli-wrapper.cjs"
                ),
            )
        )  # fmt: skip
        self._timeout = timeout

    def complete(self, prompt: str) -> str:
        for required in (self._node, self._cli):
            if not required.is_file():
                raise LlmError(f"No existe {required}. Define NODE_EXE / CLAUDE_CJS o instala Claude Code.")
        command = [
            str(self._node), str(self._cli), "--print", "--output-format", "json",
            "--allowedTools", ",".join(READ_ONLY_TOOLS),
        ]  # fmt: skip
        # El prompt va por stdin: evita el límite de longitud de argumentos y no aparece en la lista de procesos.
        try:
            result = subprocess.run(  # noqa: S603
                command,
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self._timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise LlmError(f"Claude Code no respondió en {self._timeout} s") from exc
        if result.returncode != 0:
            raise LlmError(f"Claude Code terminó con error (código {result.returncode}): {result.stderr[:800]}")
        if not result.stdout.strip():
            raise LlmError("Claude Code no devolvió ninguna respuesta")
        return _unwrap(result.stdout)


def _unwrap(stdout: str) -> str:
    """`--output-format json` envuelve la respuesta en un objeto con el campo «result»."""
    try:
        wrapper = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout
    if isinstance(wrapper, dict) and isinstance(wrapper.get("result"), str):
        return wrapper["result"]
    return stdout
