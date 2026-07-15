from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_usuario_atual
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
from app.services.groq_service import (
    GroqService,
    RegistroAnalise,
    get_groq_service,
)

roteador = APIRouter(prefix="/pets", tags=["pets"])


def _buscar_pet_autorizado(db: Session, pet_id: int, usuario: Usuario) -> Pet:
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if pet is None:
        raise HTTPException(status_code=404, detail="Pet não encontrado")
    if usuario.papel != "admin" and pet.owner_id != usuario.id:
        raise HTTPException(status_code=403, detail="Acesso negado a este pet")
    return pet


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
    """Lista pets do usuário autenticado; admin pode ver todos."""
    consulta = db.query(Pet)
    if usuario.papel != "admin":
        consulta = consulta.filter(Pet.owner_id == usuario.id)
    return consulta.all()


@roteador.get("/{pet_id}", response_model=PetResponse)
def buscar_pet(
    pet_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_atual),
) -> Pet:
    """Busca um pet pelo ID."""
    return _buscar_pet_autorizado(db, pet_id, usuario)


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
    _buscar_pet_autorizado(db, pet_id, usuario)

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
    _buscar_pet_autorizado(db, pet_id, usuario)

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
    _buscar_pet_autorizado(db, pet_id, usuario)

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
    service: GroqService = Depends(get_groq_service),
) -> AnaliseComportamentoResponse:
    """Analisa o comportamento do pet usando IA e retorna insights estruturados."""
    pet = _buscar_pet_autorizado(db, pet_id, usuario)

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

    registros_dict: list[RegistroAnalise] = [
        {
            "agitacao": r.agitacao,
            "sono": r.sono,
            "apetite": r.apetite,
            "humor": r.humor,
            "observacoes": r.observacoes,
        }
        for r in registros
    ]

    analise = service.analisar_comportamento(pet.nome, pet.especie, registros_dict)

    return AnaliseComportamentoResponse(
        pet_id=pet_id,
        nome_pet=pet.nome,
        especie=pet.especie,
        total_registros=len(registros),
        estado_predominante=analise["estado_predominante"],
        confianca=analise["confianca"],
        medias=MediasSchema(**analise["medias"]),
        tendencias=TendenciasSchema(**analise["tendencias"]),
        alertas=analise["alertas"],
        diagnostico=analise["diagnostico"],
        recomendacao=analise["recomendacao"],
    )
