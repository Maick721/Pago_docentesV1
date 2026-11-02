from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer,
    String, Text, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, SCHEMA
from .modulos import TeacherModule


class Alert(Base):
    # Esta clase representa las alertas del módulo de pagos.
    __tablename__ = "alertas"

    __table_args__ = (
        Index(
            "uq_alerta_activa", "id_modulo", unique=True,
            postgresql_where=text("estado = 'ACTIVA'"),
        ),
        CheckConstraint("tipo = 'PAGO_ATRASADO'", name="alertas_tipo_check"),
        CheckConstraint(
            "estado IN ('ACTIVA', 'RESUELTA')", name="alertas_estado_check"
        ),
        {"schema": SCHEMA},
    )

    # Identificador único de la alerta.
    id_alerta: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Módulo que generó la alerta.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{SCHEMA}.modulos.id_modulo"),
        nullable=False,
    )
    id_configuracion: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.configuracion_umbral.id_configuracion")
    )

    # Fecha y hora en la que se registró la alerta.
    fecha_alerta: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )

    # Tipo de alerta, por ejemplo, pago atrasado.
    tipo: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PAGO_ATRASADO", server_default=text("'PAGO_ATRASADO'")
    )

    # Mensaje que explica el motivo de la alerta.
    mensaje: Mapped[str | None] = mapped_column(Text)

    # Estado actual de la alerta.
    dias_atraso: Mapped[int | None] = mapped_column(Integer)
    correo_enviado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    fecha_envio_correo: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ACTIVA", server_default=text("'ACTIVA'")
    )
    fecha_resolucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    # Relación que permite consultar el módulo de la alerta.
    modulo: Mapped[TeacherModule | None] = relationship(
        back_populates="alertas"
    )
