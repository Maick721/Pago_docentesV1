from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pagos_docentes.enums import PaymentRecordStatus, PaymentStatus
from app.modules.pagos_docentes.models import Payment, TeacherModule
from app.modules.pagos_docentes.services.comun import _ultima_aprobacion, _vencido
from app.modules.pagos_docentes.schemas import PaymentSummary


async def obtener_resumen(session: AsyncSession) -> PaymentSummary:
    latest = _ultima_aprobacion()
    in_progress = TeacherModule.estado == PaymentStatus.EN_CURSO.value
    ready = TeacherModule.estado == PaymentStatus.LISTO_PAGO.value
    approved = TeacherModule.estado == PaymentStatus.APROBADO.value
    paid = Payment.estado == PaymentRecordStatus.PAGADO.value
    pending = Payment.estado == PaymentRecordStatus.POR_PAGAR.value
    payment_overdue = (
        approved
        & pending
        & _vencido(latest.c.fecha_aprobacion)
    )
    approval_overdue = ready & _vencido(TeacherModule.fecha_listo_pago)
    query = select(
        func.count(TeacherModule.id_modulo),
        func.count(case((in_progress, TeacherModule.id_modulo))),
        func.count(case((ready, TeacherModule.id_modulo))),
        func.count(case((pending, TeacherModule.id_modulo))),
        func.count(case((paid, TeacherModule.id_modulo))),
        func.count(case((payment_overdue, TeacherModule.id_modulo))),
        func.count(case((approval_overdue, TeacherModule.id_modulo))),
        func.coalesce(func.sum(case((pending, Payment.monto), else_=0)), 0),
        func.coalesce(func.sum(case((paid, Payment.monto), else_=0)), 0),
    )
    query = query.outerjoin(Payment, Payment.id_modulo == TeacherModule.id_modulo)
    query = query.outerjoin(
        latest, latest.c.id_modulo == TeacherModule.id_modulo
    )
    row = (await session.execute(query)).one()
    return PaymentSummary(
        total=row[0],
        borradores=row[1],
        listos=row[2],
        por_pagar=row[3],
        pagados=row[4],
        en_mora=row[5],
        listos_atrasados=row[6],
        monto_pendiente=row[7] or Decimal(0),
        monto_pagado=row[8] or Decimal(0),
    )
