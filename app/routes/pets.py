from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pet import Pet, RegistroComportamento
from app.models.user import Usuario
from app.schemas.pet import (
    AnaliseComportamentoResponse,
    MediasSchema,
    PetCreate,
    PetResponse,
    RegistroComportamentoCreate,
    RegistroComportamentoResponse,
    TendenciasSchema,
    UltimoRegistroResponse,
)
from app.services.emocao_service import calcular_estado_emocional
from app.services.auth_service import get_usuario_atual
from app.services.groq_service import GroqService

roteador = APIRouter(prefix="/pets", tags=["pets"])


# ── Pets ──────────────────────────────────────────────────────────────────────


@roteador.post("/", response_model=PetResponse, status_code=201)
def cadastrar_pet(
    pet: PetCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> Pet:
    """Cadastra um novo pet no sistema."""
    novo_pet = Pet(**pet.model_dump(), owner_id=usuario.id)
    db.add(novo_pet)
    db.commit()
    db.refresh(novo_pet)
    return novo_pet


@roteador.get("/", response_model=list[PetResponse])
def listar_pets(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> list[Pet]:
    """Lista todos os pets cadastrados."""
    return db.query(Pet).filter(Pet.owner_id == usuario.id).all()


@roteador.get("/{pet_id}", response_model=PetResponse)
def buscar_pet(
    pet_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> Pet:
    """Busca um pet pelo ID."""
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == usuario.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")
    return pet


# ── Registros de Comportamento ────────────────────────────────────────────────


@roteador.post(
    "/{pet_id}/registros", response_model=RegistroComportamentoResponse, status_code=201
)
def adicionar_registro(
    pet_id: int,
    registro: RegistroComportamentoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> RegistroComportamento:
    """Adiciona um registro de comportamento diário para um pet."""
    # Verifica se o pet existe
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == usuario.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")

    novo_registro = RegistroComportamento(**registro.model_dump(), pet_id=pet_id)
    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)
    return novo_registro


@roteador.get("/{pet_id}/registros", response_model=list[RegistroComportamentoResponse])
def listar_registros(
    pet_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> list[RegistroComportamento]:
    """Lista todos os registros de comportamento de um pet."""
    # Verifica se o pet existe
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == usuario.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")

    return (
        db.query(RegistroComportamento)
        .filter(RegistroComportamento.pet_id == pet_id)
        .all()
    )


@roteador.get("/{pet_id}/registros/ultimo", response_model=UltimoRegistroResponse)
def ultimo_registro(
    pet_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> UltimoRegistroResponse:
    """Retorna o registro mais recente do pet com o estado emocional calculado."""
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == usuario.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")

    registro = (
        db.query(RegistroComportamento)
        .filter(RegistroComportamento.pet_id == pet_id)
        .order_by(RegistroComportamento.data_hora.desc())
        .first()
    )
    if registro is None:
        raise HTTPException(
            status_code=400, detail="Nenhum registro encontrado para este pet"
        )

    estado = calcular_estado_emocional(
        agitacao=registro.agitacao,
        sono=registro.sono,
        apetite=registro.apetite,
        humor=registro.humor,
    )

    return UltimoRegistroResponse(
        id=registro.id,
        pet_id=registro.pet_id,
        data_hora=registro.data_hora,
        agitacao=registro.agitacao,
        sono=registro.sono,
        apetite=registro.apetite,
        humor=registro.humor,
        observacoes=registro.observacoes,
        estado_emocional=estado,
    )


@roteador.post("/{pet_id}/analisar", response_model=AnaliseComportamentoResponse)
def analisar_comportamento(
    pet_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> AnaliseComportamentoResponse:
    """Analisa o comportamento do pet usando IA e retorna insights estruturados."""
    pet = db.query(Pet).filter(Pet.id == pet_id, Pet.owner_id == usuario.id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")

    registros = (
        db.query(RegistroComportamento)
        .filter(RegistroComportamento.pet_id == pet_id)
        .order_by(RegistroComportamento.data_hora.asc())
        .all()
    )
    if not registros:
        raise HTTPException(
            status_code=400, detail="Nenhum registro encontrado para este pet"
        )

    registros_dict: list[dict[str, object]] = [
        {
            "agitacao": r.agitacao,
            "sono": r.sono,
            "apetite": r.apetite,
            "humor": r.humor,
            "observacoes": r.observacoes,
        }
        for r in registros
    ]

    service = GroqService()
    analise = service.analisar_comportamento(pet.nome, pet.especie, registros_dict)

    return AnaliseComportamentoResponse(
        pet_id=pet_id,
        nome_pet=pet.nome,
        especie=pet.especie,
        total_registros=len(registros),
        estado_predominante=str(analise.get("estado_predominante", "feliz")),
        confianca=int(analise.get("confianca", 70)),  # type: ignore[arg-type]
        medias=MediasSchema(**analise.get("medias", {})),  # type: ignore[arg-type]
        tendencias=TendenciasSchema(**analise.get("tendencias", {})),  # type: ignore[arg-type]
        alertas=list(analise.get("alertas", [])),  # type: ignore[arg-type]
        diagnostico=str(analise.get("diagnostico", "")),
        recomendacao=str(analise.get("recomendacao", "")),
    )
