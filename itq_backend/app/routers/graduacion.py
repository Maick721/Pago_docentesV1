"""
app/routers/graduacion.py
Endpoints del módulo de Graduación y Titulación.

  GET  /api/v1/graduacion/eventos          — Lista eventos activos.
  POST /api/v1/graduacion/validar-qr       — Valida un código QR de pase. [JWT]
  POST /api/v1/graduacion/validar-cedula   — Validación manual por cédula. [JWT]
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.audit import registrar_auditoria
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.core import Persona, Usuario
from app.models.graduacion import Butaca, Evento, Pase, QR
from app.schemas.graduacion import (
    ButacaOut,
    EventoListOut,
    EventoOut,
    PaseValidoResponse,
    ValidarCedulaRequest,
    ValidarQRRequest,
)

router = APIRouter(prefix="/graduacion", tags=["Graduación y Titulación"])


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_pase_response(
    pase: Pase,
    usuario_valida: Usuario,
) -> PaseValidoResponse:
    """Construye el DTO de respuesta para un pase validado exitosamente."""
    butaca_out: ButacaOut | None = None
    if pase.butaca:
        butaca_out = ButacaOut.model_validate(pase.butaca)

    nombres_graduando: str | None = None
    cedula_graduando: str | None = None
    if pase.estudiante:
        nombres_graduando = f"{pase.estudiante.nombres} {pase.estudiante.apellidos}"
        cedula_graduando = pase.estudiante.cedula

    return PaseValidoResponse(
        mensaje="Acceso autorizado ✔",
        id_pase=pase.id_pase,
        tipo_pase=pase.tipo,
        evento=pase.evento.nombre,
        sede=pase.evento.sede,
        nombres_graduando=nombres_graduando,
        cedula_graduando=cedula_graduando,
        nombre_invitado=pase.nombre_invitado,
        cedula_invitado=pase.cedula_invitado,
        butaca=butaca_out,
        fecha_validacion=datetime.now(timezone.utc),
        validado_por=usuario_valida.nombre_usuario,
    )


def _pase_query_with_relations():
    """Retorna la query base para Pase con todas las relaciones cargadas."""
    return select(Pase).options(
        selectinload(Pase.evento),
        selectinload(Pase.butaca),
        selectinload(Pase.estudiante),
        selectinload(Pase.qr),
    )


# ─── GET /graduacion/eventos ─────────────────────────────────────────────────
@router.get(
    "/eventos",
    response_model=EventoListOut,
    summary="Listar eventos activos de graduación",
    description="Retorna todos los eventos de graduación con estado 'activo', ordenados por fecha.",
)
async def listar_eventos(
    db: AsyncSession = Depends(get_db),
) -> EventoListOut:
    result = await db.execute(
        select(Evento)
        .where(Evento.estado == "activo")
        .order_by(Evento.fecha.asc())
    )
    eventos = result.scalars().all()

    return EventoListOut(
        total=len(eventos),
        eventos=[EventoOut.model_validate(e) for e in eventos],
    )


# ─── POST /graduacion/validar-qr ─────────────────────────────────────────────
@router.post(
    "/validar-qr",
    response_model=PaseValidoResponse,
    summary="Validar pase mediante código QR",
    description=(
        "Busca el código QR en `graduacion.qr`. "
        "- Si no existe → **404** (Pase inválido). "
        "- Si ya fue utilizado → **400** (Pase ya utilizado). "
        "- Si es válido → Marca como utilizado, registra auditoría y retorna datos del pase."
    ),
)
async def validar_qr(
    body: ValidarQRRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> PaseValidoResponse:
    ip_cliente = request.client.host if request.client else "desconocida"

    # 1. Buscar el QR
    qr_result = await db.execute(
        select(QR).where(QR.codigo == body.codigo_qr.strip())
    )
    qr: QR | None = qr_result.scalar_one_or_none()

    # 2. QR inexistente → 404
    if qr is None:
        await registrar_auditoria(
            db=db,
            id_usuario=usuario_actual.id_usuario,
            modulo="GRADUACION",
            accion="VALIDAR_QR_NO_ENCONTRADO",
            tabla_afectada="graduacion.qr",
            ip=ip_cliente,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pase inválido: el código QR no existe en el sistema.",
        )

    # 3. QR ya utilizado → 400
    if qr.utilizado:
        await registrar_auditoria(
            db=db,
            id_usuario=usuario_actual.id_usuario,
            modulo="GRADUACION",
            accion="VALIDAR_QR_YA_UTILIZADO",
            tabla_afectada="graduacion.qr",
            id_registro=qr.id_qr,
            ip=ip_cliente,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"El pase ya fue utilizado. "
                f"Fecha de uso: {qr.fecha_uso.isoformat() if qr.fecha_uso else 'desconocida'}."
            ),
        )

    # 4. Validación exitosa — actualizar QR
    ahora = datetime.now(timezone.utc)
    qr.utilizado = True
    qr.fecha_uso = ahora
    qr.id_usuario_valida = usuario_actual.id_usuario
    qr.dispositivo_info = body.dispositivo_info
    db.add(qr)

    # 5. Cargar el pase con sus relaciones
    pase_result = await db.execute(
        _pase_query_with_relations().where(Pase.id_pase == qr.id_pase)
    )
    pase: Pase = pase_result.scalar_one()

    # 6. Actualizar estado del pase
    pase.estado = "utilizado"
    db.add(pase)

    # 7. Registrar auditoría
    await registrar_auditoria(
        db=db,
        id_usuario=usuario_actual.id_usuario,
        modulo="GRADUACION",
        accion="VALIDAR_QR_EXITOSO",
        tabla_afectada="graduacion.qr",
        id_registro=qr.id_qr,
        ip=ip_cliente,
    )

    return _build_pase_response(pase, usuario_actual)


# ─── POST /graduacion/validar-cedula ─────────────────────────────────────────
@router.post(
    "/validar-cedula",
    response_model=PaseValidoResponse,
    summary="Validación manual por cédula (contingencia)",
    description=(
        "Validación contingente cuando el QR no puede ser escaneado. "
        "Busca un pase activo asociado a la cédula del graduando o invitado "
        "en el evento especificado. "
        "- Si no existe pase activo → **404**. "
        "- Si el pase ya fue utilizado → **400**."
    ),
)
async def validar_cedula(
    body: ValidarCedulaRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
) -> PaseValidoResponse:
    ip_cliente = request.client.host if request.client else "desconocida"
    cedula = body.cedula.strip()

    # Buscar persona por cédula
    persona_result = await db.execute(
        select(Persona).where(Persona.cedula == cedula)
    )
    persona: Persona | None = persona_result.scalar_one_or_none()

    # Buscar pase activo por cédula de graduando o invitado en el evento
    pase_query = (
        _pase_query_with_relations()
        .where(
            and_(
                Pase.id_evento == body.id_evento,
                Pase.estado == "emitido",
            )
        )
    )

    if body.tipo_pase == "graduando":
        if persona is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró ninguna persona con cédula '{cedula}'.",
            )
        pase_query = pase_query.where(Pase.id_estudiante == persona.id_persona)
    else:
        # Búsqueda por cédula_invitado (campo de texto)
        pase_query = pase_query.where(Pase.cedula_invitado == cedula)

    pase_result = await db.execute(pase_query)
    pases = pase_result.scalars().all()

    # Filtrar por tipo de pase
    pases_filtrados = [p for p in pases if p.tipo == body.tipo_pase]

    if not pases_filtrados:
        await registrar_auditoria(
            db=db,
            id_usuario=usuario_actual.id_usuario,
            modulo="GRADUACION",
            accion="VALIDAR_CEDULA_NO_ENCONTRADO",
            tabla_afectada="graduacion.pases",
            ip=ip_cliente,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No se encontró un pase activo de tipo '{body.tipo_pase}' "
                f"para la cédula '{cedula}' en el evento ID {body.id_evento}."
            ),
        )

    # Tomar el primer pase válido
    pase = pases_filtrados[0]

    if pase.estado == "utilizado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pase correspondiente a esta cédula ya fue utilizado.",
        )

    # Marcar como utilizado
    ahora = datetime.now(timezone.utc)
    pase.estado = "utilizado"
    db.add(pase)

    # Actualizar QR asociado si existe
    if pase.qr:
        pase.qr.utilizado = True
        pase.qr.fecha_uso = ahora
        pase.qr.id_usuario_valida = usuario_actual.id_usuario
        pase.qr.dispositivo_info = "validación-manual-cedula"
        db.add(pase.qr)

    # Registrar auditoría
    await registrar_auditoria(
        db=db,
        id_usuario=usuario_actual.id_usuario,
        modulo="GRADUACION",
        accion="VALIDAR_CEDULA_EXITOSO",
        tabla_afectada="graduacion.pases",
        id_registro=pase.id_pase,
        ip=ip_cliente,
    )

    return _build_pase_response(pase, usuario_actual)
