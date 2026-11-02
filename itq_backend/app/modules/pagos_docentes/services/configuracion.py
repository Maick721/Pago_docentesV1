from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pagos_docentes.enums import ThresholdUnit
from app.modules.pagos_docentes.models import PaymentConfig
from app.modules.pagos_docentes.schemas import PaymentSettingsRead, PaymentSettingsUpdate
from app.modules.pagos_docentes.services.comun import DEFAULT_THRESHOLD


async def actualizar_configuracion(
    body: PaymentSettingsUpdate,
    session: AsyncSession,
    actor_id: int,
) -> PaymentSettingsRead:
    config = await session.scalar(
        select(PaymentConfig)
        .where(PaymentConfig.activo.is_(True))
        .order_by(PaymentConfig.id_configuracion.desc())
        .limit(1)
    )
    if config is None:
        config = PaymentConfig(
            valor=body.valor or DEFAULT_THRESHOLD,
            unidad=(body.unidad or ThresholdUnit.DIAS).value,
            correo_notificacion=body.correo_notificacion,
            activo=True,
            id_usuario=actor_id,
        )
        session.add(config)
    else:
        if body.valor is not None:
            config.valor = body.valor
        if body.unidad is not None:
            config.unidad = body.unidad.value
        if "correo_notificacion" in body.model_fields_set:
            config.correo_notificacion = body.correo_notificacion
        config.id_usuario = actor_id
    await session.commit()
    await session.refresh(config)
    return PaymentSettingsRead(
        valor=config.valor,
        unidad=config.unidad,
        correo_notificacion=config.correo_notificacion,
    )
