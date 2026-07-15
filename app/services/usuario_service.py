"""Serviços de criação e busca de usuários."""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import Usuario
from app.services.auth_service import hash_senha


def buscar_usuario_por_email(db: Session, email: str) -> Usuario | None:
    """Busca usuário por e-mail."""
    return db.query(Usuario).filter(Usuario.email == email).first()


def criar_usuario(
    db: Session,
    *,
    nome: str,
    email: str,
    senha: str,
    papel: str = "usuario",
) -> Usuario:
    """Cria usuário com validação básica de e-mail único."""
    existente = buscar_usuario_por_email(db, email)
    if existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_senha(senha),
        papel=papel,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario
