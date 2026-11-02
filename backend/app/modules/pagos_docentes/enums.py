
from enum import StrEnum


# Esta clase contiene los estados por los que puede pasar un pago.
# Uso StrEnum porque sus valores son cadenas de texto.
class PaymentStatus(StrEnum):
    EN_CURSO = "EN_CURSO"
    BORRADOR = "EN_CURSO"
    LISTO_PAGO = "LISTO_PAGO"
    LISTO = "LISTO_PAGO"
    APROBADO = "APROBADO"
    PAGADO = "PAGADO"
    ANULADO = "ANULADO"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            aliases = {
                "BORRADOR": "EN_CURSO",
                "LISTO": "LISTO_PAGO",
            }
            return cls.__members__.get(aliases.get(value.upper(), value.upper()))
        return None


# Aquí defino los modelos o tipos de pago que maneja el sistema.
class PaymentModel(StrEnum):
    CARRERA = "CARRERA"       
    VALIDACION = "VALIDACION" 

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            return cls.__members__.get(value.upper())
        return None


# Esta clase sirve para identificar los tipos de alertas
# que puede generar el sistema.
class AlertType(StrEnum):
    PAGO_ATRASADO = "PAGO_ATRASADO"


# Aquí manejo los estados de las alertas.
class AlertStatus(StrEnum):
    ACTIVA = "ACTIVA"
    RESUELTA = "RESUELTA"


class PaymentRecordStatus(StrEnum):
    POR_PAGAR = "POR_PAGAR"
    PAGADO = "PAGADO"


class ApprovalStatus(StrEnum):
    VIGENTE = "VIGENTE"
    ANULADA = "ANULADA"


class ApprovalOrigin(StrEnum):
    CORREO = "CORREO"
    MANUAL = "MANUAL"


class ThresholdUnit(StrEnum):
    DIAS = "DIAS"
    MESES = "MESES"


# Esta clase indica si un requisito se cumple o no.
class RequirementStatus(StrEnum):
    CUMPLE = "CUMPLE"          
    NO_CUMPLE = "NO_CUMPLE"   
    PENDIENTE = "PENDIENTE"    


# Estos son los eventos que pueden ocurrir durante el proceso de pago.
class PaymentEvent(StrEnum):
    CREADO = "creado"          
    LISTO = "listo"            
    APROBADO = "aprobado"      
    PAGADO = "pagado"          
