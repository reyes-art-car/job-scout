class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    """Email o contraseña incorrectos. No distingue el motivo para no revelar qué emails existen."""


class RegistrationClosedError(Exception):
    pass
