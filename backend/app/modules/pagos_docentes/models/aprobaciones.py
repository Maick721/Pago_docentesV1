from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text,
    UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA
from .modulos import TeacherModule


class Approval(Base):
    # Esta clase representa la tabla de aprobaciones.
    __tablename__ = "aprobaciones"

    __table_args__ = (
        Index("ix_aprobaciones_fecha", "fecha_aprobacion"),
        UniqueConstraint("id_modulo", name="aprobaciones_id_modulo_key"),
        CheckConstraint(
            "estado IN ('VIGENTE', 'ANULADA')", name="aprobaciones_estado_check"
        ),
        CheckConstraint(
            "origen IN ('CORREO', 'MANUAL')", name="aprobaciones_origen_check"
        ),
        {"schema": SCHEMA},
    )

    # Identificador único de cada aprobación.
    id_aprobacion: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Relaciono la aprobación con el módulo correspondiente.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )

    # Registro cuándo se realizó la aprobación.
    fecha_aprobacion: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)

    # Indico de dónde provino la aprobación.
    origen: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MANUAL", server_default=text("'MANUAL'")
    )
    id_correo: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.correos_procesados.id_correo")
    )

    # Estado de la aprobación.
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="VIGENTE", server_default=text("'VIGENTE'")
    )
    observacion: Mapped[str | None] = mapped_column(Text)

    # Usuario que realizó la aprobación.
    # La relación con core.usuarios existe en la base de datos,
    # pero no se declara como ForeignKey en este modelo.
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )

    # Permito acceder al módulo desde una aprobación.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="aprobaciones"
    )
