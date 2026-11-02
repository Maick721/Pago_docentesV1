from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pagos_docentes.enums import ApprovalStatus, PaymentRecordStatus, PaymentStatus
from app.modules.pagos_docentes.models import Approval, HistoryEntry, Payment, TeacherModule, utc_now_naive
from app.modules.pagos_docentes.referencias_docentes import CoreUserRef
from app.modules.pagos_docentes.schemas import (
    PaymentApproval,
    PaymentCompletion,
    PaymentHistoryRead,
    PaymentRead,
    PaymentReady,
)
from app.modules.pagos_docentes.services.comun import (
    HTTPException,
    status,
    _agregar_historial,
    _obtener_modulo,
    _obtener_respuesta_pago,
)


async def marcar_listo(
    payment_id: int,
    body: PaymentReady,
    session: AsyncSession,
    actor_id: int,
) -> PaymentRead:
    module = await _obtener_modulo(session, payment_id)
    if module.estado != PaymentStatus.EN_CURSO.value or module.listo_para_pago:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo un módulo EN_CURSO puede marcarse LISTO_PAGO.",
        )
    existing_payment = await session.scalar(
        select(Payment).where(Payment.id_modulo == module.id_modulo)
    )
    if existing_payment is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "El módulo ya tiene un pago registrado.")
    old_status = module.estado
    module.estado = PaymentStatus.LISTO_PAGO.value
    module.listo_para_pago = True
    module.fecha_listo_pago = utc_now_naive()
    session.add(
        Payment(
            id_modulo=module.id_modulo,
            monto=body.monto,
            estado=PaymentRecordStatus.POR_PAGAR.value,
        )
    )
    await _agregar_historial(
        session,
        module,
        old_status,
        module.estado,
        actor_id,
        "Módulo marcado LISTO_PAGO; pago creado como POR_PAGAR.",
    )
    await session.commit()
    return await _obtener_respuesta_pago(session, payment_id)


async def registrar_aprobacion(
    payment_id: int,
    body: PaymentApproval,
    session: AsyncSession,
    actor_id: int,
) -> PaymentRead:
    module = await _obtener_modulo(session, payment_id)
    if module.estado != PaymentStatus.LISTO_PAGO.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo un módulo LISTO_PAGO puede aprobarse.",
        )
    payment = await session.scalar(
        select(Payment).where(Payment.id_modulo == module.id_modulo)
    )
    if payment is None or payment.estado != PaymentRecordStatus.POR_PAGAR.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No existe un pago POR_PAGAR para este módulo.",
        )
    approval = await session.scalar(
        select(Approval).where(Approval.id_modulo == module.id_modulo)
    )
    if approval is None:
        approval = Approval(id_modulo=module.id_modulo)
        session.add(approval)
    elif approval.estado != ApprovalStatus.ANULADA.value:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El módulo ya tiene una aprobación vigente.",
        )
    old_status = module.estado
    module.estado = PaymentStatus.APROBADO.value
    approval.fecha_aprobacion = utc_now_naive()
    approval.origen = "CORREO" if body.id_correo is not None else "MANUAL"
    approval.id_correo = body.id_correo
    approval.estado = ApprovalStatus.VIGENTE.value
    approval.observacion = body.observacion
    approval.id_usuario = actor_id
    await _agregar_historial(
        session,
        module,
        old_status,
        module.estado,
        actor_id,
        body.observacion or "Aprobación manual registrada.",
    )
    await session.commit()
    return await _obtener_respuesta_pago(session, payment_id)


async def marcar_pagado(
    payment_id: int,
    body: PaymentCompletion,
    session: AsyncSession,
    actor_id: int,
) -> PaymentRead:
    module = await _obtener_modulo(session, payment_id)
    if module.estado != PaymentStatus.APROBADO.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "Solo un módulo APROBADO puede marcarse PAGADO.")
    payment = await session.scalar(
        select(Payment).where(Payment.id_modulo == module.id_modulo)
    )
    if payment is None or payment.estado != PaymentRecordStatus.POR_PAGAR.value:
        raise HTTPException(status.HTTP_409_CONFLICT, "No existe un pago POR_PAGAR para este módulo.")
    old_status = module.estado
    module.estado = PaymentStatus.PAGADO.value
    payment.estado = PaymentRecordStatus.PAGADO.value
    payment.fecha_pago = utc_now_naive().date()
    payment.id_usuario = actor_id
    payment.observacion = body.observacion
    payment.numero_factura = body.numero_factura
    payment.numero_comprobante = body.numero_comprobante
    await _agregar_historial(
        session,
        module,
        old_status,
        module.estado,
        actor_id,
        body.observacion or "Pago confirmado manualmente.",
    )
    await session.commit()
    return await _obtener_respuesta_pago(session, payment_id)


async def historial_pago(
    payment_id: int,
    session: AsyncSession,
) -> list[PaymentHistoryRead]:
    await _obtener_modulo(session, payment_id)
    rows = (
        await session.execute(
            select(HistoryEntry, CoreUserRef.nombre_usuario)
            .outerjoin(CoreUserRef, CoreUserRef.id_usuario == HistoryEntry.id_usuario)
            .where(HistoryEntry.id_modulo == payment_id)
            .order_by(HistoryEntry.fecha.desc(), HistoryEntry.id_historial.desc())
        )
    ).all()
    return [
        PaymentHistoryRead(
            id=entry.id_historial,
            evento=entry.estado_nuevo,
            detalle=(
                f"{entry.estado_anterior or 'INICIO'} → {entry.estado_nuevo}"
                + (f": {entry.observacion}" if entry.observacion else "")
            ),
            actor=username or (
                f"Usuario {entry.id_usuario}" if entry.id_usuario else "Sistema"
            ),
            creado_en=entry.fecha,
        )
        for entry, username in rows
    ]
