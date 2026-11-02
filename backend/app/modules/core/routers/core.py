"""
app/modules/core/routers/core.py
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
from app.modules.core.models.core import (
    Persona,
    Usuario,
    UsuarioRol,
    Permiso,
    Modulo,
    Unidad,
    Estudiante,
    Empleado,
    CatalogoAcademico,
    AcademicProgram,
    AcademicPeriod,
    Campus,
    AcademicModality,
    AcademicParallel,
)
from app.modules.core.schemas.core import (
    PersonaOut,
    UsuarioListOut,
    UsuarioOut,
    PermisoOut,
    PermisoCreate,
    ModuloOut,
    ModuloCreate,
    UnidadOut,
    UnidadCreate,
    EstudianteOut,
    EstudianteCreate,
    EmpleadoOut,
    EmpleadoCreate,
    CatalogoAcademicoOut,
    CatalogoAcademicoCreate,
    AcademicProgramOut,
    AcademicProgramCreate,
    AcademicPeriodOut,
    AcademicPeriodCreate,
    CampusOut,
    CampusCreate,
    AcademicModalityOut,
    AcademicModalityCreate,
    AcademicParallelOut,
    AcademicParallelCreate,
)

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
    estado: str | None = Query(default=None, description="Filtrar por estado: activo o inactivo."),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> UsuarioListOut:
    # Query base con carga eager de roles
    query = select(Usuario).options(
        selectinload(Usuario.roles)
    )

    # Filtro opcional por estado
    if estado is not None:
        normalized_status = estado.strip().lower()
        if normalized_status not in {"activo", "inactivo"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El estado debe ser 'activo' o 'inactivo'.",
            )
        query = query.where(Usuario.estado.is_(normalized_status == "activo"))

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


# ─── Helper genérico ───────────────────────────────────────────────────────────

async def _get_or_404(db: AsyncSession, model, entity_id: int, pk_column: str):
    result = await db.execute(select(model).where(getattr(model, pk_column) == entity_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{model.__name__} con id {entity_id} no encontrado.",
        )
    return obj


# ─── Permisos ──────────────────────────────────────────────────────────────────

@router.get(
    "/permisos",
    response_model=list[PermisoOut],
    summary="Listar permisos",
)
async def listar_permisos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Permiso).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/permisos",
    response_model=PermisoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear permiso",
)
async def crear_permiso(
    body: PermisoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Permiso(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/permisos/{permiso_id}",
    response_model=PermisoOut,
    summary="Actualizar permiso",
)
async def actualizar_permiso(
    permiso_id: int,
    body: PermisoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Permiso, permiso_id, "id_permiso")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/permisos/{permiso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar permiso",
)
async def desactivar_permiso(
    permiso_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Permiso, permiso_id, "id_permiso")
    obj.estado = False
    await db.commit()


# ─── Modulos ───────────────────────────────────────────────────────────────────

@router.get(
    "/modulos",
    response_model=list[ModuloOut],
    summary="Listar módulos",
)
async def listar_modulos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Modulo).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/modulos",
    response_model=ModuloOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear módulo",
)
async def crear_modulo(
    body: ModuloCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Modulo(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/modulos/{modulo_id}",
    response_model=ModuloOut,
    summary="Actualizar módulo",
)
async def actualizar_modulo(
    modulo_id: int,
    body: ModuloCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Modulo, modulo_id, "id_modulo")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/modulos/{modulo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar módulo",
)
async def desactivar_modulo(
    modulo_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Modulo, modulo_id, "id_modulo")
    obj.estado = False
    await db.commit()


# ─── Unidades ──────────────────────────────────────────────────────────────────

@router.get(
    "/unidades",
    response_model=list[UnidadOut],
    summary="Listar unidades",
)
async def listar_unidades(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Unidad).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/unidades",
    response_model=UnidadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear unidad",
)
async def crear_unidad(
    body: UnidadCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Unidad(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/unidades/{unidad_id}",
    response_model=UnidadOut,
    summary="Actualizar unidad",
)
async def actualizar_unidad(
    unidad_id: int,
    body: UnidadCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Unidad, unidad_id, "id_unidad")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/unidades/{unidad_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar unidad",
)
async def desactivar_unidad(
    unidad_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Unidad, unidad_id, "id_unidad")
    obj.estado = False
    await db.commit()


# ─── Estudiantes ───────────────────────────────────────────────────────────────

@router.get(
    "/estudiantes",
    response_model=list[EstudianteOut],
    summary="Listar estudiantes",
)
async def listar_estudiantes(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Estudiante).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/estudiantes",
    response_model=EstudianteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear estudiante",
)
async def crear_estudiante(
    body: EstudianteCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Estudiante(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/estudiantes/{estudiante_id}",
    response_model=EstudianteOut,
    summary="Actualizar estudiante",
)
async def actualizar_estudiante(
    estudiante_id: int,
    body: EstudianteCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Estudiante, estudiante_id, "id_estudiante")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/estudiantes/{estudiante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar estudiante",
)
async def desactivar_estudiante(
    estudiante_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Estudiante, estudiante_id, "id_estudiante")
    obj.estado = False
    await db.commit()


# ─── Empleados ─────────────────────────────────────────────────────────────────

@router.get(
    "/empleados",
    response_model=list[EmpleadoOut],
    summary="Listar empleados",
)
async def listar_empleados(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Empleado).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/empleados",
    response_model=EmpleadoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empleado",
)
async def crear_empleado(
    body: EmpleadoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Empleado(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/empleados/{empleado_id}",
    response_model=EmpleadoOut,
    summary="Actualizar empleado",
)
async def actualizar_empleado(
    empleado_id: int,
    body: EmpleadoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Empleado, empleado_id, "id_empleado")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/empleados/{empleado_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar empleado",
)
async def desactivar_empleado(
    empleado_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Empleado, empleado_id, "id_empleado")
    obj.estado = False
    await db.commit()


# ─── Catalogos Academicos ──────────────────────────────────────────────────────

@router.get(
    "/catalogos-academicos",
    response_model=list[CatalogoAcademicoOut],
    summary="Listar catálogos académicos",
)
async def listar_catalogos_academicos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(CatalogoAcademico).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/catalogos-academicos",
    response_model=CatalogoAcademicoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear catálogo académico",
)
async def crear_catalogo_academico(
    body: CatalogoAcademicoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = CatalogoAcademico(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.put(
    "/catalogos-academicos/{catalogo_id}",
    response_model=CatalogoAcademicoOut,
    summary="Actualizar catálogo académico",
)
async def actualizar_catalogo_academico(
    catalogo_id: int,
    body: CatalogoAcademicoCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, CatalogoAcademico, catalogo_id, "id_catalogo")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/catalogos-academicos/{catalogo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar catálogo académico",
)
async def desactivar_catalogo_academico(
    catalogo_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, CatalogoAcademico, catalogo_id, "id_catalogo")
    obj.estado = False
    await db.commit()


# ─── Academic Programs ─────────────────────────────────────────────────────────

@router.get(
    "/academic-programs",
    response_model=list[AcademicProgramOut],
    summary="Listar programas académicos",
)
async def listar_academic_programs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(AcademicProgram).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/academic-programs",
    response_model=AcademicProgramOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear programa académico",
)
async def crear_academic_program(
    body: AcademicProgramCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = AcademicProgram(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/academic-programs/{program_id}",
    response_model=AcademicProgramOut,
    summary="Obtener programa académico por ID",
)
async def obtener_academic_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, AcademicProgram, program_id, "id_program")


@router.put(
    "/academic-programs/{program_id}",
    response_model=AcademicProgramOut,
    summary="Actualizar programa académico",
)
async def actualizar_academic_program(
    program_id: int,
    body: AcademicProgramCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicProgram, program_id, "id_program")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/academic-programs/{program_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar programa académico",
)
async def desactivar_academic_program(
    program_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicProgram, program_id, "id_program")
    obj.estado = False
    await db.commit()


# ─── Academic Periods ──────────────────────────────────────────────────────────

@router.get(
    "/academic-periods",
    response_model=list[AcademicPeriodOut],
    summary="Listar periodos académicos",
)
async def listar_academic_periods(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(AcademicPeriod).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/academic-periods",
    response_model=AcademicPeriodOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear periodo académico",
)
async def crear_academic_period(
    body: AcademicPeriodCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = AcademicPeriod(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/academic-periods/{period_id}",
    response_model=AcademicPeriodOut,
    summary="Obtener periodo académico por ID",
)
async def obtener_academic_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, AcademicPeriod, period_id, "id_period")


@router.put(
    "/academic-periods/{period_id}",
    response_model=AcademicPeriodOut,
    summary="Actualizar periodo académico",
)
async def actualizar_academic_period(
    period_id: int,
    body: AcademicPeriodCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicPeriod, period_id, "id_period")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/academic-periods/{period_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar periodo académico",
)
async def desactivar_academic_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicPeriod, period_id, "id_period")
    obj.estado = False
    await db.commit()


# ─── Campus ────────────────────────────────────────────────────────────────────

@router.get(
    "/campus",
    response_model=list[CampusOut],
    summary="Listar campus",
)
async def listar_campus(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Campus).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/campus",
    response_model=CampusOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear campus",
)
async def crear_campus(
    body: CampusCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = Campus(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/campus/{campus_id}",
    response_model=CampusOut,
    summary="Obtener campus por ID",
)
async def obtener_campus(
    campus_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Campus, campus_id, "id_campus")


@router.put(
    "/campus/{campus_id}",
    response_model=CampusOut,
    summary="Actualizar campus",
)
async def actualizar_campus(
    campus_id: int,
    body: CampusCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Campus, campus_id, "id_campus")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/campus/{campus_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar campus",
)
async def desactivar_campus(
    campus_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Campus, campus_id, "id_campus")
    obj.estado = False
    await db.commit()


# ─── Academic Modalities ───────────────────────────────────────────────────────

@router.get(
    "/academic-modalities",
    response_model=list[AcademicModalityOut],
    summary="Listar modalidades académicas",
)
async def listar_academic_modalities(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(AcademicModality).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/academic-modalities",
    response_model=AcademicModalityOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear modalidad académica",
)
async def crear_academic_modality(
    body: AcademicModalityCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = AcademicModality(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/academic-modalities/{modality_id}",
    response_model=AcademicModalityOut,
    summary="Obtener modalidad académica por ID",
)
async def obtener_academic_modality(
    modality_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, AcademicModality, modality_id, "id_modality")


@router.put(
    "/academic-modalities/{modality_id}",
    response_model=AcademicModalityOut,
    summary="Actualizar modalidad académica",
)
async def actualizar_academic_modality(
    modality_id: int,
    body: AcademicModalityCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicModality, modality_id, "id_modality")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/academic-modalities/{modality_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar modalidad académica",
)
async def desactivar_academic_modality(
    modality_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicModality, modality_id, "id_modality")
    obj.estado = False
    await db.commit()


# ─── Academic Parallels ────────────────────────────────────────────────────────

@router.get(
    "/academic-parallels",
    response_model=list[AcademicParallelOut],
    summary="Listar paralelos académicos",
)
async def listar_academic_parallels(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(AcademicParallel).offset(skip).limit(limit))
    return result.scalars().all()


@router.post(
    "/academic-parallels",
    response_model=AcademicParallelOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear paralelo académico",
)
async def crear_academic_parallel(
    body: AcademicParallelCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = AcademicParallel(**body.model_dump())
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.get(
    "/academic-parallels/{parallel_id}",
    response_model=AcademicParallelOut,
    summary="Obtener paralelo académico por ID",
)
async def obtener_academic_parallel(
    parallel_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, AcademicParallel, parallel_id, "id_parallel")


@router.put(
    "/academic-parallels/{parallel_id}",
    response_model=AcademicParallelOut,
    summary="Actualizar paralelo académico",
)
async def actualizar_academic_parallel(
    parallel_id: int,
    body: AcademicParallelCreate,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicParallel, parallel_id, "id_parallel")
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/academic-parallels/{parallel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desactivar paralelo académico",
)
async def desactivar_academic_parallel(
    parallel_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, AcademicParallel, parallel_id, "id_parallel")
    obj.estado = False
    await db.commit()


# ─── Detalle por ID (GET individuales) ─────────────────────────────────────────

@router.get(
    "/personas/{persona_id}",
    response_model=PersonaOut,
    summary="Obtener persona por ID",
)
async def obtener_persona(
    persona_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    obj = await _get_or_404(db, Persona, persona_id, "id_persona")
    return obj


@router.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioOut,
    summary="Obtener usuario por ID",
)
async def obtener_usuario(
    usuario_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.roles).selectinload(UsuarioRol.rol))
        .where(Usuario.id_usuario == usuario_id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con id {usuario_id} no encontrado.",
        )
    return obj


@router.get(
    "/permisos/{permiso_id}",
    response_model=PermisoOut,
    summary="Obtener permiso por ID",
)
async def obtener_permiso(
    permiso_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Permiso, permiso_id, "id_permiso")


@router.get(
    "/modulos/{modulo_id}",
    response_model=ModuloOut,
    summary="Obtener módulo por ID",
)
async def obtener_modulo(
    modulo_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Modulo, modulo_id, "id_modulo")


@router.get(
    "/unidades/{unidad_id}",
    response_model=UnidadOut,
    summary="Obtener unidad por ID",
)
async def obtener_unidad(
    unidad_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Unidad, unidad_id, "id_unidad")


@router.get(
    "/estudiantes/{estudiante_id}",
    response_model=EstudianteOut,
    summary="Obtener estudiante por ID",
)
async def obtener_estudiante(
    estudiante_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Estudiante, estudiante_id, "id_estudiante")


@router.get(
    "/empleados/{empleado_id}",
    response_model=EmpleadoOut,
    summary="Obtener empleado por ID",
)
async def obtener_empleado(
    empleado_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, Empleado, empleado_id, "id_empleado")


@router.get(
    "/catalogos-academicos/{catalogo_id}",
    response_model=CatalogoAcademicoOut,
    summary="Obtener catálogo académico por ID",
)
async def obtener_catalogo_academico(
    catalogo_id: int,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return await _get_or_404(db, CatalogoAcademico, catalogo_id, "id_catalogo")


# ─── Notificaciones (RF-CORE-06) ───────────────────────────────────────────────

@router.get(
    "/notificaciones",
    response_model=list[dict],
    summary="Listar notificaciones",
)
async def listar_notificaciones(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Endpoint placeholder para notificaciones internas (RF-CORE-06)."""
    return []


@router.post(
    "/notificaciones",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Crear notificación",
)
async def crear_notificacion(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Endpoint placeholder para generar alertas/notificaciones (RF-CORE-06)."""
    return {"status": "notificada", "detalle": body}


# ─── Reportes / exportaciones (RF-CORE-08) ─────────────────────────────────────

@router.get(
    "/reportes/usuarios",
    response_model=dict,
    summary="Reporte de usuarios",
)
async def reporte_usuarios(
    db: AsyncSession = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    """Endpoint de reporte/exportación de usuarios (RF-CORE-08)."""
    result = await db.execute(select(Usuario))
    usuarios = result.scalars().all()
    return {
        "total": len(usuarios),
        "usuarios": [
            {
                "id_usuario": u.id_usuario,
                "nombre_usuario": u.nombre_usuario,
                "correo_institucional": u.correo_institucional,
                "estado": u.estado,
                "fecha_creacion": u.fecha_creacion.isoformat() if u.fecha_creacion else None,
            }
            for u in usuarios
        ],
    }
