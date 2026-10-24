"""Schemas de usuário."""
from pydantic import BaseModel, Field


class RegistroRequest(BaseModel):
    nome: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    senha: str = Field(..., min_length=6)


class RegistroAdminBootstrapRequest(RegistroRequest):
    chave_bootstrap: str | None = None


class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginDemoRequest(BaseModel):
    perfil: str = "usuario"


class LoginResponse(BaseModel):
    mensagem: str
    access_token: str
    token_type: str = "bearer"
    usuario_id: int
    nome: str
    email: str
    papel: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    papel: str

    model_config = {"from_attributes": True}


class AdminBootstrapStatusResponse(BaseModel):
    habilitado: bool
    exige_chave: bool
