from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index,
    SmallInteger, String, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.pagos_docentes.enums import PaymentStatus

from .base import Base, SCHEMA


class TeacherModule(Base):
    # Esta clase representa la tabla de módulos de los docentes.
    __tablename__ = "modulos"

    # Aquí defino reglas e índices adicionales para la tabla.
    __table_args__ = (
        CheckConstraint(
            "estado IN ('EN_CURSO', 'LISTO_PAGO', 'APROBADO', 'PAGADO', 'ANULADO')",
            name="modulos_estado_check",
        ),
        CheckConstraint("fecha_fin >= fecha_inicio", name="ck_modulo_fechas"),
        {"schema": SCHEMA},
    )

    # Identificador principal del módulo, generado automáticamente.
    id_modulo: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # Identificador del docente relacionado con el módulo.
    # La relación con core.empleados existe en la base de datos,
    # pero no se declara aquí como ForeignKey.
    id_docente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.docentes.id_docente"), nullable=False
    )
    id_periodo: Mapped[int] = mapped_column(
        BigInteger, ForeignKey(f"{SCHEMA}.periodos.id_periodo"), nullable=False
    )
    id_carrera: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core.catalogos_academicos.id_catalogo"), nullable=False
    )
    codigo_eva: Mapped[str | None] = mapped_column(String(50))
    nombre_modulo: Mapped[str] = mapped_column(String(200), nullable=False)
    paralelo: Mapped[str | None] = mapped_column(String(50))
    numero_modulo: Mapped[int | None] = mapped_column(SmallInteger)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    listo_para_pago: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    fecha_listo_pago: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    modelo: Mapped[str] = mapped_column(
        String(20), nullable=False, default="CARRERA", server_default=text("'CARRERA'")
    )
    contrato: Mapped[str | None] = mapped_column(String(80))
    datos_modelo: Mapped[dict | None] = mapped_column(JSONB)
    estado: Mapped[str] = mapped_column(
        String(30), nullable=False, default=PaymentStatus.EN_CURSO.value,
        server_default=text("'EN_CURSO'"),
    )
    id_usuario_registro: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario")
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )

    # Relaciones para consultar aprobaciones, pagos, alertas
    # e historial asociados con este módulo.
    aprobaciones: Mapped[list["Approval"]] = relationship(
        back_populates="modulo"
    )
    pagos: Mapped[list["Payment"]] = relationship(
        back_populates="modulo"
    )
    alertas: Mapped[list["Alert"]] = relationship(
        back_populates="modulo"
    )
    historial: Mapped[list["HistoryEntry"]] = relationship(
        back_populates="modulo"
    )
