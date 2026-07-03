from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import Usuario
from app.schemas.auth import (
    EsqueciSenhaRequest,
    EsqueciSenhaResponse,
    LoginResponse,
    RedefinirSenhaRequest,
    UsuarioCreate,
    UsuarioLogin,
    UsuarioResponse,
)
from app.services.auth_service import (
    gerar_hash_senha,
    gerar_token_reset,
    get_usuario_atual,
    verificar_senha,
)

roteador = APIRouter(prefix="/auth", tags=["auth"])


@roteador.post("/register", response_model=UsuarioResponse, status_code=201)
def registrar_usuario(payload: UsuarioCreate, db: Session = Depends(get_db)) -> Usuario:
    """Cria um novo usuário para autenticação."""
    existente = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if existente is not None:
        raise HTTPException(status_code=400, detail="E-mail já cadastrado")

    usuario = Usuario(
        nome=payload.nome,
        email=payload.email,
        senha_hash=gerar_hash_senha(payload.senha),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@roteador.post("/login", response_model=LoginResponse)
def login_usuario(payload: UsuarioLogin, db: Session = Depends(get_db)) -> LoginResponse:
    """Autentica usuário por e-mail e senha (sem token)."""
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario is None or not verificar_senha(payload.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return LoginResponse(
        mensagem="Login realizado com sucesso",
        usuario=UsuarioResponse.model_validate(usuario),
    )


@roteador.get("/me", response_model=UsuarioResponse)
def usuario_logado(usuario: Usuario = Depends(get_usuario_atual)) -> Usuario:
    """Retorna dados do usuário autenticado."""
    return usuario


@roteador.post("/esqueci-senha", response_model=EsqueciSenhaResponse)
def esqueci_senha(
    payload: EsqueciSenhaRequest,
    db: Session = Depends(get_db),
) -> EsqueciSenhaResponse:
    """Gera token local de redefinição sem expor token na resposta."""
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if usuario is None:
        return EsqueciSenhaResponse(
            mensagem="Se o e-mail existir, enviaremos as instruções para redefinir a senha."
        )

    token = gerar_token_reset()
    # Em produção, enviar token por e-mail. Aqui registramos no servidor para testes.
    print(f"[PetMind] Token de reset para {usuario.email}: {token}")
    return EsqueciSenhaResponse(
        mensagem="Se o e-mail existir, enviaremos as instruções para redefinir a senha."
    )


@roteador.post("/redefinir-senha")
def redefinir_senha(
    payload: RedefinirSenhaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> dict[str, str]:
    """Troca senha do usuário autenticado validando a senha atual."""
    if not verificar_senha(payload.senha_antiga, usuario.senha_hash):
        raise HTTPException(status_code=400, detail="Senha antiga incorreta")

    usuario.senha_hash = gerar_hash_senha(payload.nova_senha)
    db.commit()

    return {"mensagem": "Senha redefinida com sucesso"}
