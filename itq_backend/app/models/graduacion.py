"""
app/models/graduacion.py
Modelos SQLAlchemy 2.0 para el módulo de Graduación y Titulación:
  Evento, Butaca, Pase, QR
"""
from datetime import datetime, time

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Evento(Base):
    """
    graduacion.eventos — Eventos de ceremonia de graduación del ITQ.
    """
    __tablename__ = "eventos"
    __table_args__ = {"schema": "graduacion"}

    id_evento: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hora: Mapped[time | None] = mapped_column(Time, nullable=True)
    sede: Mapped[str | None] = mapped_column(String(300), nullable=True)
    jornada: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aforo: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="activo")

    # Relaciones
    butacas: Mapped[list["Butaca"]] = relationship(back_populates="evento")
    pases: Mapped[list["Pase"]] = relationship(back_populates="evento")

    def __repr__(self) -> str:
        return f"<Evento(id={self.id_evento}, nombre={self.nombre}, estado={self.estado})>"


class Butaca(Base):
    """
    graduacion.butacas — Asientos disponibles por evento de graduación.
    """
    __tablename__ = "butacas"
    __table_args__ = {"schema": "graduacion"}

    id_butaca: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_evento: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("graduacion.eventos.id_evento", ondelete="CASCADE"), nullable=False
    )
    fila: Mapped[str] = mapped_column(String(10), nullable=False)
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="disponible")
    # Estados posibles: disponible, asignada, ocupada, reservada

    # Relaciones
    evento: Mapped[Evento] = relationship(back_populates="butacas")
    pase: Mapped["Pase | None"] = relationship(back_populates="butaca", uselist=False)

    def __repr__(self) -> str:
        return f"<Butaca(id={self.id_butaca}, evento={self.id_evento}, fila={self.fila}, num={self.numero})>"


class Pase(Base):
    """
    graduacion.pases — Pases de acceso emitidos para la ceremonia de graduación.
    Cada pase puede ser de tipo 'graduando' o 'invitado'.
    """
    __tablename__ = "pases"
    __table_args__ = {"schema": "graduacion"}

    id_pase: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_evento: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("graduacion.eventos.id_evento", ondelete="RESTRICT"), nullable=False
    )
    id_estudiante: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.personas.id_persona", ondelete="SET NULL"), nullable=True
    )
    id_butaca: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("graduacion.butacas.id_butaca", ondelete="SET NULL"), nullable=True
    )
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    # Tipos: graduando, invitado
    fecha_emision: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="emitido")
    # Estados: emitido, utilizado, cancelado, vencido

    # Datos del invitado (cuando tipo == 'invitado')
    cedula_invitado: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nombre_invitado: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Relaciones
    evento: Mapped[Evento] = relationship(back_populates="pases")
    butaca: Mapped[Butaca | None] = relationship(back_populates="pase")
    estudiante: Mapped["Persona | None"] = relationship(foreign_keys=[id_estudiante])
    qr: Mapped["QR | None"] = relationship(back_populates="pase", uselist=False)

    def __repr__(self) -> str:
        return f"<Pase(id={self.id_pase}, tipo={self.tipo}, estado={self.estado})>"


class QR(Base):
    """
    graduacion.qr — Códigos QR generados para cada pase de graduación.
    Incluye control de uso y auditoría de validación.
    """
    __tablename__ = "qr"
    __table_args__ = {"schema": "graduacion"}

    id_qr: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_pase: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("graduacion.pases.id_pase", ondelete="CASCADE"), nullable=False, unique=True
    )
    codigo: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    fecha_generacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fecha_uso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    utilizado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    id_usuario_valida: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario", ondelete="SET NULL"), nullable=True
    )
    dispositivo_info: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relaciones
    pase: Mapped[Pase] = relationship(back_populates="qr")
    usuario_valida: Mapped["Usuario | None"] = relationship(foreign_keys=[id_usuario_valida])

    def __repr__(self) -> str:
        return f"<QR(id={self.id_qr}, codigo={self.codigo[:20]}..., utilizado={self.utilizado})>"


# Importación necesaria para las relaciones forward-reference
from app.models.core import Persona, Usuario  # noqa: E402
