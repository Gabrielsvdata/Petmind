"""Rotas de usuário — registro e login simples, sem JWT."""

from fastapi import APIRouter, Depends, HTTPException
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
