from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA
from .modulos import TeacherModule


class HistoryEntry(Base):
    # Esta clase representa el historial de cambios de estado.
    __tablename__ = "historial"

    __table_args__ = (
        # Facilito las consultas del historial por módulo y fecha.
        Index("ix_historial_modulo", "id_modulo", "fecha"),
        {"schema": SCHEMA},
    )

    # Identificador único del registro histórico.
    id_historial: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Módulo al que corresponde el cambio.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )

    # Guardo el estado anterior y el nuevo estado del módulo.
    estado_anterior: Mapped[str | None] = mapped_column(String(50))
    estado_nuevo: Mapped[str] = mapped_column(String(50), nullable=False)

    # Fecha y hora en la que ocurrió el cambio.
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )

    # Explicación del cambio y usuario que lo realizó.
    observacion: Mapped[str | None] = mapped_column(Text)

    # La relación con core.usuarios existe en la BD,
    # pero no se declara como ForeignKey en este modelo.
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )

    # Permito consultar el módulo desde el historial.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="historial"
    )
