from datetime import datetime

from sqlalchemy import (
    BigInteger, CheckConstraint, DateTime, ForeignKey, Index, Integer, String,
    Text, UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SCHEMA


class PaymentConfig(Base):
    # Esta clase representa la configuración general de los pagos.
    __tablename__ = "configuracion_umbral"
    __table_args__ = (
        Index(
            "uq_umbral_activo", "activo", unique=True,
            postgresql_where=text("activo"),
        ),
        CheckConstraint("valor > 0", name="configuracion_umbral_valor_check"),
        CheckConstraint(
            "unidad IN ('DIAS', 'MESES')",
            name="configuracion_umbral_unidad_check",
        ),
        {"schema": SCHEMA},
    )

    id_configuracion: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    valor: Mapped[int] = mapped_column(Integer, nullable=False)
    unidad: Mapped[str] = mapped_column(String(10), nullable=False)
    correo_notificacion: Mapped[str | None] = mapped_column(String(150))
    activo: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )


class ProcessedEmail(Base):
    __tablename__ = "correos_procesados"

    __table_args__ = (
        Index("ix_correos_estado", "estado"),
        UniqueConstraint(
            "message_id", name="correos_procesados_message_id_key"
        ),
        CheckConstraint(
            "estado IN ('PENDIENTE', 'PROCESADO', 'FALLIDO', 'REVISADO_MANUAL')",
            name="correos_procesados_estado_check",
        ),
        {"schema": SCHEMA},
    )

    id_correo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False)
    remitente: Mapped[str | None] = mapped_column(String(150))
    asunto: Mapped[str | None] = mapped_column(String(300))
    fecha_recepcion: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    fecha_procesamiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDIENTE", server_default=text("'PENDIENTE'")
    )
    detalle_error: Mapped[str | None] = mapped_column(Text)
    id_modulo: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.modulos.id_modulo")
    )
    id_usuario_revision: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )
    fecha_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
