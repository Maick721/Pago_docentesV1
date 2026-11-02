"""
app/schemas/auth.py
DTOs Pydantic v2 para autenticación y tokens JWT.
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Cuerpo de la solicitud de login."""
    nombre_usuario: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nombre de usuario o correo institucional.",
        examples=["jperez"],
    )
    contrasena: str = Field(
        ...,
        min_length=6,
        description="Contraseña del usuario.",
        examples=["Mi$Contrasena123"],
    )


class TokenResponse(BaseModel):
    """Respuesta exitosa de autenticación con el token JWT."""
    access_token: str = Field(..., description="Token JWT de acceso.")
    token_type: str = Field(default="bearer", description="Tipo de token.")
    expires_in: int = Field(..., description="Segundos hasta la expiración del token.")
    usuario: "UsuarioMeResponse"


class UsuarioMeResponse(BaseModel):
    """Datos del usuario autenticado retornados en /auth/me y en el login."""
    id_usuario: int
    nombre_usuario: str | None
    correo_institucional: str | None
    estado: bool | None
    roles: list[str] = Field(default_factory=list, description="Nombres de roles activos del usuario.")

    model_config = {"from_attributes": True}


# Resuelve la referencia circular dentro del mismo módulo
TokenResponse.model_rebuild()
