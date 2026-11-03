from datetime import date, datetime
from decimal import Decimal

import pydantic

from app.modules.pagos_docentes.enums import (
    AlertStatus,
    AlertType,
    PaymentModel,
    PaymentStatus,
    ThresholdUnit,
)


class PaymentCreate(pydantic.BaseModel):
    """Datos del módulo; la identidad del docente se referencia por id."""

    id_docente: int = pydantic.Field(gt=0)
    id_periodo: int = pydantic.Field(gt=0)
    id_carrera: int = pydantic.Field(gt=0)
    nombre_modulo: str = pydantic.Field(min_length=1, max_length=200)
    paralelo: str | None = pydantic.Field(default=None, max_length=50)
    numero_modulo: int | None = pydantic.Field(default=None, ge=0, le=32767)
    fecha_inicio: date
    fecha_fin: date
    estado: PaymentStatus = PaymentStatus.EN_CURSO
    codigo_eva: str | None = pydantic.Field(default=None, max_length=50)
    modelo: PaymentModel = PaymentModel.CARRERA
    contrato: str | None = pydantic.Field(default=None, max_length=80)
    datos_modelo: dict[str, object] | None = None

    @pydantic.model_validator(mode="after")
    def validate_dates(self) -> "PaymentCreate":
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin debe ser igual o posterior a la fecha de inicio.")
        if self.estado != PaymentStatus.EN_CURSO:
            raise ValueError("Un módulo nuevo debe iniciar en estado EN_CURSO.")
        return self


class PaymentReady(pydantic.BaseModel):
    monto: Decimal = pydantic.Field(gt=0, max_digits=12, decimal_places=2)


class PaymentApproval(pydantic.BaseModel):
    id_correo: int | None = pydantic.Field(default=None, gt=0)
    observacion: str | None = None


class PaymentCompletion(pydantic.BaseModel):
    observacion: str | None = None
    numero_factura: str | None = pydantic.Field(default=None, max_length=50)
    numero_comprobante: str | None = pydantic.Field(default=None, max_length=100)


class TeacherRead(pydantic.BaseModel):
    id_docente: int | None
    nombre: str
    cedula: str | None
    correo: str | None


class PaymentRead(pydantic.BaseModel):
    id: int
    docente: str
    correo_docente: str | None
    modulo: str
    carrera: str
    periodo_academico: str
    fecha_inicio: date
    fecha_fin: date
    estado: str
    codigo_eva: str | None
    modelo: str
    datos_modelo: dict[str, object] | None = None
    monto: Decimal | None = None
    aprobado_en: datetime | None = None
    aprobado_por: str | None = None
    pagado_en: date | None = None
    dias_desde_listo: int | None = None
    dias_desde_aprobacion: int | None = None
    en_mora: bool = False
    listo_atrasado: bool = False
    numero_factura: str | None = None
    numero_comprobante: str | None = None


class PaymentHistoryRead(pydantic.BaseModel):
    id: int
    evento: str
    detalle: str
    actor: str
    creado_en: datetime


class PaymentSettingsUpdate(pydantic.BaseModel):
    valor: int | None = pydantic.Field(default=None, gt=0, le=365)
    unidad: ThresholdUnit | None = None
    correo_notificacion: pydantic.EmailStr | None = None

    @pydantic.model_validator(mode="after")
    def require_at_least_one_value(self) -> "PaymentSettingsUpdate":
        if (
            self.valor is None
            and self.unidad is None
            and self.correo_notificacion is None
        ):
            raise ValueError("Debe indicar al menos un valor para actualizar.")
        return self


class PaymentSettingsRead(pydantic.BaseModel):
    valor: int
    unidad: ThresholdUnit
    correo_notificacion: str | None = None


class PaymentSummary(pydantic.BaseModel):
    total: int
    borradores: int
    listos: int
    por_pagar: int
    pagados: int
    en_mora: int
    listos_atrasados: int
    monto_pendiente: Decimal
    monto_pagado: Decimal


class PaymentAlertRead(pydantic.BaseModel):
    id_modulo: int
    docente: TeacherRead
    nombre_modulo: str | None
    carrera: str | None
    periodo: str | None
    tipo: AlertType
    estado: AlertStatus
    fecha_referencia: datetime
    dias_transcurridos: int
    umbral: int
    unidad: ThresholdUnit


class PaymentPage(pydantic.BaseModel):
    items: list[PaymentRead]
    total: int
    page: int
    page_size: int


class LookupOption(pydantic.BaseModel):
    id: int
    nombre: str
    grupo: str | None = None


class TeacherOption(pydantic.BaseModel):
    id_docente: int
    nombre: str
    cedula: str | None
    correo: str | None


class PaymentLookups(pydantic.BaseModel):
    docentes: list[TeacherOption]
    periodos: list[LookupOption]
    carreras: list[LookupOption]
