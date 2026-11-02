
# Importo los tipos de datos y la herramienta de eventos de SQLAlchemy.
from sqlalchemy import BigInteger, Boolean, String, event

# Importo la excepción que voy a utilizar cuando se intente
# modificar un modelo que debe ser de solo lectura.
from sqlalchemy.exc import InvalidRequestError

# Importo las herramientas para definir columnas y sesiones.
from sqlalchemy.orm import Mapped, Session, mapped_column

# Importo Base, que es la clase base de los modelos del proyecto.
from app.core.database import Base


class CoreEmployeeRef(Base):
    # Esta clase representa una referencia de solo lectura
    # a la tabla empleados del esquema core.
    # La utilizo para consultar e identificar al docente.
    __tablename__ = "empleados"

    # Indico que la tabla está en el esquema core.
    # La opción read_only es información descriptiva del modelo.
    __table_args__ = {
        "schema": "core",
        "info": {"read_only": True},
    }

    # Identificador único del empleado.
    # Es la clave primaria de esta tabla.
    id_empleado: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    # Identificador de la persona asociada al empleado.
    # La clave foránea hacia core.personas existe en la BD,
    # aunque no se declara explícitamente en este modelo.
    id_persona: Mapped[int | None] = mapped_column(BigInteger)


class CorePersonRef(Base):
    # Esta clase representa una referencia de solo lectura
    # a la tabla personas del esquema core.
    # Sirve para consultar los datos personales del empleado.
    __tablename__ = "personas"

    # Indico el esquema al que pertenece esta tabla
    # y marco el modelo con información de solo lectura.
    __table_args__ = {
        "schema": "core",
        "info": {"read_only": True},
    }

    # Identificador único de la persona.
    id_persona: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    # Datos personales que se pueden consultar.
    cedula: Mapped[str | None] = mapped_column(String(20))
    nombres: Mapped[str | None] = mapped_column(String(100))
    apellidos: Mapped[str | None] = mapped_column(String(100))
    correo: Mapped[str | None] = mapped_column(String(150))

    @property
    def nombre(self) -> str:
        # Esta propiedad junta los nombres y apellidos
        # para obtener el nombre completo de la persona.
        # Si algún dato está vacío o es None, lo omite.
        # Finalmente, strip() elimina los espacios de los extremos.
        return " ".join(
            value
            for value in (self.nombres, self.apellidos)
            if value
        ).strip()

class CoreAcademicCatalogRef(Base):
    # Esta clase representa una referencia de solo lectura
    # a la tabla catálogo académico del esquema core.
    # La utilizo para consultar e identificar el catálogo académico.
    __tablename__ = "catalogos_academicos"

    # Indico que la tabla está en el esquema core.
    # La opción read_only es información descriptiva del modelo.
    __table_args__ = {
        "schema": "core",
        "info": {"read_only": True},
    }

    # Identificador único del catálogo académico.
    id_catalogo: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    tipo: Mapped[str | None] = mapped_column(String(100))
    nombre: Mapped[str | None] = mapped_column(String(150))
    estado: Mapped[bool | None] = mapped_column(Boolean)


class CoreUserRef(Base):
    __tablename__ = "usuarios"
    __table_args__ = {
        "schema": "core",
        "info": {"read_only": True},
    }

    id_usuario: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nombre_usuario: Mapped[str | None] = mapped_column(String(100))


# Registro un evento que se ejecuta antes de que SQLAlchemy
# guarde los cambios pendientes de una sesión.
@event.listens_for(Session, "before_flush")
def prevent_core_reference_writes(
    session: Session,
    flush_context: object,
    instances: object,
) -> None:
    # Defino las clases que deben ser de solo lectura.
    references = (
        CoreEmployeeRef,
        CorePersonRef,
        CoreAcademicCatalogRef,
        CoreUserRef,
    )

    # Reúno los objetos nuevos, los modificados y los eliminados.
    changed = (*session.new, *session.dirty, *session.deleted)

    # Compruebo si alguno de los objetos pertenece a los modelos
    # de referencia protegidos.
    if any(isinstance(instance, references) for instance in changed):
        # Si encuentro uno, lanzo un error para impedir
        # que esos cambios se guarden mediante esta sesión.
        raise InvalidRequestError(
            "Los modelos de referencia core son de solo lectura."
        )
