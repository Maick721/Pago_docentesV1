"""
app/core/security.py
Utilidades de seguridad: hashing de contraseñas, generación y validación de JWT,
y dependencia FastAPI para obtener el usuario autenticado actual.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

# ─── Contexto de hashing ─────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Esquema Bearer para Swagger UI ──────────────────────────────────────────
bearer_scheme = HTTPBearer()


def _configured_secret_key() -> str:
    if not settings.secret_key or settings.secret_key == "replace_with_a_secure_random_value":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configura SECRET_KEY en el entorno del servidor.",
        )
    return settings.secret_key


# ─── Contraseñas ─────────────────────────────────────────────────────────────
def hash_password(plain_password: str) -> str:
    """Genera el hash bcrypt de una contraseña en texto plano."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que una contraseña en texto plano coincida con su hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT ─────────────────────────────────────────────────────────────────────
def create_access_token(
    subject: str | Any,
    extra_claims: dict | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Genera un JWT firmado con HS256.

    Args:
        subject:      Identificador único del usuario (ej. id_usuario como str).
        extra_claims: Claims adicionales opcionales (rol, nombre, etc.).
        expires_delta: Duración personalizada; si es None, usa la config.

    Returns:
        Token JWT como string.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta

    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, _configured_secret_key(), algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida un JWT.

    Raises:
        HTTPException 401 si el token es inválido o ha expirado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de acceso.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, _configured_secret_key(), algorithms=[settings.algorithm]
        )
        sub: str | None = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


# ─── Dependencia: usuario actual ─────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Dependencia FastAPI que extrae y valida el Bearer token del encabezado
    Authorization, luego carga el usuario desde la base de datos.

    Returns:
        Instancia del modelo Usuario si el token es válido y el usuario está activo.

    Raises:
        HTTPException 401 si el token es inválido o el usuario no existe.
        HTTPException 403 si el usuario está inactivo.
    """
    # Importación local para evitar circular imports
    from app.modules.core.models.core import Usuario

    payload = decode_access_token(credentials.credentials)
    user_id: str = payload.get("sub")

    result = await db.execute(
        select(Usuario).where(Usuario.id_usuario == int(user_id))
    )
    usuario = result.scalar_one_or_none()

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if usuario.estado is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de usuario está inactiva.",
        )

    return usuario
