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
    _unidad_umbral,
    _ultima_aprobacion,
    _valor_umbral,
    _vencido,
    _unir_docente,
)


async def listar_alertas(session: AsyncSession) -> list[PaymentAlertRead]:
    threshold = _valor_umbral()
    unit = _unidad_umbral()
    latest = _ultima_aprobacion()
    payment_due_days = _dias_transcurridos(latest.c.fecha_aprobacion)
    alerts = select(
        TeacherModule.id_modulo.label("id_modulo"),
        *_columnas_docente(),
        TeacherModule.nombre_modulo.label("nombre_modulo"),
        literal(AlertType.PAGO_ATRASADO.value).label("tipo"),
        literal(AlertStatus.ACTIVA.value).label("estado"),
        latest.c.fecha_aprobacion.label("fecha_referencia"),
        payment_due_days.label("dias_transcurridos"),
        threshold.label("umbral"),
        unit.label("unidad"),
    )
    alerts = _unir_docente(alerts).join(
        latest, latest.c.id_modulo == TeacherModule.id_modulo
    ).join(Payment, Payment.id_modulo == TeacherModule.id_modulo).where(
        TeacherModule.estado == PaymentStatus.APROBADO.value,
        Payment.estado == PaymentRecordStatus.POR_PAGAR.value,
        _vencido(latest.c.fecha_aprobacion),
    )
    rows = (
        await session.execute(
            alerts.order_by(latest.c.fecha_aprobacion.asc())
        )
    ).all()
    return [
        PaymentAlertRead(
            id_modulo=row.id_modulo,
            docente=TeacherRead(
                id_docente=row.teacher_id,
                nombre=row.teacher_name or "",
                cedula=row.teacher_cedula,
                correo=row.teacher_email,
            ),
            nombre_modulo=row.nombre_modulo,
            carrera=row.career_name or "",
            periodo=row.period_name or "",
            tipo=row.tipo,
            estado=row.estado,
            fecha_referencia=row.fecha_referencia,
            dias_transcurridos=row.dias_transcurridos,
            umbral=row.umbral,
            unidad=row.unidad,
        )
        for row in rows
    ]
