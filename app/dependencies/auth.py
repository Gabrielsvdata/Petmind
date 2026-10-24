"""Dependências de autenticação da aplicação."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Usuario
from app.services.token_service import ler_usuario_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_usuario_atual(
    db: Session = Depends(get_db),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Usuario:
    """Obtém o usuário autenticado a partir do token (Authorization: Bearer)."""
    if authorization is None or authorization.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Autenticação obrigatória")

    usuario_id = ler_usuario_id(authorization.credentials)
    if usuario_id is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")

    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=401, detail="Sessão inválida ou expirada")
    return usuario
