from datetime import date, datetime

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, SCHEMA


class Teacher(Base):
    __tablename__ = "docentes"
    __table_args__ = (
        UniqueConstraint("id_empleado", name="docentes_id_empleado_key"),
        {"schema": SCHEMA},
    )

    id_docente: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_empleado: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core.empleados.id_empleado"), nullable=False
    )
    correo_notificacion: Mapped[str | None] = mapped_column(String(150))
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=text("now()")
    )
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


class AcademicPeriod(Base):
    __tablename__ = "periodos"
    __table_args__ = (
        UniqueConstraint("nombre", name="periodos_nombre_key"),
        {"schema": SCHEMA},
    )

    id_periodo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_inicio: Mapped[date | None] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
