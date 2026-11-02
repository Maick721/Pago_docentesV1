"""Clases de consulta de solo lectura para tablas administradas por Core."""

from sqlalchemy import event
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.modules.core.models.core import (
    CatalogoAcademico,
    Empleado,
    Persona,
    Usuario,
)


class CoreEmployeeRef(Base):
    __table__ = Empleado.__table__


class CorePersonRef(Base):
    __table__ = Persona.__table__


class CoreAcademicCatalogRef(Base):
    __table__ = CatalogoAcademico.__table__


class CoreUserRef(Base):
    __table__ = Usuario.__table__


@event.listens_for(Session, "before_flush")
def prevent_core_reference_writes(
    session: Session,
    _flush_context: object,
    _instances: object,
) -> None:
    references = (
        CoreEmployeeRef,
        CorePersonRef,
        CoreAcademicCatalogRef,
        CoreUserRef,
    )
    changed = (*session.new, *session.dirty, *session.deleted)
    if any(isinstance(instance, references) for instance in changed):
        raise InvalidRequestError(
            "Los modelos de referencia core son de solo lectura."
        )
