from typing import Protocol


class EmailSender(Protocol):
    """Puerto de envío de correo. Las implementaciones no deben lanzar por un destinatario rechazado."""

    def send(self, to: str, subject: str, body: str) -> None: ...
