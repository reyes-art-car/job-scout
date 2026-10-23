import logging

from job_tracker.domain.user.entities import User
from job_tracker.domain.user.mailer import EmailSender
from job_tracker.domain.user.tokens import ActionKind, ActionTokens

logger = logging.getLogger("job_tracker.email")


class AccountMailer:
    """Redacta y envía los correos de la cuenta. Nunca lanza: un fallo de correo no debe cambiar la respuesta."""

    def __init__(self, sender: EmailSender, tokens: ActionTokens, base_url: str) -> None:
        self._sender = sender
        self._tokens = tokens
        self._base_url = base_url.rstrip("/")

    def _link(self, route: str, token: str | None = None) -> str:
        # Las rutas de Angular usan «#/»: el token viaja en el fragmento y no llega a los logs de ningún servidor.
        return f"{self._base_url}/#/{route}" + (f"?token={token}" if token else "")

    def _send(self, to: str, subject: str, body: str) -> None:
        try:
            self._sender.send(to, subject, body)
        except Exception:
            logger.exception("Fallo inesperado al enviar un correo")

    def send_verification(self, user: User) -> None:
        link = self._link("verificar", self._tokens.issue(ActionKind.VERIFY_EMAIL, user))
        self._send(
            user.email,
            "Confirma tu email · Job Hopping & Learning",
            f"Hola,\n\nConfirma tu email para poder lanzar búsquedas de ofertas:\n{link}\n\n"
            "El enlace caduca en unas horas. Si no has creado tú esta cuenta, ignora este mensaje.",
        )

    def send_already_registered(self, email: str) -> None:
        self._send(
            email,
            "Ya tienes una cuenta · Job Hopping & Learning",
            f"Hola,\n\nAlguien ha intentado crear una cuenta con este email, pero ya tienes una.\n"
            f"Puedes iniciar sesión aquí: {self._link('acceso')}\n"
            f"Si has olvidado la contraseña, puedes restablecerla desde esa misma pantalla.\n\n"
            "Si no has sido tú, ignora este mensaje: tu cuenta no ha cambiado.",
        )

    def send_password_reset(self, user: User) -> None:
        link = self._link("restablecer", self._tokens.issue(ActionKind.RESET, user))
        self._send(
            user.email,
            "Restablece tu contraseña · Job Hopping & Learning",
            f"Hola,\n\nPara elegir una contraseña nueva abre este enlace (caduca en media hora):\n{link}\n\n"
            "Si no lo has pedido tú, ignora este mensaje: tu contraseña sigue siendo la misma.",
        )
