"""Dados de demonstração do PetMind (tudo fictício).

Cria as contas de visitante (tutor e admin), outros tutores, pets e uma semana
de registros de comportamento, para a análise e o painel admin terem conteúdo.

- Roda sozinho na subida da API quando DEMO_MODE=true e as contas não existem.
- Para recriar do zero: python -m app.seeds.demo_seed --reset
"""

import secrets
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.demo import CONTAS_DEMO
from app.models.pet import Pet, RegistroComportamento
from app.models.user import Usuario
from app.services.auth_service import hash_senha

OUTROS_TUTORES = [
    {"nome": "Camila Rocha", "email": "camila.demo@petmind.dev"},
    {"nome": "Diego Martins", "email": "diego.demo@petmind.dev"},
]
EMAILS_SEED = {c["email"] for c in CONTAS_DEMO.values()} | {
    t["email"] for t in OUTROS_TUTORES
}

# (tutor, nome, espécie, raça, idade, peso, sequência de registros)
# Cada registro: (agitacao, sono, apetite, humor, observação)
Registro = tuple[int, int, int, int, str | None]
PetDemo = tuple[str, str, str, str, int, float, list[Registro]]

PETS: list[PetDemo] = [
    ("usuario", "Thor", "cachorro", "Golden Retriever", 4, 31.5, [
        (3, 4, 5, 5, None), (2, 4, 4, 5, "Passeio longo no parque"),
        (3, 5, 4, 4, None), (4, 3, 4, 4, "EVENTOS:jogo_copa | Muito barulho na rua"),
        (5, 2, 3, 3, "EVENTOS:jogo_copa,torcida_casa | Latiu durante o jogo"),
        (3, 4, 4, 4, None), (2, 5, 5, 5, "Dia tranquilo"),
    ]),
    ("usuario", "Mia", "gato", "Siamês", 2, 4.2, [
        (2, 5, 3, 4, None), (2, 5, 2, 3, "Comeu pouco"), (1, 5, 2, 3, None),
        (2, 4, 2, 2, "EVENTOS:sozinho | Ficou sozinha à tarde"),
        (1, 5, 2, 2, None), (2, 5, 3, 3, None),
    ]),
    ("usuario", "Pipoca", "hamster", "Sírio", 1, 0.15, [
        (4, 3, 4, 4, None), (4, 2, 5, 4, "Correu a noite toda"), (5, 2, 4, 5, None),
        (4, 3, 4, 4, None), (5, 2, 5, 4, None),
    ]),
    ("camila", "Nina", "coelho", "Mini Lop", 3, 1.8, [
        (2, 4, 4, 5, None), (2, 4, 5, 5, None), (1, 5, 4, 4, None), (2, 4, 4, 5, None),
    ]),
    ("diego", "Bolt", "cachorro", "Border Collie", 5, 19.0, [
        (5, 3, 5, 4, "EVENTOS:tempestade | Trovões à noite"),
        (5, 2, 4, 3, None), (4, 3, 4, 4, None),
    ]),
]


def _travar(db: Session) -> None:
    """Impede que duas instâncias criem os dados ao mesmo tempo (Postgres)."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(515151)"))


def _obter_ou_criar(db: Session, nome: str, email: str, papel: str) -> Usuario:
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))
    if usuario:
        return usuario
    usuario = Usuario(
        nome=nome,
        email=email,
        # Senha aleatória: as contas de demo entram pelo /auth/login-demo
        senha_hash=hash_senha(secrets.token_urlsafe(24)),
        papel=papel,
    )
    db.add(usuario)
    db.flush()
    return usuario


def _apagar(db: Session) -> None:
    usuarios = db.scalars(select(Usuario).where(Usuario.email.in_(EMAILS_SEED))).all()
    ids = [u.id for u in usuarios]
    if not ids:
        return
    pets = select(Pet.id).where(Pet.owner_id.in_(ids))
    db.execute(delete(RegistroComportamento).where(RegistroComportamento.pet_id.in_(pets)))
    db.execute(delete(Pet).where(Pet.owner_id.in_(ids)))
    db.execute(delete(Usuario).where(Usuario.id.in_(ids)))
    db.flush()


def popular_demo(db: Session, resetar: bool = False) -> bool:
    """Cria (ou recria) os dados de demonstração. Retorna True se criou."""
    _travar(db)
    if resetar:
        _apagar(db)
    else:
        email_demo = CONTAS_DEMO["usuario"]["email"]
        if db.scalar(select(Usuario).where(Usuario.email == email_demo)):
            return False

    tutores = {
        "usuario": _obter_ou_criar(db, **CONTAS_DEMO["usuario"], papel="usuario"),
        "admin": _obter_ou_criar(db, **CONTAS_DEMO["admin"], papel="admin"),
        "camila": _obter_ou_criar(db, **OUTROS_TUTORES[0], papel="usuario"),
        "diego": _obter_ou_criar(db, **OUTROS_TUTORES[1], papel="usuario"),
    }

    agora = datetime.now(UTC)
    for tutor, nome, especie, raca, idade, peso, registros in PETS:
        pet = Pet(
            owner_id=tutores[tutor].id,
            nome=nome,
            especie=especie,
            raca=raca,
            idade=idade,
            peso=peso,
        )
        db.add(pet)
        db.flush()
        total = len(registros)
        for i, (agitacao, sono, apetite, humor, obs) in enumerate(registros):
            db.add(
                RegistroComportamento(
                    pet_id=pet.id,
                    data_hora=agora - timedelta(days=total - 1 - i, hours=3),
                    agitacao=agitacao,
                    sono=sono,
                    apetite=apetite,
                    humor=humor,
                    observacoes=obs,
                )
            )
    db.commit()
    return True


def main() -> None:
    db = SessionLocal()
    try:
        criado = popular_demo(db, resetar="--reset" in sys.argv)
        print("Dados de demonstração criados." if criado else "Dados já existiam.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
