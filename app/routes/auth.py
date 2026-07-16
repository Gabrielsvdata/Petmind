"""Rotas de usuário — registro e login simples, sem JWT."""

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Usuario
from app.schemas.auth import (
    AdminBootstrapStatusResponse,
    LoginRequest,
    LoginResponse,
    RegistroAdminBootstrapRequest,
    RegistroRequest,
    UsuarioResponse,
)
from app.services.auth_service import verificar_senha
from app.services.usuario_service import buscar_usuario_por_email, criar_usuario

roteador = APIRouter(prefix="/auth", tags=["auth"])

ADMIN_BOOTSTRAP_ENV = "ENABLE_ADMIN_BOOTSTRAP"
ADMIN_BOOTSTRAP_KEY_ENV = "ADMIN_BOOTSTRAP_KEY"


def _admin_bootstrap_habilitado() -> bool:
    valor = os.getenv(ADMIN_BOOTSTRAP_ENV, "false").strip().lower()
    return valor in {"1", "true", "yes", "on"}


def _admin_bootstrap_key() -> str | None:
    chave = os.getenv(ADMIN_BOOTSTRAP_KEY_ENV, "").strip()
    return chave or None


def _ja_existe_admin(db: Session) -> bool:
    return db.query(Usuario).filter(Usuario.papel == "admin").first() is not None


@roteador.post("/registro", response_model=UsuarioResponse, status_code=201)
@roteador.post("/register", response_model=UsuarioResponse, status_code=201)
def registrar(
    request: RegistroRequest,
    db: Session = Depends(get_db),
) -> UsuarioResponse:
    """Cadastra novo usuário."""
    return criar_usuario(
        db,
        nome=request.nome,
        email=request.email,
        senha=request.senha,
    )


@roteador.get(
    "/admin-bootstrap/status",
    response_model=AdminBootstrapStatusResponse,
)
def status_admin_bootstrap() -> AdminBootstrapStatusResponse:
    """Informa se a tela deve exibir a opção de criar primeiro admin."""
    chave = _admin_bootstrap_key()
    return AdminBootstrapStatusResponse(
        habilitado=_admin_bootstrap_habilitado(),
        exige_chave=bool(chave),
    )


@roteador.post(
    "/admin-bootstrap/register-admin",
    response_model=UsuarioResponse,
    status_code=201,
)
@roteador.post(
    "/register-admin",
    response_model=UsuarioResponse,
    status_code=201,
)
def registrar_admin_bootstrap(
    request: RegistroAdminBootstrapRequest,
    db: Session = Depends(get_db),
) -> UsuarioResponse:
    """Cria o primeiro admin quando o bootstrap estiver habilitado."""
    if not _admin_bootstrap_habilitado():
        raise HTTPException(
            status_code=403,
            detail="Bootstrap de administrador desabilitado",
        )

    chave = _admin_bootstrap_key()
    if chave and request.chave_bootstrap != chave:
        raise HTTPException(status_code=403, detail="Chave de bootstrap inválida")

    if _ja_existe_admin(db):
        raise HTTPException(
            status_code=409,
            detail="Administrador já existe. Use /admin/usuarios/admin",
        )

    return criar_usuario(
        db,
        nome=request.nome,
        email=request.email,
        senha=request.senha,
        papel="admin",
    )

@roteador.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Autentica usuário — retorna dados para salvar no frontend."""
    usuario = buscar_usuario_por_email(db, request.email)
    if not usuario or not verificar_senha(request.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    return LoginResponse(
        mensagem="Login realizado com sucesso",
        usuario_id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        papel=usuario.papel,
    )
