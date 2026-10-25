"""
app/routers/auth.py
Endpoints de autenticación y gestión de sesión.

  POST /api/v1/auth/login  — Autentica usuario, registra auditoría, retorna JWT.
  GET  /api/v1/auth/me     — Retorna datos del usuario autenticado actual.
"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import registrar_auditoria
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    verify_password,
)
from app.models.core import Usuario
from app.schemas.auth import LoginRequest, TokenResponse, UsuarioMeResponse

router = APIRouter(prefix="/auth", tags=["Autenticación"])


def _build_me_response(usuario: Usuario) -> UsuarioMeResponse:
    """Construye el DTO UsuarioMeResponse desde un modelo Usuario."""
    roles_activos = [
        ur.rol.nombre
        for ur in usuario.roles
        if ur.estado == "activo"
    ]
    return UsuarioMeResponse(
        id_usuario=usuario.id_usuario,
        nombre_usuario=usuario.nombre_usuario,
        correo_institucional=usuario.correo_institucional,
        estado=usuario.estado,
        roles=roles_activos,
    )


# ─── POST /auth/login ────────────────────────────────────────────────────────
@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description=(
        "Autentica las credenciales contra `core.usuarios`. "
        "Retorna un token JWT válido por `ACCESS_TOKEN_EXPIRE_MINUTES` minutos "
        "y registra el evento en `core.auditoria`."
    ),
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    ip_cliente = request.client.host if request.client else "desconocida"

    # Buscar usuario por nombre_usuario O correo_institucional
    result = await db.execute(
        select(Usuario).where(
            or_(
                Usuario.nombre_usuario == body.nombre_usuario,
                Usuario.correo_institucional == body.nombre_usuario,
            )
        )
    )
    usuario: Usuario | None = result.scalar_one_or_none()

    # Validaciones de existencia y contraseña
    if not usuario or not verify_password(body.contrasena, usuario.contrasena_hash):
        # Auditoría de intento fallido (id_usuario=None si no se encontró)
        await registrar_auditoria(
            db=db,
            id_usuario=usuario.id_usuario if usuario else None,
            modulo="AUTH",
            accion="LOGIN_FALLIDO",
            tabla_afectada="core.usuarios",
            id_registro=usuario.id_usuario if usuario else None,
            ip=ip_cliente,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas. Verifique su usuario y contraseña.",
        )

    # Validación de estado
    if usuario.estado != "activo":
        await registrar_auditoria(
            db=db,
            id_usuario=usuario.id_usuario,
            modulo="AUTH",
            accion="LOGIN_CUENTA_INACTIVA",
            tabla_afectada="core.usuarios",
            id_registro=usuario.id_usuario,
            ip=ip_cliente,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"La cuenta está {usuario.estado}. Contacte al administrador.",
        )

    # Generar token JWT
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=usuario.id_usuario,
        extra_claims={
            "nombre_usuario": usuario.nombre_usuario,
            "correo": usuario.correo_institucional,
        },
        expires_delta=expires,
    )

    # Auditoría de login exitoso
    await registrar_auditoria(
        db=db,
        id_usuario=usuario.id_usuario,
        modulo="AUTH",
        accion="LOGIN_EXITOSO",
        tabla_afectada="core.usuarios",
        id_registro=usuario.id_usuario,
        ip=ip_cliente,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=_build_me_response(usuario),
    )


# ─── GET /auth/me ────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UsuarioMeResponse,
    summary="Perfil del usuario autenticado",
    description="Retorna los datos del usuario autenticado a partir del token JWT.",
)
async def get_me(
    usuario: Usuario = Depends(get_current_user),
) -> UsuarioMeResponse:
    return _build_me_response(usuario)
