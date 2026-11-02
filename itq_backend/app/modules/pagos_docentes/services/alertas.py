from sqlalchemy import literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pagos_docentes.enums import (
    AlertStatus,
    AlertType,
    PaymentRecordStatus,
    PaymentStatus,
)
from app.modules.pagos_docentes.models import Payment, TeacherModule
from app.modules.pagos_docentes.schemas import PaymentAlertRead, TeacherRead
from app.modules.pagos_docentes.services.comun import (
    _columnas_docente,
    _dias_transcurridos,
    _ultima_aprobacion,
    _unidad_umbral,
    _unir_referencias,
    _valor_umbral,
    _vencido,
)


async def listar_alertas(session: AsyncSession) -> list[PaymentAlertRead]:
    threshold = _valor_umbral()
    unit = _unidad_umbral()
    latest = _ultima_aprobacion()

    payment_alerts = _unir_referencias(
        select(
            TeacherModule.id_modulo.label("id_modulo"),
            *_columnas_docente(),
            TeacherModule.nombre_modulo.label("nombre_modulo"),
            literal(AlertType.PAGO_ATRASADO.value).label("tipo"),
            literal(AlertStatus.ACTIVA.value).label("alert_status"),
            latest.c.fecha_aprobacion.label("fecha_referencia"),
            _dias_transcurridos(latest.c.fecha_aprobacion).label(
                "dias_transcurridos"
            ),
            threshold.label("umbral"),
            unit.label("unidad"),
        )
    )
    payment_alerts = (
        payment_alerts.join(
            latest, latest.c.id_modulo == TeacherModule.id_modulo
        )
        .join(Payment, Payment.id_modulo == TeacherModule.id_modulo)
        .where(
            TeacherModule.estado == PaymentStatus.APROBADO.value,
            Payment.estado == PaymentRecordStatus.POR_PAGAR.value,
            _vencido(latest.c.fecha_aprobacion),
        )
    )

    approval_alerts = _unir_referencias(
        select(
            TeacherModule.id_modulo.label("id_modulo"),
            *_columnas_docente(),
            TeacherModule.nombre_modulo.label("nombre_modulo"),
            literal(AlertType.APROBACION_PENDIENTE.value).label("tipo"),
            literal(AlertStatus.ACTIVA.value).label("alert_status"),
            TeacherModule.fecha_listo_pago.label("fecha_referencia"),
            _dias_transcurridos(TeacherModule.fecha_listo_pago).label(
                "dias_transcurridos"
            ),
            threshold.label("umbral"),
            unit.label("unidad"),
        )
    ).where(
        TeacherModule.estado == PaymentStatus.LISTO_PAGO.value,
        TeacherModule.listo_para_pago.is_(True),
        _vencido(TeacherModule.fecha_listo_pago),
    )

    combined = payment_alerts.union_all(approval_alerts).subquery()
    rows = (
        await session.execute(
            select(combined).order_by(
                combined.c.fecha_referencia.asc(), combined.c.id_modulo.asc()
            )
        )
    ).all()
    alerts = []
    for row in rows:
        teacher = TeacherRead(
            id_docente=row.teacher_id,
            nombre=row.teacher_name or "",
            cedula=row.teacher_cedula,
            correo=row.teacher_email,
        )
        alerts.append(
            PaymentAlertRead(
                id_modulo=row.id_modulo,
                docente=teacher,
                nombre_modulo=row.nombre_modulo,
                carrera=row.career_name or "",
                periodo=row.period_name or "",
                tipo=row.tipo,
                estado=row.alert_status,
                fecha_referencia=row.fecha_referencia,
                dias_transcurridos=row.dias_transcurridos,
                umbral=row.umbral,
                unidad=row.unidad,
            )
        )
    return alerts
