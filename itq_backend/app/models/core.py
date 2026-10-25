"""
app/models/core.py
Modelos SQLAlchemy 2.0 para el esquema 'core':
  - Persona, Usuario, Rol, UsuarioRol, Auditoria
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Persona(Base):
    """
    core.personas — Registro maestro de personas físicas del ITQ.
    """
    __tablename__ = "personas"
    __table_args__ = {"schema": "core"}

    id_persona: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    cedula: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    nombres: Mapped[str] = mapped_column(String(150), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")

    # Relación inversa
    usuario: Mapped["Usuario | None"] = relationship(back_populates="persona", uselist=False)

    def __repr__(self) -> str:
        return f"<Persona(id={self.id_persona}, cedula={self.cedula}, nombre={self.nombres} {self.apellidos})>"


class Usuario(Base):
    """
    core.usuarios — Cuentas de acceso al sistema ITQ Conecta.
    """
    __tablename__ = "usuarios"
    __table_args__ = {"schema": "core"}

    id_usuario: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_persona: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.personas.id_persona", ondelete="SET NULL"), nullable=True
    )
    nombre_usuario: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    correo_institucional: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relaciones
    persona: Mapped[Persona | None] = relationship(back_populates="usuario")
    roles: Mapped[list["UsuarioRol"]] = relationship(back_populates="usuario", lazy="selectin")
    auditorias: Mapped[list["Auditoria"]] = relationship(back_populates="usuario")

    def __repr__(self) -> str:
        return f"<Usuario(id={self.id_usuario}, usuario={self.nombre_usuario}, estado={self.estado})>"


class Rol(Base):
    """
    core.roles — Catálogo de roles del sistema.
    """
    __tablename__ = "roles"
    __table_args__ = {"schema": "core"}

    id_rol: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")

    # Relación inversa
    asignaciones: Mapped[list["UsuarioRol"]] = relationship(back_populates="rol")

    def __repr__(self) -> str:
        return f"<Rol(id={self.id_rol}, nombre={self.nombre})>"


class UsuarioRol(Base):
    """
    core.usuario_rol — Asignación M:N de roles a usuarios.
    """
    __tablename__ = "usuario_rol"
    __table_args__ = {"schema": "core"}

    id_usuario_rol: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario", ondelete="CASCADE"), nullable=False
    )
    id_rol: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("core.roles.id_rol", ondelete="CASCADE"), nullable=False
    )
    fecha_asignacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="activo")

    # Relaciones
    usuario: Mapped[Usuario] = relationship(back_populates="roles")
    rol: Mapped[Rol] = relationship(back_populates="asignaciones")

    def __repr__(self) -> str:
        return f"<UsuarioRol(usuario={self.id_usuario}, rol={self.id_rol})>"


class Auditoria(Base):
    """
    core.auditoria — Log de auditoría transversal del sistema.
    """
    __tablename__ = "auditoria"
    __table_args__ = {"schema": "core"}

    id_auditoria: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario", ondelete="SET NULL"), nullable=True
    )
    modulo: Mapped[str] = mapped_column(String(100), nullable=False)
    accion: Mapped[str] = mapped_column(String(200), nullable=False)
    tabla_afectada: Mapped[str | None] = mapped_column(String(150), nullable=True)
    id_registro: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    direccion_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relación
    usuario: Mapped[Usuario | None] = relationship(back_populates="auditorias")

    def __repr__(self) -> str:
        return f"<Auditoria(id={self.id_auditoria}, accion={self.accion}, usuario={self.id_usuario})>"
