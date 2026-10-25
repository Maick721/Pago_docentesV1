"""
app/routers/core.py
Endpoints del módulo institucional Core.

  GET /api/v1/core/personas/buscar  — Búsqueda de persona por número de cédula.
  GET /api/v1/core/usuarios         — Listado paginado de usuarios del sistema.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.core import Persona, Usuario
from app.schemas.core import PersonaOut, UsuarioListOut, UsuarioOut

router = APIRouter(prefix="/core", tags=["Core Institucional"])


# ─── GET /core/personas/buscar ───────────────────────────────────────────────
@router.get(
    "/personas/buscar",
    response_model=PersonaOut,
    summary="Buscar persona por cédula",
    description=(
        "Busca un registro en `core.personas` por número de cédula exacta. "
        "Requiere autenticación JWT activa."
    ),
)
async def buscar_persona_por_cedula(
    cedula: str = Query(
        ...,
        min_length=5,
        max_length=20,
        description="Número de cédula a buscar.",
        examples=["0912345678"],
    ),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),  # Proteger el endpoint
) -> PersonaOut:
    result = await db.execute(
        select(Persona).where(Persona.cedula == cedula.strip())
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ninguna persona con cédula '{cedula}'.",
        )

    return PersonaOut.model_validate(persona)


# ─── GET /core/usuarios ──────────────────────────────────────────────────────
@router.get(
    "/usuarios",
    response_model=UsuarioListOut,
    summary="Listar usuarios del sistema",
    description=(
        "Retorna un listado paginado de todos los usuarios registrados en "
        "`core.usuarios` con sus roles activos. Requiere autenticación JWT."
    ),
)
async def listar_usuarios(
    skip: int = Query(default=0, ge=0, description="Número de registros a saltar (offset)."),
    limit: int = Query(default=50, ge=1, le=200, description="Número máximo de registros a retornar."),
    estado: str | None = Query(default=None, description="Filtrar por estado: activo, inactivo, etc."),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> UsuarioListOut:
    # Query base con carga eager de roles
    query = select(Usuario).options(
        selectinload(Usuario.roles)
    )

    # Filtro opcional por estado
    if estado:
        query = query.where(Usuario.estado == estado)

    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Aplicar paginación
    query = query.offset(skip).limit(limit).order_by(Usuario.fecha_creacion.desc())
    result = await db.execute(query)
    usuarios = result.scalars().all()

    return UsuarioListOut(
        total=total,
        usuarios=[UsuarioOut.model_validate(u) for u in usuarios],
    )
