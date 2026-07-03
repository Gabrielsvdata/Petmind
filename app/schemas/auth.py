from datetime import datetime

from pydantic import BaseModel, Field


class UsuarioCreate(BaseModel):
    """Schema para cadastro de usuário."""

    nome: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    senha: str = Field(..., min_length=6, max_length=128)


class UsuarioLogin(BaseModel):
    """Schema para login."""

    email: str = Field(..., min_length=3, max_length=255)
    senha: str = Field(..., min_length=6, max_length=128)


class UsuarioResponse(BaseModel):
    """Schema público de usuário."""

    id: int
    nome: str
    email: str
    criado_em: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Resposta de autenticação sem token."""

    mensagem: str
    usuario: UsuarioResponse


class EsqueciSenhaRequest(BaseModel):
    """Request para fluxo de esqueci senha."""

    email: str = Field(..., min_length=3, max_length=255)


class EsqueciSenhaResponse(BaseModel):
    """Resposta para esqueci senha."""

    mensagem: str


class RedefinirSenhaRequest(BaseModel):
    """Request para troca de senha com validação da senha atual."""

    senha_antiga: str = Field(..., min_length=6, max_length=128)
    nova_senha: str = Field(..., min_length=6, max_length=128)
