from enum import StrEnum


class PaymentStatus(StrEnum):
    EN_CURSO = "EN_CURSO"
    LISTO_PAGO = "LISTO_PAGO"
    APROBADO = "APROBADO"
    PAGADO = "PAGADO"
    ANULADO = "ANULADO"

    # Compatibility names used by the existing workflow.
    BORRADOR = "EN_CURSO"
    LISTO = "LISTO_PAGO"


class PaymentModel(StrEnum):
    CARRERA = "CARRERA"
    VALIDACION = "VALIDACION"


class PaymentRecordStatus(StrEnum):
    POR_PAGAR = "POR_PAGAR"
    PAGADO = "PAGADO"


class ApprovalStatus(StrEnum):
    VIGENTE = "VIGENTE"
    ANULADA = "ANULADA"


class AlertType(StrEnum):
    PAGO_ATRASADO = "PAGO_ATRASADO"
    APROBACION_PENDIENTE = "APROBACION_PENDIENTE"


class AlertStatus(StrEnum):
    ACTIVA = "ACTIVA"
    RESUELTA = "RESUELTA"


class ThresholdUnit(StrEnum):
    DIAS = "DIAS"
    MESES = "MESES"


class EmailProcessingStatus(StrEnum):
    PENDIENTE = "PENDIENTE"
    PROCESADO = "PROCESADO"
    FALLIDO = "FALLIDO"
    REVISADO_MANUAL = "REVISADO_MANUAL"


class RequirementStatus(StrEnum):
    CUMPLE = "CUMPLE"
    NO_CUMPLE = "NO_CUMPLE"
    PENDIENTE = "PENDIENTE"
