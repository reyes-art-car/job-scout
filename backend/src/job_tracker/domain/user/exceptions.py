class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    """Email o contraseña incorrectos. No distingue el motivo para no revelar qué emails existen."""


class RegistrationClosedError(Exception):
    pass


class WrongPasswordError(Exception):
    """La contraseña de confirmación es incorrecta (la sesión sí es válida)."""


class EmailNotVerifiedError(Exception):
    """La acción exige un email confirmado."""


class InvalidActionTokenError(Exception):
    """Enlace de verificación o de restablecimiento caducado, manipulado o ya usado."""


class TooManyAttemptsError(Exception):
    """Demasiados intentos de inicio de sesión fallidos para esa cuenta."""

    def __init__(self, retry_after: int):
        super().__init__("Demasiados intentos")
        self.retry_after = retry_after
