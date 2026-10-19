from fastapi import APIRouter, Response, status

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/check", status_code=status.HTTP_204_NO_CONTENT)
def check_access() -> Response:
    """Confirma que la clave de acceso enviada es válida (la exige la dependencia del router en `main.py`)."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
