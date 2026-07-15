from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.admin import get_usuario_admin
from app.models.pet import Pet, RegistroComportamento
from app.models.user import Usuario
from app.schemas.admin import (
    AlterarPapelRequest,
    EstatisticasResponse,
    UsuarioAdminResponse,
    UsuarioDetalheAdminResponse,
)
from app.schemas.pet import PetResponse
from app.services.emocao_service import calcular_estado_emocional

roteador = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_usuario_admin)],
)


def _resumo_usuario(db: Session, usuario: Usuario) -> UsuarioAdminResponse:
    total_pets = db.query(Pet).filter(Pet.owner_id == usuario.id).count()
    total_registros = (
        db.query(RegistroComportamento)
        .join(Pet, RegistroComportamento.pet_id == Pet.id)
        .filter(Pet.owner_id == usuario.id)
        .count()
    )
    ultimo_acesso = (
        db.query(func.max(RegistroComportamento.data_hora))
        .join(Pet, RegistroComportamento.pet_id == Pet.id)
        .filter(Pet.owner_id == usuario.id)
        .scalar()
    )

    return UsuarioAdminResponse(
        id=usuario.id,
        nome=usuario.nome,
        email=usuario.email,
        papel=usuario.papel,
        criado_em=usuario.criado_em,
        total_pets=total_pets,
        total_registros=total_registros,
        ultimo_acesso=ultimo_acesso,
    )


@roteador.get("/usuarios", response_model=list[UsuarioAdminResponse])
def listar_usuarios(
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[UsuarioAdminResponse]:
    offset = (pagina - 1) * limite
    usuarios = (
        db.query(Usuario)
        .order_by(Usuario.id.asc())
        .offset(offset)
        .limit(limite)
        .all()
    )
    return [_resumo_usuario(db, usuario) for usuario in usuarios]


@roteador.get("/usuarios/{usuario_id}", response_model=UsuarioDetalheAdminResponse)
def detalhar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
) -> UsuarioDetalheAdminResponse:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    resumo = _resumo_usuario(db, usuario)
    pets = db.query(Pet).filter(Pet.owner_id == usuario.id).order_by(Pet.id.asc()).all()
    return UsuarioDetalheAdminResponse(
        **resumo.model_dump(),
        pets=[PetResponse.model_validate(pet) for pet in pets],
    )


@roteador.put("/usuarios/{usuario_id}/papel")
def alterar_papel(
    usuario_id: int,
    request: AlterarPapelRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    usuario.papel = request.papel
    db.commit()
    return {"mensagem": f"Papel atualizado para '{request.papel}'"}


@roteador.delete("/usuarios/{usuario_id}")
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    db.delete(usuario)
    db.commit()
    return {"mensagem": "Usuário removido com sucesso"}


@roteador.get("/pets", response_model=list[PetResponse])
def listar_todos_pets(
    db: Session = Depends(get_db),
) -> list[Pet]:
    return db.query(Pet).order_by(Pet.id.asc()).all()


@roteador.delete("/pets/{pet_id}")
def deletar_pet_admin(
    pet_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado")
    db.delete(pet)
    db.commit()
    return {"mensagem": "Pet removido com sucesso"}


@roteador.get("/estatisticas", response_model=EstatisticasResponse)
def estatisticas(
    db: Session = Depends(get_db),
) -> EstatisticasResponse:
    total_usuarios = db.query(Usuario).count()
    total_pets = db.query(Pet).count()
    total_registros = db.query(RegistroComportamento).count()

    pets_por_especie: dict[str, int] = {}
    for especie, quantidade in (
        db.query(Pet.especie, func.count(Pet.id)).group_by(Pet.especie).all()
    ):
        pets_por_especie[str(especie)] = int(quantidade)

    estados_mais_comuns: dict[str, int] = {}
    registros = db.query(RegistroComportamento).all()
    for registro in registros:
        estado = calcular_estado_emocional(
            registro.agitacao,
            registro.sono,
            registro.apetite,
            registro.humor,
        )
        estados_mais_comuns[estado] = estados_mais_comuns.get(estado, 0) + 1

    semana_atras = datetime.now(UTC) - timedelta(days=7)
    registros_semana = (
        db.query(RegistroComportamento)
        .filter(RegistroComportamento.data_hora >= semana_atras)
        .count()
    )
    usuarios_ativos = (
        db.query(func.count(func.distinct(Pet.owner_id)))
        .join(RegistroComportamento, RegistroComportamento.pet_id == Pet.id)
        .filter(
            Pet.owner_id.isnot(None),
            RegistroComportamento.data_hora >= semana_atras,
        )
        .scalar()
    )

    return EstatisticasResponse(
        total_usuarios=total_usuarios,
        total_pets=total_pets,
        total_registros=total_registros,
        pets_por_especie=pets_por_especie,
        estados_mais_comuns=estados_mais_comuns,
        usuarios_ativos=int(usuarios_ativos or 0),
        registros_ultima_semana=registros_semana,
    )
