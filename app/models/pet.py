from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import Usuario


class Pet(Base):
    """Modelo que representa um pet cadastrado no sistema."""

    __tablename__ = "pets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("usuarios.id"), nullable=True, index=True
    )
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    raca: Mapped[str] = mapped_column(String(100), nullable=False)
    especie: Mapped[str] = mapped_column(String(20), nullable=False, default="cachorro")
    idade: Mapped[int] = mapped_column(Integer, nullable=False)
    peso: Mapped[float] = mapped_column(Float, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )

    # Relacionamento com registros de comportamento
    registros: Mapped[list["RegistroComportamento"]] = relationship(
        back_populates="pet", cascade="all, delete-orphan"
    )
    owner: Mapped["Usuario | None"] = relationship(back_populates="pets")


class RegistroComportamento(Base):
    """Registro diário de comportamento de um pet."""

    __tablename__ = "registros_comportamento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pet_id: Mapped[int] = mapped_column(Integer, ForeignKey("pets.id"), nullable=False)
    data_hora: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    agitacao: Mapped[int] = mapped_column(Integer, nullable=False)
    sono: Mapped[int] = mapped_column(Integer, nullable=False)
    apetite: Mapped[int] = mapped_column(Integer, nullable=False)
    humor: Mapped[int] = mapped_column(Integer, nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamento com o pet
    pet: Mapped["Pet"] = relationship(back_populates="registros")
