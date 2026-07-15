"""Schemas de usuário."""
from pydantic import BaseModel, Field


class RegistroRequest(BaseModel):
    nome: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    senha: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    senha: str


class LoginResponse(BaseModel):
    mensagem: str
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
