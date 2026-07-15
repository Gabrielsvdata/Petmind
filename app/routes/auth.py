"""Rotas de usuário — registro e login simples, sem JWT."""
import os

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegistroRequest,
    UsuarioResponse,
)
from app.services.auth_service import verificar_senha
from app.services.usuario_service import buscar_usuario_por_email, criar_usuario

roteador = APIRouter(prefix="/auth", tags=["auth"])

HOSTS_LOCAIS = {"127.0.0.1", "localhost", "::1"}


def _validar_bootstrap_admin_local(request: Request) -> None:
    """Permite cadastro admin apenas em bootstrap local explicitamente habilitado."""
    bootstrap_habilitado = os.getenv("ENABLE_ADMIN_BOOTSTRAP", "").strip().lower()
    if bootstrap_habilitado not in {"1", "true", "yes", "on"}:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rota não disponível neste ambiente",
        )

    client_host = request.client.host if request.client else None
    if client_host not in HOSTS_LOCAIS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro administrativo liberado apenas em ambiente local",
        )


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


@roteador.post("/register-admin", response_model=UsuarioResponse, status_code=201)
def registrar_admin(
    request: RegistroRequest,
    http_request: Request,
    db: Session = Depends(get_db),
) -> UsuarioResponse:
    """Cadastra usuário administrador para uso local e homologação manual."""
    _validar_bootstrap_admin_local(http_request)
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
