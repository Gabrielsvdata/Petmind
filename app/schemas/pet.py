from datetime import datetime

from pydantic import BaseModel, Field


class PetBase(BaseModel):
    """Schema base com os campos compartilhados de um pet."""

    nome: str = Field(..., max_length=100, description="Nome do pet")
    raca: str = Field(..., max_length=100, description="Raça do pet")
    especie: str = Field(
        default="cachorro",
        description="Espécie do pet",
        pattern="^(cachorro|gato|hamster|coelho)$",
    )
    idade: int = Field(..., ge=0, description="Idade em anos")
    peso: float = Field(..., gt=0, description="Peso em kg")
    observacoes: str | None = Field(None, description="Observações adicionais")


class PetCreate(PetBase):
    """Schema para criação de um novo pet."""

    pass


class PetResponse(PetBase):
    """Schema de resposta ao consultar um pet."""

    id: int
    criado_em: datetime

    model_config = {"from_attributes": True}


class RegistroComportamentoBase(BaseModel):
    """Schema base com os campos de um registro de comportamento."""

    agitacao: int = Field(..., ge=1, le=5, description="Nível de agitação (1-5)")
    sono: int = Field(..., ge=1, le=5, description="Qualidade do sono (1-5)")
    apetite: int = Field(..., ge=1, le=5, description="Nível de apetite (1-5)")
    humor: int = Field(..., ge=1, le=5, description="Humor (1-5)")
    observacoes: str | None = Field(None, description="Observações livres")


class RegistroComportamentoCreate(RegistroComportamentoBase):
    """Schema para criação de um novo registro de comportamento."""

    pass


class RegistroComportamentoResponse(RegistroComportamentoBase):
    """Schema de resposta ao consultar um registro."""

    id: int
    pet_id: int
    data_hora: datetime

    model_config = {"from_attributes": True}


class UltimoRegistroResponse(BaseModel):
    """Schema de resposta para o último registro com estado emocional calculado."""

    id: int
    pet_id: int
    data_hora: datetime
    agitacao: int
    sono: int
    apetite: int
    humor: int
    observacoes: str | None
    estado_emocional: str

    model_config = {"from_attributes": True}


class AnaliseComportamentoResponse(BaseModel):
    """Schema de resposta para a análise de comportamento via IA."""

    pet_id: int
    nome_pet: str
    especie: str
    total_registros: int
    estado_emocional_atual: str
    analise: str
