from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pagos_docentes.referencias_docentes import (
    CoreAcademicCatalogRef,
    CoreEmployeeRef,
    CorePersonRef,
)
from app.modules.pagos_docentes.enums import PaymentStatus
from app.modules.pagos_docentes.models import (
    AcademicPeriod,
    Approval,
    Payment,
    Teacher,
    TeacherModule,
)
from app.modules.pagos_docentes.schemas import (
    LookupOption,
    PaymentCreate,
    PaymentLookups,
    PaymentPage,
    PaymentRead,
    TeacherOption,
)
from app.modules.pagos_docentes.services.comun import (
    HTTPException,
    _agregar_historial,
    _consulta_pagos,
    _obtener_respuesta_pago,
    _respuesta_pago,
    _ultima_aprobacion,
    status,
)


async def listar_opciones(session: AsyncSession) -> PaymentLookups:
    teachers = (
        await session.execute(
            select(
                Teacher.id_docente,
                func.concat_ws(" ", CorePersonRef.nombres, CorePersonRef.apellidos).label("nombre"),
                CorePersonRef.cedula,
                func.coalesce(CorePersonRef.correo, Teacher.correo_notificacion).label("correo"),
            )
            .join(CoreEmployeeRef, CoreEmployeeRef.id_empleado == Teacher.id_empleado)
            .outerjoin(CorePersonRef, CorePersonRef.id_persona == CoreEmployeeRef.id_persona)
            .where(Teacher.estado.is_(True))
            .order_by(CorePersonRef.apellidos, CorePersonRef.nombres)
        )
    ).all()
    periods = (
        await session.execute(
            select(AcademicPeriod.id_periodo, AcademicPeriod.nombre)
            .where(AcademicPeriod.estado.is_(True))
            .order_by(AcademicPeriod.nombre)
        )
    ).all()
    careers = (
        await session.execute(
            select(
                CoreAcademicCatalogRef.id_catalogo,
                CoreAcademicCatalogRef.nombre,
                CoreAcademicCatalogRef.descripcion,
            )
            .where(
                CoreAcademicCatalogRef.tipo == "CARRERA",
                CoreAcademicCatalogRef.estado.is_(True),
            )
            .order_by(CoreAcademicCatalogRef.descripcion, CoreAcademicCatalogRef.nombre)
        )
    ).all()
    return PaymentLookups(
        docentes=[
            TeacherOption(
                id_docente=row.id_docente,
                nombre=row.nombre or "",
                cedula=row.cedula,
                correo=row.correo,
            )
            for row in teachers
        ],
        periodos=[LookupOption(id=row.id_periodo, nombre=row.nombre) for row in periods],
        carreras=[
            LookupOption(
                id=row.id_catalogo,
                nombre=row.nombre or "",
                grupo=row.descripcion,
            )
            for row in careers
            if row.nombre is not None
        ],
    )


async def listar_pagos(
    session: AsyncSession,
    periodo: str | None,
    mes: int | None,
    carrera: str | None,
    estado: PaymentStatus | None,
    q: str | None,
    page: int,
    page_size: int,
) -> PaymentPage:
    query = _consulta_pagos()
    if periodo:
        query = query.where(AcademicPeriod.nombre.ilike(f"%{periodo}%"))
    if mes:
        approved_in_month = select(Approval.id_modulo).where(
            Approval.estado == "VIGENTE",
            extract("month", Approval.fecha_aprobacion) == mes,
        )
        query = query.where(TeacherModule.id_modulo.in_(approved_in_month))
    if carrera:
        query = query.where(CoreAcademicCatalogRef.nombre.ilike(f"%{carrera}%"))
    if estado:
        query = query.where(TeacherModule.estado == estado.value)
    if q:
        query = query.where(
            func.concat_ws(" ", CorePersonRef.nombres, CorePersonRef.apellidos).ilike(f"%{q}%")
            | CorePersonRef.cedula.ilike(f"%{q}%")
            | CorePersonRef.correo.ilike(f"%{q}%")
            | TeacherModule.nombre_modulo.ilike(f"%{q}%")
        )
    count_query = select(func.count()).select_from(
        query.with_only_columns(TeacherModule.id_modulo)
        .order_by(None)
        .subquery()
    )
    total = await session.scalar(count_query) or 0
    query = (
        query.order_by(TeacherModule.id_modulo.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(query)).all()
    items = [_respuesta_pago(row) for row in rows]
    return PaymentPage(items=items, total=total, page=page, page_size=page_size)


async def crear_pago(
    body: PaymentCreate,
    session: AsyncSession,
    actor_id: int,
) -> PaymentRead:
    teacher = await session.get(Teacher, body.id_docente)
    if teacher is None or not teacher.estado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró el docente activo.")
    period = await session.get(AcademicPeriod, body.id_periodo)
    if period is None or not period.estado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró el período académico activo.")
    career = await session.get(CoreAcademicCatalogRef, body.id_carrera)
    if career is None or career.tipo != "CARRERA" or career.estado is not True:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró la carrera activa.")
    module = TeacherModule(
        id_docente=body.id_docente,
        id_periodo=body.id_periodo,
        id_carrera=body.id_carrera,
        nombre_modulo=body.nombre_modulo,
        paralelo=body.paralelo,
        numero_modulo=body.numero_modulo,
        fecha_inicio=body.fecha_inicio,
        fecha_fin=body.fecha_fin,
        estado=PaymentStatus.EN_CURSO.value,
        listo_para_pago=False,
        id_usuario_registro=actor_id,
        codigo_eva=body.codigo_eva,
        modelo=body.modelo.value,
        contrato=body.contrato,
        datos_modelo=body.datos_modelo,
    )
    session.add(module)
    await session.flush()
    await _agregar_historial(
        session,
        module,
        None,
        PaymentStatus.EN_CURSO.value,
        actor_id,
        "Módulo creado.",
    )
    await session.commit()
    return await _obtener_respuesta_pago(session, module.id_modulo)
