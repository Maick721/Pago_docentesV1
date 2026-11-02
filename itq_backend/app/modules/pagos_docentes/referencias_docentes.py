from sqlalchemy import BigInteger, Boolean, String, event
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.database import Base
from app.models.core import Persona


class CoreEmployeeRef(Base):
    """Referencia de solo lectura a core.empleados para consultar al docente."""

    __tablename__ = "empleados"
    __table_args__ = {"schema": "core", "info": {"read_only": True}}

    id_empleado: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # La FK a core.personas(id_persona) existe en la BD.
    id_persona: Mapped[int | None] = mapped_column(BigInteger)


CorePersonRef = Persona


class CoreAcademicCatalogRef(Base):
    """Referencia de solo lectura al catálogo de carreras de core."""

    __tablename__ = "catalogos_academicos"
    __table_args__ = {"schema": "core", "info": {"read_only": True}}

    id_catalogo: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tipo: Mapped[str | None] = mapped_column(String(100))
    nombre: Mapped[str | None] = mapped_column(String(150))
    estado: Mapped[bool | None] = mapped_column(Boolean)


@event.listens_for(Session, "before_flush")
def prevent_core_reference_writes(
    session: Session,
    flush_context: object,
    instances: object,
) -> None:
    """Impide escribir por accidente en la referencia local de empleados."""
    changed = (*session.new, *session.dirty, *session.deleted)
    read_only_models = (CoreEmployeeRef, CoreAcademicCatalogRef)
    if any(isinstance(instance, read_only_models) for instance in changed):
        raise InvalidRequestError("Los modelos de referencia core son de solo lectura.")
