"""Dependências de autenticação da aplicação."""
import base64

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBasicCredentials
from fastapi.security.http import HTTPBasic as HTTPBasicSecurity
from fastapi.security.http import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Usuario
from app.services.auth_service import verificar_senha

basic_scheme = HTTPBasicSecurity(auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


def _extrair_credenciais_basic(
    authorization: HTTPAuthorizationCredentials | None,
) -> HTTPBasicCredentials | None:
    """Converte um header Authorization Basic em credenciais utilizáveis."""
    if authorization is None or authorization.scheme.lower() != "basic":
        return None

    try:
        decoded = base64.b64decode(authorization.credentials).decode("utf-8")
        email, senha = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Credenciais inválidas") from None

    return HTTPBasicCredentials(username=email, password=senha)


def get_usuario_atual(
    db: Session = Depends(get_db),
    credenciais_basic: HTTPBasicCredentials | None = Depends(basic_scheme),
    authorization: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> Usuario:
    """Obtém o usuário autenticado a partir do header Authorization Basic."""
    credenciais = credenciais_basic
    if credenciais is None:
        credenciais = _extrair_credenciais_basic(authorization)

    if credenciais is None:
        raise HTTPException(status_code=401, detail="Autenticação obrigatória")

    usuario = db.query(Usuario).filter(Usuario.email == credenciais.username).first()
    if usuario is None or not verificar_senha(credenciais.password, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return usuario
