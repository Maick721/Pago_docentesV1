"""
app/modules/core/models/core.py
Modelos SQLAlchemy 2.0 para el esquema 'core':
  - Persona, Usuario, Rol, UsuarioRol, Auditoria
  - Permiso, Modulo, Unidad, Estudiante, Empleado, CatalogoAcademico
  - AcademicProgram, AcademicPeriod, Campus, AcademicModality, AcademicParallel
"""
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
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
    cedula: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    nombres: Mapped[str | None] = mapped_column(String(100))
    apellidos: Mapped[str | None] = mapped_column(String(100))
    correo: Mapped[str | None] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    # Relaciones inversas
    usuario: Mapped["Usuario | None"] = relationship(back_populates="persona", uselist=False)
    estudiante: Mapped["Estudiante | None"] = relationship(back_populates="persona", uselist=False)
    empleado: Mapped["Empleado | None"] = relationship(back_populates="persona", uselist=False)

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
    nombre_usuario: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    correo_institucional: Mapped[str | None] = mapped_column(String(150), unique=True, index=True)
    contrasena_hash: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[bool | None] = mapped_column(Boolean)
    fecha_creacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
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
    nombre: Mapped[str | None] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

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
    id_usuario: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.usuarios.id_usuario", ondelete="CASCADE")
    )
    id_rol: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.roles.id_rol", ondelete="CASCADE")
    )
    fecha_asignacion: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    estado: Mapped[bool | None] = mapped_column(Boolean)

    # Relaciones
    usuario: Mapped[Usuario | None] = relationship(back_populates="roles")
    rol: Mapped[Rol | None] = relationship(back_populates="asignaciones")

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
    modulo: Mapped[str | None] = mapped_column(String(100))
    accion: Mapped[str | None] = mapped_column(String(100))
    tabla_afectada: Mapped[str | None] = mapped_column(String(100))
    id_registro: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    fecha_hora: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    direccion_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relación
    usuario: Mapped[Usuario | None] = relationship(back_populates="auditorias")

    def __repr__(self) -> str:
        return f"<Auditoria(id={self.id_auditoria}, accion={self.accion}, usuario={self.id_usuario})>"


# ─── Permisos ──────────────────────────────────────────────────────────────────

class Permiso(Base):
    """
    core.permisos — Catálogo de permisos del sistema.
    """
    __tablename__ = "permisos"
    __table_args__ = {"schema": "core"}

    id_permiso: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str | None] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    accion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return f"<Permiso(id={self.id_permiso}, nombre={self.nombre})>"


# ─── Modulos ───────────────────────────────────────────────────────────────────

class Modulo(Base):
    """
    core.modulos — Módulos del sistema institucional.
    """
    __tablename__ = "modulos"
    __table_args__ = {"schema": "core"}

    id_modulo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str | None] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return f"<Modulo(id={self.id_modulo}, nombre={self.nombre})>"


# ─── Unidades ──────────────────────────────────────────────────────────────────

class Unidad(Base):
    """
    core.unidades — Departamentos o unidades institucionales.
    """
    __tablename__ = "unidades"
    __table_args__ = {"schema": "core"}

    id_unidad: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nombre: Mapped[str | None] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    # Relación inversa
    empleados: Mapped[list["Empleado"]] = relationship(back_populates="unidad")

    def __repr__(self) -> str:
        return f"<Unidad(id={self.id_unidad}, nombre={self.nombre})>"


# ─── Estudiantes ───────────────────────────────────────────────────────────────

class Estudiante(Base):
    """
    core.estudiantes — Registro de estudiantes vinculados a una persona.
    """
    __tablename__ = "estudiantes"
    __table_args__ = {"schema": "core"}

    id_estudiante: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_persona: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.personas.id_persona", ondelete="SET NULL"), nullable=True
    )
    codigo_estudiante: Mapped[str | None] = mapped_column(String(50), nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    # Relación
    persona: Mapped["Persona | None"] = relationship(back_populates="estudiante", uselist=False)

    def __repr__(self) -> str:
        return f"<Estudiante(id={self.id_estudiante}, codigo={self.codigo_estudiante})>"


# ─── Empleados ─────────────────────────────────────────────────────────────────

class Empleado(Base):
    """
    core.empleados — Registro de empleados vinculados a persona y unidad.
    """
    __tablename__ = "empleados"
    __table_args__ = {"schema": "core"}

    id_empleado: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_persona: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.personas.id_persona", ondelete="SET NULL"), nullable=True
    )
    id_unidad: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("core.unidades.id_unidad", ondelete="SET NULL"), nullable=True
    )
    codigo_empleado: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fecha_ingreso: Mapped[date | None] = mapped_column(nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    # Relaciones
    persona: Mapped["Persona | None"] = relationship(back_populates="empleado", uselist=False)
    unidad: Mapped["Unidad | None"] = relationship(back_populates="empleados")

    def __repr__(self) -> str:
        return f"<Empleado(id={self.id_empleado}, cargo={self.cargo})>"


# ─── Catalogos Academicos ──────────────────────────────────────────────────────

class CatalogoAcademico(Base):
    """
    core.catalogos_academicos — Catálogos académicos del sistema.
    """
    __tablename__ = "catalogos_academicos"
    __table_args__ = {"schema": "core"}

    id_catalogo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tipo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nombre: Mapped[str | None] = mapped_column(String(150), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool | None] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return f"<CatalogoAcademico(id={self.id_catalogo}, nombre={self.nombre})>"


# ─── Academic Program ──────────────────────────────────────────────────────────

class AcademicProgram(Base):
    """
    core.academic_programs — Programas académicos del ITQ.
    """
    __tablename__ = "academic_programs"
    __table_args__ = {"schema": "core"}

    id_program: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<AcademicProgram(id={self.id_program}, codigo={self.codigo}, nombre={self.nombre})>"


# ─── Academic Period ───────────────────────────────────────────────────────────

class AcademicPeriod(Base):
    """
    core.academic_periods — Periodos académicos (ej. 2026-1, 2026-2).
    """
    __tablename__ = "academic_periods"
    __table_args__ = {"schema": "core"}

    id_period: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<AcademicPeriod(id={self.id_period}, codigo={self.codigo}, nombre={self.nombre})>"


# ─── Campus ────────────────────────────────────────────────────────────────────

class Campus(Base):
    """
    core.campus — Sedes o campus del ITQ.
    """
    __tablename__ = "campus"
    __table_args__ = {"schema": "core"}

    id_campus: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<Campus(id={self.id_campus}, codigo={self.codigo}, nombre={self.nombre})>"


# ─── Academic Modality ─────────────────────────────────────────────────────────

class AcademicModality(Base):
    """
    core.academic_modalities — Modalidades académicas (ej. presencial, semipresencial, virtual).
    """
    __tablename__ = "academic_modalities"
    __table_args__ = {"schema": "core"}

    id_modality: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<AcademicModality(id={self.id_modality}, codigo={self.codigo}, nombre={self.nombre})>"


# ─── Academic Parallel ─────────────────────────────────────────────────────────

class AcademicParallel(Base):
    """
    core.academic_parallels — Paralelos académicos (ej. A, B, C; 1, 2, 3).
    """
    __tablename__ = "academic_parallels"
    __table_args__ = {"schema": "core"}

    id_parallel: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:
        return f"<AcademicParallel(id={self.id_parallel}, codigo={self.codigo}, nombre={self.nombre})>"
