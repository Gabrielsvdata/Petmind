"""Rotas de usuário — registro, login com token e acesso de demonstração."""

import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.demo import CONTAS_DEMO
from app.dependencies.auth import get_usuario_atual
from app.models.user import Usuario
from app.schemas.auth import (
    AdminBootstrapStatusResponse,
    LoginDemoRequest,
    LoginRequest,
    LoginResponse,
    RegistroAdminBootstrapRequest,
    RegistroRequest,
    UsuarioResponse,
)
from app.services.auth_service import verificar_senha
from app.services.token_service import gerar_token
from app.services.usuario_service import buscar_usuario_por_email, criar_usuario

roteador = APIRouter(prefix="/auth", tags=["auth"])

ADMIN_BOOTSTRAP_ENV = "ENABLE_ADMIN_BOOTSTRAP"
ADMIN_BOOTSTRAP_KEY_ENV = "ADMIN_BOOTSTRAP_KEY"


def _admin_bootstrap_habilitado() -> bool:
    # Desligado por padrão: criar admin pela tela só em ambiente de teste
    valor = os.getenv(ADMIN_BOOTSTRAP_ENV, "false").strip().lower()
    return valor in {"1", "true", "yes", "on"}


def _admin_bootstrap_key() -> str | None:
    chave = os.getenv(ADMIN_BOOTSTRAP_KEY_ENV, "").strip()
    return chave or None


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
    """Informa se a tela deve exibir a opção de criar conta admin."""
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
    """Cria conta admin via fluxo de bootstrap para ambiente de teste."""
    if not _admin_bootstrap_habilitado():
        raise HTTPException(
            status_code=403,
            detail="Bootstrap de administrador desabilitado",
        )

    chave = _admin_bootstrap_key()
    if chave and request.chave_bootstrap != chave:
        raise HTTPException(status_code=403, detail="Chave de bootstrap inválida")

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
    return _resposta_login(usuario)


def _resposta_login(usuario: Usuario) -> LoginResponse:
    return LoginResponse(
        mensagem="Login realizado com sucesso",
        access_token=gerar_token(usuario.id, usuario.papel),
        usuario_id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        papel=usuario.papel,
    )


@roteador.post("/login-demo", response_model=LoginResponse)
def login_demo(
    request: LoginDemoRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Entra numa conta de demonstração sem senha (só com DEMO_MODE=true)."""
    if os.getenv("DEMO_MODE", "false").strip().lower() != "true":
        raise HTTPException(status_code=404, detail="Modo demonstração desativado")
    conta = CONTAS_DEMO.get(request.perfil)
    if conta is None:
        raise HTTPException(
            status_code=400, detail="Perfil deve ser 'usuario' ou 'admin'"
        )
    usuario = buscar_usuario_por_email(db, conta["email"])
    if usuario is None:
        raise HTTPException(
            status_code=503, detail="Conta de demonstração indisponível"
        )
    return _resposta_login(usuario)


@roteador.get("/me", response_model=UsuarioResponse)
def usuario_logado(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    """Retorna o usuário do token (usado para validar a sessão salva)."""
    return usuario
