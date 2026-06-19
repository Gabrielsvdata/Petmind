import os
from collections.abc import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Carrega variáveis de ambiente do .env
load_dotenv()

# URL do banco de dados PostgreSQL
# Render fornece "postgres://" — SQLAlchemy exige "postgresql://"
_raw_url = os.getenv(
    "DATABASE_URL",
    "postgresql://petmind:petmind123@localhost:5432/petmind",
)
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos SQLAlchemy."""

    pass


def get_db() -> Iterator[Session]:
    """Dependency que fornece uma sessão de banco de dados por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
