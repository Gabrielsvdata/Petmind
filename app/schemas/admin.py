from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.pet import PetResponse


class UsuarioAdminResponse(BaseModel):
    id: int
    nome: str
    email: str
    papel: str
    criado_em: datetime
    total_pets: int
    total_registros: int
    ultimo_acesso: datetime | None

    model_config = {"from_attributes": True}


class AlterarPapelRequest(BaseModel):
    papel: str = Field(..., pattern="^(usuario|admin)$")


class CriarAdminRequest(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=255)
    senha: str = Field(..., min_length=6, max_length=255)


class UsuarioDetalheAdminResponse(BaseModel):
    id: int
    nome: str
    email: str
    papel: str
    criado_em: datetime
    total_pets: int
    total_registros: int
    ultimo_acesso: datetime | None
    pets: list[PetResponse]


class EstatisticasResponse(BaseModel):
    total_usuarios: int
    total_pets: int
    total_registros: int
    pets_por_especie: dict[str, int]
    estados_mais_comuns: dict[str, int]
    usuarios_ativos: int
    registros_ultima_semana: int

