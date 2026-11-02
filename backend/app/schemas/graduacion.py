"""
app/schemas/graduacion.py
DTOs Pydantic v2 para el módulo de Graduación y Titulación.
"""
from datetime import datetime, time

from pydantic import BaseModel, Field


# ─── Evento ──────────────────────────────────────────────────────────────────

class EventoOut(BaseModel):
    """DTO de respuesta con datos de un evento de graduación."""
    id_evento: int
    nombre: str
    fecha: datetime
    hora: time | None = None
    sede: str | None = None
    jornada: str | None = None
    aforo: int | None = None
    estado: str

    model_config = {"from_attributes": True}


class EventoListOut(BaseModel):
    """DTO para listado de eventos activos."""
    total: int
    eventos: list[EventoOut]


# ─── Butaca ──────────────────────────────────────────────────────────────────

class ButacaOut(BaseModel):
    """DTO de respuesta con datos de una butaca asignada."""
    id_butaca: int
    fila: str
    numero: int
    estado: str

    model_config = {"from_attributes": True}


# ─── Validación por QR ───────────────────────────────────────────────────────

class ValidarQRRequest(BaseModel):
    """Cuerpo de la solicitud de validación de QR."""
    codigo_qr: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Código QR escaneado desde el pase de graduación.",
        examples=["QR-2026-00123-ABCXYZ"],
    )
    dispositivo_info: str | None = Field(
        None,
        max_length=500,
        description="Información del dispositivo que realiza la validación (User-Agent, ID escáner, etc.).",
    )


# ─── Validación por Cédula ───────────────────────────────────────────────────

class ValidarCedulaRequest(BaseModel):
    """Cuerpo de la solicitud de validación manual por cédula (contingencia)."""
    cedula: str = Field(
        ...,
        min_length=5,
        max_length=20,
        description="Número de cédula del graduando o invitado.",
        examples=["0912345678"],
    )
    id_evento: int = Field(
        ...,
        description="ID del evento de graduación donde se realiza la validación.",
    )
    tipo_pase: str = Field(
        default="graduando",
        description="Tipo de pase a buscar: 'graduando' o 'invitado'.",
        examples=["graduando"],
    )


# ─── Respuesta de Validación Exitosa ─────────────────────────────────────────

class PaseValidoResponse(BaseModel):
    """Respuesta devuelta cuando un QR o cédula se valida exitosamente."""
    mensaje: str = Field(default="Acceso autorizado", description="Mensaje de confirmación.")
    id_pase: int
    tipo_pase: str
    evento: str
    sede: str | None = None

    # Datos del graduando (cuando el pase es de tipo 'graduando')
    nombres_graduando: str | None = None
    cedula_graduando: str | None = None

    # Datos del invitado (cuando el pase es de tipo 'invitado')
    nombre_invitado: str | None = None
    cedula_invitado: str | None = None

    # Datos de la butaca asignada
    butaca: ButacaOut | None = None

    # Metadatos de la validación
    fecha_validacion: datetime = Field(default_factory=datetime.utcnow)
    validado_por: str | None = None


# ─── Respuesta de Error de Validación ────────────────────────────────────────

class PaseInvalidoResponse(BaseModel):
    """Respuesta cuando la validación falla por pase ya utilizado o inexistente."""
    error: str
    detalle: str | None = None
    codigo_qr: str | None = None
