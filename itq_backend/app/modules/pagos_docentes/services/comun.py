from typing import Any

from sqlalchemy import Integer, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.exceptions import HTTPException

from app.models.core import Usuario
from app.modules.pagos_docentes.enums import (
    AlertStatus,
    PaymentStatus,
    ThresholdUnit,
)
from app.modules.pagos_docentes.models import (
    AcademicPeriod,
    Approval,
    HistoryEntry,
    Payment,
    PaymentConfig,
    Teacher,
    TeacherModule,
    utc_now_naive,
)
from app.modules.pagos_docentes.referencias_docentes import (
    CoreAcademicCatalogRef,
    CoreEmployeeRef,
    CorePersonRef,
)
from app.modules.pagos_docentes.schemas import (
    PaymentRead,
    PaymentSettingsRead,
    TeacherRead,
)

DEFAULT_THRESHOLD = 30
SECONDS_PER_DAY = 86400

_API_STATUS = {
    PaymentStatus.EN_CURSO.value: "borrador",
    PaymentStatus.LISTO_PAGO.value: "listo",
    PaymentStatus.APROBADO.value: "aprobado",
    PaymentStatus.PAGADO.value: "pagado",
    PaymentStatus.ANULADO.value: "anulado",
}


def _dias_transcurridos(column: Any) -> Any:
    utc_now = func.timezone("UTC", func.now())
    elapsed_seconds = func.extract("epoch", utc_now - column)
    return func.greatest(0, func.floor(elapsed_seconds / SECONDS_PER_DAY)).cast(Integer)


def _ultima_aprobacion():
    return (
        select(
            Approval.id_modulo.label("id_modulo"),
            Approval.fecha_aprobacion.label("fecha_aprobacion"),
            Approval.id_usuario.label("id_usuario"),
        )
        .where(Approval.estado == "VIGENTE")
        .subquery()
    )


def _valor_umbral():
    return func.coalesce(
        select(PaymentConfig.valor)
        .where(PaymentConfig.activo.is_(True))
        .limit(1)
        .scalar_subquery(),
        DEFAULT_THRESHOLD,
    )


def _unidad_umbral():
    return func.coalesce(
        select(PaymentConfig.unidad)
        .where(PaymentConfig.activo.is_(True))
        .limit(1)
        .scalar_subquery(),
        ThresholdUnit.DIAS.value,
    )


def _vencido(column: Any) -> Any:
    value = _valor_umbral()
    unit = _unidad_umbral()
    interval = func.make_interval(
        0,
        case((unit == ThresholdUnit.MESES.value, value), else_=0),
        0,
        case((unit == ThresholdUnit.DIAS.value, value), else_=0),
        0,
        0,
        0,
    )
    return column.is_not(None) & (
        column + interval < func.timezone("UTC", func.now())
    )


def _columnas_docente() -> tuple[Any, ...]:
    return (
        Teacher.id_docente.label("teacher_id"),
        func.concat_ws(
            " ", CorePersonRef.nombres, CorePersonRef.apellidos
        ).label("teacher_name"),
        CorePersonRef.cedula.label("teacher_cedula"),
        func.coalesce(
            CorePersonRef.correo, Teacher.correo_notificacion
        ).label("teacher_email"),
        CoreAcademicCatalogRef.nombre.label("career_name"),
        AcademicPeriod.nombre.label("period_name"),
    )


def _unir_referencias(query: Any) -> Any:
    return (
        query.join(Teacher, Teacher.id_docente == TeacherModule.id_docente)
        .join(CoreEmployeeRef, CoreEmployeeRef.id_empleado == Teacher.id_empleado)
        .join(CorePersonRef, CorePersonRef.id_persona == CoreEmployeeRef.id_persona)
        .join(AcademicPeriod, AcademicPeriod.id_periodo == TeacherModule.id_periodo)
        .join(
            CoreAcademicCatalogRef,
            CoreAcademicCatalogRef.id_catalogo == TeacherModule.id_carrera,
        )
    )


def _respuesta_docente(row: Any) -> TeacherRead:
    return TeacherRead(
        id_docente=row.teacher_id,
        nombre=row.teacher_name or "",
        cedula=row.teacher_cedula,
        correo=row.teacher_email,
    )


def _respuesta_pago(row: Any) -> PaymentRead:
    module = row[0]
    return PaymentRead(
        id=module.id_modulo,
        docente=row.teacher_name or "",
        correo_docente=row.teacher_email,
        modulo=module.nombre_modulo,
        carrera=row.career_name or "",
        periodo_academico=row.period_name or "",
        fecha_inicio=module.fecha_inicio,
        fecha_fin=module.fecha_fin,
        monto=row.amount,
        modelo=module.modelo.lower(),
        datos_modelo=module.datos_modelo,
        estado=_API_STATUS[module.estado],
        aprobado_en=row.approval_date,
        aprobado_por=row.approver_name,
        pagado_en=row.payment_date,
        dias_desde_aprobacion=row.approved_days,
        en_mora=bool(row.payment_overdue),
        dias_desde_listo=row.ready_days,
        listo_atrasado=bool(row.approval_overdue),
        numero_factura=row.invoice_number,
        numero_comprobante=row.receipt_number,
    )


def _consulta_pagos():
    latest = _ultima_aprobacion()
    ready_days = _dias_transcurridos(TeacherModule.fecha_listo_pago)
    approved_days = _dias_transcurridos(latest.c.fecha_aprobacion)
    query = select(
        TeacherModule,
        *_columnas_docente(),
        Payment.monto.label("amount"),
        Payment.fecha_pago.label("payment_date"),
        Payment.numero_factura.label("invoice_number"),
        Payment.numero_comprobante.label("receipt_number"),
        latest.c.fecha_aprobacion.label("approval_date"),
        Usuario.nombre_usuario.label("approver_name"),
        case(
            (TeacherModule.estado == PaymentStatus.LISTO_PAGO.value, ready_days),
            else_=None,
        ).label("ready_days"),
        case(
            (TeacherModule.estado == PaymentStatus.APROBADO.value, approved_days),
            else_=None,
        ).label("approved_days"),
        case(
            (
                (TeacherModule.estado == PaymentStatus.LISTO_PAGO.value)
                & _vencido(TeacherModule.fecha_listo_pago),
                True,
            ),
            else_=False,
        ).label("approval_overdue"),
        case(
            (
                (TeacherModule.estado == PaymentStatus.APROBADO.value)
                & (Payment.estado == "POR_PAGAR")
                & _vencido(latest.c.fecha_aprobacion),
                True,
            ),
            else_=False,
        ).label("payment_overdue"),
    )
    query = _unir_referencias(query)
    query = query.outerjoin(Payment, Payment.id_modulo == TeacherModule.id_modulo)
    query = query.outerjoin(
        latest, latest.c.id_modulo == TeacherModule.id_modulo
    ).outerjoin(Usuario, Usuario.id_usuario == latest.c.id_usuario)
    return query


async def _obtener_modulo(
    session: AsyncSession, payment_id: int
) -> TeacherModule:
    module = await session.get(TeacherModule, payment_id)
    if module is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró el módulo.")
    return module


async def _obtener_respuesta_pago(
    session: AsyncSession, payment_id: int
) -> PaymentRead:
    query = _consulta_pagos().where(TeacherModule.id_modulo == payment_id)
    row = (await session.execute(query)).one_or_none()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No se encontró el módulo.")
    return _respuesta_pago(row)


async def _agregar_historial(
    session: AsyncSession,
    module: TeacherModule,
    old_status: str | None,
    new_status: str,
    actor_id: int,
    note: str | None = None,
) -> None:
    session.add(
        HistoryEntry(
            id_modulo=module.id_modulo,
            estado_anterior=old_status,
            estado_nuevo=new_status,
            fecha=utc_now_naive(),
            observacion=note,
            id_usuario=actor_id,
        )
    )


async def leer_configuracion(session: AsyncSession) -> PaymentSettingsRead:
    config = await session.scalar(
        select(PaymentConfig)
        .where(PaymentConfig.activo.is_(True))
        .order_by(PaymentConfig.id_configuracion.desc())
        .limit(1)
    )
    if config is None:
        return PaymentSettingsRead(
            valor=DEFAULT_THRESHOLD,
            unidad=ThresholdUnit.DIAS,
        )
    return PaymentSettingsRead(
        valor=config.valor,
        unidad=config.unidad,
        correo_notificacion=config.correo_notificacion,
    )
