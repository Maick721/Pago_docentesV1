"""
app/middleware/audit_logging.py
Servicio de auditoría transversal: registra acciones de usuario en core.auditoria.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.core.models.core import Auditoria


async def registrar_auditoria(
    db: AsyncSession,
    id_usuario: int | None,
    modulo: str,
    accion: str,
    tabla_afectada: str,
    id_registro: int | None = None,
    ip: str | None = None,
) -> Auditoria:
    """
    Inserta un registro de auditoría en la tabla core.auditoria.

    Args:
        db:             Sesión asíncrona de SQLAlchemy.
        id_usuario:     ID del usuario que realizó la acción (puede ser None en login fallido).
        modulo:         Módulo del sistema (ej. "AUTH", "GRADUACION", "CORE").
        accion:         Descripción de la acción (ej. "LOGIN", "VALIDAR_QR", "CONSULTAR_PERSONA").
        tabla_afectada: Nombre de la tabla afectada (ej. "graduacion.qr").
        id_registro:    ID del registro afectado (opcional).
        ip:             Dirección IP del cliente (opcional).

    Returns:
        Instancia de Auditoria recién creada y persistida.
    """
    entrada = Auditoria(
        id_usuario=id_usuario,
        modulo=modulo,
        accion=accion,
        tabla_afectada=tabla_afectada,
        id_registro=id_registro,
        fecha_hora=datetime.now(timezone.utc),
        direccion_ip=ip,
    )
    db.add(entrada)
    await db.flush()  # Persiste sin cerrar la transacción (el commit lo gestiona get_db)
    return entrada
