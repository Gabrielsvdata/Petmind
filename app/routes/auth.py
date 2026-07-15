"""Rotas de usuário — registro e login simples, sem JWT."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Usuario
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegistroRequest,
    UsuarioResponse,
)
from app.services.auth_service import hash_senha, verificar_senha

roteador = APIRouter(prefix="/auth", tags=["auth"])


@roteador.post("/registro", response_model=UsuarioResponse, status_code=201)
def registrar(request: RegistroRequest, db: Session = Depends(get_db)) -> Usuario:
    """Cadastra novo usuário."""
    existente = db.query(Usuario).filter(Usuario.email == request.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    usuario = Usuario(
        nome=request.nome,
        email=request.email,
        senha_hash=hash_senha(request.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@roteador.post("/register", response_model=UsuarioResponse, status_code=201)
def registrar_alias(request: RegistroRequest, db: Session = Depends(get_db)) -> Usuario:
    """Alias para manter compatibilidade com clientes existentes."""
    return registrar(request, db)


@roteador.post("/register-admin", response_model=UsuarioResponse, status_code=201)
def registrar_admin(request: RegistroRequest, db: Session = Depends(get_db)) -> Usuario:
    """Cadastra usuário administrador para uso local e homologação manual."""
    existente = db.query(Usuario).filter(Usuario.email == request.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    usuario = Usuario(
        nome=request.nome,
        email=request.email,
        senha_hash=hash_senha(request.senha),
        papel="admin",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@roteador.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Autentica usuário — retorna dados para salvar no frontend."""
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()
    if not usuario or not verificar_senha(request.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos")

    return LoginResponse(
        mensagem="Login realizado com sucesso",
        usuario_id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        papel=usuario.papel,
    )
