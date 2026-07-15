import os
import subprocess
import sys

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

BASE_REVISION = "45b000817676"
USUARIOS_CREATED_REVISION = "a66159c11155"
RESET_TOKEN_REVISION = "c9f9e6a4b201"
PAPEL_REVISION = "d19a93f9c3f2"
HEAD_REVISION = "f4d2b6e8a1c3"
AUTO_MIGRATE_ENV = "PETMIND_AUTO_MIGRATE_ON_STARTUP"


def _run_alembic(*args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], check=True)


def _obter_revisao_atual() -> str | None:
    with engine.connect() as conn:
        try:
            resultado = conn.execute(text("SELECT version_num FROM alembic_version"))
        except SQLAlchemyError:
            return None
        linha = resultado.first()
        return str(linha[0]) if linha else None


def _inferir_revisao_por_schema() -> str | None:
    inspetor = inspect(engine)
    tabelas = set(inspetor.get_table_names())
    if "usuarios" not in tabelas:
        return None

    colunas = {coluna["name"] for coluna in inspetor.get_columns("usuarios")}
    tem_reset_token = {
        "reset_token",
        "reset_token_expires_at",
    }.intersection(colunas)

    if "papel" in colunas:
        if tem_reset_token:
            return PAPEL_REVISION
        return HEAD_REVISION

    if tem_reset_token:
        return RESET_TOKEN_REVISION

    return USUARIOS_CREATED_REVISION


def ensure_schema_ready() -> None:
    revisao_atual = _obter_revisao_atual()
    revisao_inferida = _inferir_revisao_por_schema()

    if revisao_inferida and revisao_atual != revisao_inferida:
        # Corrige drift conhecido do banco do Render antes de aplicar o restante.
        if revisao_atual in {None, BASE_REVISION}:
            print(
                "Ajustando revisão do Alembic para refletir o schema atual:",
                revisao_inferida,
            )
            _run_alembic("stamp", revisao_inferida)
        elif revisao_atual != HEAD_REVISION:
            print(
                "Sincronizando revisão do Alembic com o schema detectado:",
                revisao_inferida,
            )
            _run_alembic("stamp", revisao_inferida)

    _run_alembic("upgrade", "head")


def auto_migrate_enabled() -> bool:
    valor = os.getenv(AUTO_MIGRATE_ENV, "true").strip().lower()
    return valor not in {"0", "false", "no", "off"}


def main() -> None:
    ensure_schema_ready()


if __name__ == "__main__":
    main()
