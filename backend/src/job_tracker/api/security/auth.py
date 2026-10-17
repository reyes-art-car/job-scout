import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False, description="Token de acceso configurado en API_TOKEN")


def require_api_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """Dependencia de FastAPI: exige `Authorization: Bearer <API_TOKEN>` cuando hay un token configurado.

    Sin token (solo permitido en desarrollo) la API queda abierta, pensada para uso local.
    La comparación es de tiempo constante para no filtrar el token por diferencias de latencia.
    """
    expected = request.app.state.settings.api_token
    if expected is None:
        return
    supplied = credentials.credentials if credentials is not None else ""
    if not hmac.compare_digest(supplied.encode(), expected.get_secret_value().encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
