"""
app/modules/core/schemas/core.py
DTOs Pydantic v2 para el módulo Core: Personas, Usuarios, Roles, catálogos académicos y más.
"""
from datetime import date, datetime

from pydantic import BaseModel, Field


# ─── Persona ─────────────────────────────────────────────────────────────────

class PersonaBase(BaseModel):
    cedula: str | None = Field(None, min_length=5, max_length=20, description="Número de cédula.")
    nombres: str | None = Field(None, min_length=1, max_length=100)
    apellidos: str | None = Field(None, min_length=1, max_length=100)
    correo: str | None = Field(None, max_length=150)
    telefono: str | None = Field(None, max_length=20)
    estado: bool | None = True


class PersonaCreate(PersonaBase):
    """DTO para crear una nueva persona."""
    pass


class PersonaOut(PersonaBase):
    """DTO de respuesta con datos de una persona."""
    id_persona: int

    model_config = {"from_attributes": True}


# ─── Rol ─────────────────────────────────────────────────────────────────────

class RolOut(BaseModel):
    """DTO de respuesta con datos de un rol."""
    id_rol: int
    nombre: str | None
    descripcion: str | None = None
    estado: bool | None

    model_config = {"from_attributes": True}


# ─── Usuario ─────────────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=100)
    correo_institucional: str = Field(..., max_length=150)
    estado: bool = True


class UsuarioCreate(UsuarioBase):
    """DTO para crear un nuevo usuario."""
    id_persona: int | None = None
    contrasena: str = Field(..., min_length=8, description="Contraseña en texto plano.")


class UsuarioRolOut(BaseModel):
    """DTO de asignación usuario-rol con el rol anidado."""
    id_usuario_rol: int
    id_usuario: int | None
    id_rol: int | None
    fecha_asignacion: datetime | None
    estado: bool | None
    rol: RolOut | None

    model_config = {"from_attributes": True}


class UsuarioOut(UsuarioBase):
    """DTO de respuesta con datos de un usuario (sin hash de contraseña)."""
    id_usuario: int
    nombre_usuario: str | None
    correo_institucional: str | None
    estado: bool | None
    id_persona: int | None = None
    fecha_creacion: datetime | None
    roles: list[UsuarioRolOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UsuarioListOut(BaseModel):
    """DTO para listado paginado de usuarios."""
    total: int
    usuarios: list[UsuarioOut]


# ─── Permiso ───────────────────────────────────────────────────────────────────

class PermisoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=5000)
    accion: str | None = Field(None, max_length=100)
    estado: bool = Field(default=True)


class PermisoCreate(PermisoBase):
    """DTO para crear un nuevo permiso."""
    pass


class PermisoOut(PermisoBase):
    """DTO de respuesta de un permiso."""
    id_permiso: int

    model_config = {"from_attributes": True}


# ─── Modulo ────────────────────────────────────────────────────────────────────

class ModuloBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class ModuloCreate(ModuloBase):
    """DTO para crear un nuevo módulo."""
    pass


class ModuloOut(ModuloBase):
    """DTO de respuesta de un módulo."""
    id_modulo: int

    model_config = {"from_attributes": True}


# ─── Unidad ────────────────────────────────────────────────────────────────────

class UnidadBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class UnidadCreate(UnidadBase):
    """DTO para crear una nueva unidad."""
    pass


class UnidadOut(UnidadBase):
    """DTO de respuesta de una unidad."""
    id_unidad: int

    model_config = {"from_attributes": True}


# ─── Estudiante ────────────────────────────────────────────────────────────────

class EstudianteBase(BaseModel):
    id_persona: int | None = None
    codigo_estudiante: str | None = Field(None, max_length=50)
    estado: bool = Field(default=True)


class EstudianteCreate(EstudianteBase):
    """DTO para crear un nuevo estudiante."""
    pass


class EstudianteOut(EstudianteBase):
    """DTO de respuesta de un estudiante."""
    id_estudiante: int

    model_config = {"from_attributes": True}


# ─── Empleado ──────────────────────────────────────────────────────────────────

class EmpleadoBase(BaseModel):
    id_persona: int | None = None
    id_unidad: int | None = None
    codigo_empleado: str | None = Field(None, max_length=50)
    cargo: str | None = Field(None, max_length=100)
    fecha_ingreso: date | None = None
    estado: bool = Field(default=True)


class EmpleadoCreate(EmpleadoBase):
    """DTO para crear un nuevo empleado."""
    pass


class EmpleadoOut(EmpleadoBase):
    """DTO de respuesta de un empleado."""
    id_empleado: int
    estado: bool | None

    model_config = {"from_attributes": True}


# ─── Catalogo Academico ────────────────────────────────────────────────────────

class CatalogoAcademicoBase(BaseModel):
    tipo: str | None = Field(None, max_length=100)
    codigo: str | None = Field(None, max_length=50)
    nombre: str | None = Field(None, max_length=150)
    descripcion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class CatalogoAcademicoCreate(CatalogoAcademicoBase):
    """DTO para crear un nuevo catálogo académico."""
    pass


class CatalogoAcademicoOut(CatalogoAcademicoBase):
    """DTO de respuesta de un catálogo académico."""
    id_catalogo: int

    model_config = {"from_attributes": True}


# ─── Academic Program ──────────────────────────────────────────────────────────

class AcademicProgramBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código del programa académico.")
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class AcademicProgramCreate(AcademicProgramBase):
    """DTO para crear un programa académico."""
    pass


class AcademicProgramOut(AcademicProgramBase):
    """DTO de respuesta de un programa académico."""
    id_program: int

    model_config = {"from_attributes": True}


# ─── Academic Period ───────────────────────────────────────────────────────────

class AcademicPeriodBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código del periodo académico.")
    nombre: str = Field(..., min_length=1, max_length=100)
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    estado: bool = Field(default=True)


class AcademicPeriodCreate(AcademicPeriodBase):
    """DTO para crear un periodo académico."""
    pass


class AcademicPeriodOut(AcademicPeriodBase):
    """DTO de respuesta de un periodo académico."""
    id_period: int

    model_config = {"from_attributes": True}


# ─── Campus ────────────────────────────────────────────────────────────────────

class CampusBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código del campus.")
    nombre: str = Field(..., min_length=1, max_length=200)
    direccion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class CampusCreate(CampusBase):
    """DTO para crear un campus."""
    pass


class CampusOut(CampusBase):
    """DTO de respuesta de un campus."""
    id_campus: int

    model_config = {"from_attributes": True}


# ─── Academic Modality ─────────────────────────────────────────────────────────

class AcademicModalityBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código de la modalidad académica.")
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class AcademicModalityCreate(AcademicModalityBase):
    """DTO para crear una modalidad académica."""
    pass


class AcademicModalityOut(AcademicModalityBase):
    """DTO de respuesta de una modalidad académica."""
    id_modality: int

    model_config = {"from_attributes": True}


# ─── Academic Parallel ─────────────────────────────────────────────────────────

class AcademicParallelBase(BaseModel):
    codigo: str = Field(..., min_length=1, max_length=50, description="Código del paralelo académico.")
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = Field(None, max_length=5000)
    estado: bool = Field(default=True)


class AcademicParallelCreate(AcademicParallelBase):
    """DTO para crear un paralelo académico."""
    pass


class AcademicParallelOut(AcademicParallelBase):
    """DTO de respuesta de un paralelo académico."""
    id_parallel: int

    model_config = {"from_attributes": True}
