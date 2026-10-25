"""
app/schemas/core.py
DTOs Pydantic v2 para el módulo Core: Personas, Usuarios y Roles.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ─── Persona ─────────────────────────────────────────────────────────────────

class PersonaBase(BaseModel):
    cedula: str = Field(..., min_length=5, max_length=20, description="Número de cédula.")
    nombres: str = Field(..., min_length=1, max_length=150)
    apellidos: str = Field(..., min_length=1, max_length=150)
    correo: str | None = Field(None, max_length=255)
    telefono: str | None = Field(None, max_length=20)
    estado: str = Field(default="activo", max_length=20)


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
    nombre: str
    descripcion: str | None = None
    estado: str

    model_config = {"from_attributes": True}


# ─── Usuario ─────────────────────────────────────────────────────────────────

class UsuarioBase(BaseModel):
    nombre_usuario: str = Field(..., min_length=3, max_length=100)
    correo_institucional: str = Field(..., max_length=255)
    estado: str = Field(default="activo", max_length=20)


class UsuarioCreate(UsuarioBase):
    """DTO para crear un nuevo usuario."""
    id_persona: int | None = None
    contrasena: str = Field(..., min_length=8, description="Contraseña en texto plano.")


class UsuarioOut(UsuarioBase):
    """DTO de respuesta con datos de un usuario (sin hash de contraseña)."""
    id_usuario: int
    id_persona: int | None = None
    fecha_creacion: datetime
    roles: list[RolOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UsuarioListOut(BaseModel):
    """DTO para listado paginado de usuarios."""
    total: int
    usuarios: list[UsuarioOut]
