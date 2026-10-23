"""Envío de correo: SMTP en producción y consola en desarrollo.

Un fallo de envío nunca se propaga ni cambia la respuesta de la API: así el comportamiento visible es el mismo
exista o no la cuenta (no se puede usar el error para descubrir qué emails están registrados).
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Literal

logger = logging.getLogger("job_tracker.email")

SMTP_TIMEOUT_SECONDS = 10


class ConsoleEmailSender:
    """Solo desarrollo: escribe el correo en el log para poder abrir los enlaces sin un servidor SMTP.

    Va a nivel WARNING a propósito: es el único nivel que se ve con la configuración de logging por defecto. En
    producción este envío no se puede activar (la configuración exige SMTP): nunca deja enlaces con token en el log.
    """

    def send(self, to: str, subject: str, body: str) -> None:
        logger.warning("[correo simulado, solo desarrollo] a=%s asunto=%s\n%s", to, subject, body)


class SmtpEmailSender:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        security: Literal["starttls", "ssl", "none"] = "starttls",
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender
        self._security = security

    def send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        try:
            context = ssl.create_default_context()
            if self._security == "ssl":
                with smtplib.SMTP_SSL(self._host, self._port, timeout=SMTP_TIMEOUT_SECONDS, context=context) as smtp:
                    self._deliver(smtp, message)
            else:
                with smtplib.SMTP(self._host, self._port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
                    if self._security == "starttls":
                        smtp.starttls(context=context)
                    self._deliver(smtp, message)
        except (OSError, smtplib.SMTPException):
            # Sin el destinatario ni el cuerpo en el log: contienen el email y un enlace con token.
            logger.exception("No se pudo enviar un correo (asunto %r)", subject)

    def _deliver(self, smtp: smtplib.SMTP, message: EmailMessage) -> None:
        if self._username:
            smtp.login(self._username, self._password)
        smtp.send_message(message)
