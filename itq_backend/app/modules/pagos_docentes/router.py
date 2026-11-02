from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.modules.pagos_docentes import services as servicios
from app.modules.pagos_docentes.schemas import (
    PaymentAlertRead,
    PaymentApproval,
    PaymentCompletion,
    PaymentCreate,
    PaymentHistoryRead,
    PaymentLookups,
    PaymentPage,
    PaymentRead,
    PaymentReady,
    PaymentSettingsRead,
    PaymentSettingsUpdate,
    PaymentSummary,
)
from app.models.core import Usuario

router = APIRouter(prefix="/finance/payments", tags=["Pagos docentes"])
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[Usuario, Depends(get_current_user)]


@router.get("/summary", response_model=PaymentSummary)
async def get_summary(session: DbSession) -> PaymentSummary:
    return await servicios.obtener_resumen(session)


@router.get("/alerts", response_model=list[PaymentAlertRead])
async def list_alerts(session: DbSession) -> list[PaymentAlertRead]:
    return await servicios.listar_alertas(session)


@router.get("/settings", response_model=PaymentSettingsRead)
async def read_settings(session: DbSession) -> PaymentSettingsRead:
    return await servicios.leer_configuracion(session)


@router.get("/lookups", response_model=PaymentLookups)
async def list_lookups(session: DbSession) -> PaymentLookups:
    return await servicios.listar_opciones(session)


@router.put("/settings", response_model=PaymentSettingsRead)
async def update_settings(
    body: PaymentSettingsUpdate,
    session: DbSession,
    current_user: CurrentUser,
) -> PaymentSettingsRead:
    return await servicios.actualizar_configuracion(body, session, current_user.id_usuario)


@router.get("", response_model=PaymentPage)
async def list_payments(
    session: DbSession,
    periodo: str | None = None,
    mes: int | None = Query(default=None, ge=1, le=12),
    carrera: str | None = None,
    estado: str | None = None,
    q: str | None = Query(default=None, max_length=160),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaymentPage:
    return await servicios.listar_pagos(
        session,
        periodo,
        mes,
        carrera,
        estado,
        q,
        page,
        page_size,
    )


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
async def create_payment(
    body: PaymentCreate,
    session: DbSession,
    current_user: CurrentUser,
) -> PaymentRead:
    return await servicios.crear_pago(body, session, current_user.id_usuario)


@router.post("/{payment_id}/ready", response_model=PaymentRead)
async def mark_ready(
    payment_id: int,
    body: PaymentReady,
    session: DbSession,
    current_user: CurrentUser,
) -> PaymentRead:
    return await servicios.marcar_listo(payment_id, body, session, current_user.id_usuario)


@router.post("/{payment_id}/approval", response_model=PaymentRead)
async def record_approval(
    payment_id: int,
    body: PaymentApproval,
    session: DbSession,
    current_user: CurrentUser,
) -> PaymentRead:
    return await servicios.registrar_aprobacion(
        payment_id,
        body,
        session,
        current_user.id_usuario,
    )


@router.post("/{payment_id}/paid", response_model=PaymentRead)
async def mark_paid(
    payment_id: int,
    body: PaymentCompletion,
    session: DbSession,
    current_user: CurrentUser,
) -> PaymentRead:
    return await servicios.marcar_pagado(payment_id, body, session, current_user.id_usuario)


@router.get("/{payment_id}/history", response_model=list[PaymentHistoryRead])
async def payment_history(
    payment_id: int,
    session: DbSession,
) -> list[PaymentHistoryRead]:
    return await servicios.historial_pago(payment_id, session)
