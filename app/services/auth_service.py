import secrets

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Usuario

basic_scheme = HTTPBasic(auto_error=False)


def gerar_hash_senha(senha: str) -> str:
    """Gera hash de senha usando bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha.encode("utf-8"), salt).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica senha em relação ao hash salvo."""
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except Exception:
        return False


def get_usuario_atual(
    credentials: HTTPBasicCredentials | None = Depends(basic_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    """Dependency para obter usuário autenticado via HTTP Basic."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Autenticação obrigatória")

    email = credentials.username
    senha = credentials.password
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None or not verificar_senha(senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )

    # Challenges de HTTP Basic ajudam navegadores/clientes a entender o esquema.
    # Mantemos apenas autenticação por senha, sem sessão por token.
    return usuario


def gerar_token_reset() -> str:
    """Gera token aleatório para fluxo de redefinição de senha (apenas dev)."""
    return secrets.token_urlsafe(32)
